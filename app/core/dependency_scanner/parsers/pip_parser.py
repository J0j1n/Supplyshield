"""
Module 3 — Dependency Scanner: Pip Parser

Parses Python dependency manifests:
- requirements.txt (and variants like requirements-dev.txt)
- setup.py (install_requires extraction)
- Pipfile ([packages] and [dev-packages] sections)
"""
import re
import os
import logging
from typing import List
from .base import BaseParser, DependencyInfo

logger = logging.getLogger(__name__)


class PipParser(BaseParser):
    @property
    def ecosystem(self) -> str:
        return 'pypi'
    
    @property
    def manifest_files(self) -> List[str]:
        return ['requirements.txt', 'requirements-dev.txt', 'requirements_dev.txt', 'setup.py', 'Pipfile']
    
    def parse(self, file_path: str) -> List[DependencyInfo]:
        basename = os.path.basename(file_path)
        if basename.startswith('requirements'):
            return self._parse_requirements_txt(file_path)
        elif basename == 'setup.py':
            return self._parse_setup_py(file_path)
        elif basename == 'Pipfile':
            return self._parse_pipfile(file_path)
        return []

    def _parse_requirements_txt(self, file_path: str) -> List[DependencyInfo]:
        content = self._safe_read(file_path)
        if not content:
            return []

        dependencies = []
        basename = os.path.basename(file_path)
        
        # Matches: package_name, operator, version
        # E.g.: requests>=2.25.1 -> ('requests', '>=', '2.25.1')
        pattern = re.compile(r'^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(?:([><=!~]+)\s*([^,;#\s]+))?')
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            if line.startswith('-r'):
                logger.info(f"Found included requirements file in {file_path}: {line}")
                continue
            elif line.startswith('-'):
                continue
            
            if 'git+' in line or 'hg+' in line or 'svn+' in line or 'bzr+' in line:
                logger.warning(f"Skipping VCS URL in {file_path}: {line}")
                continue
            if line.startswith('file://') or line.startswith('.'):
                continue
                
            # Strip environment markers for parsing package name and version
            base_line = line.split(';')[0].strip()
            
            match = pattern.match(base_line)
            if match:
                name = match.group(1)
                operator = match.group(2)
                version_val = match.group(3)
                
                if operator and version_val:
                    if operator == '==':
                        version = version_val
                    else:
                        version = f"{operator}{version_val}"
                else:
                    version = '*'
                    
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_direct=True,
                    source_file=basename
                ))
        
        return dependencies

    def _parse_setup_py(self, file_path: str) -> List[DependencyInfo]:
        content = self._safe_read(file_path)
        if not content:
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        # Look for install_requires=[...]
        match = re.search(r'install_requires\s*=\s*\[([^\]]+)\]', content, re.MULTILINE | re.DOTALL)
        if not match:
            return []
            
        reqs_str = match.group(1)
        # Split by comma, handling potential whitespace and quotes
        req_lines = [r.strip().strip('"\'') for r in reqs_str.split(',') if r.strip()]
        
        pattern = re.compile(r'^([A-Za-z0-9][A-Za-z0-9._-]*)(?:\[[^\]]*\])?\s*(?:([><=!~]+)\s*([^,;#\s]+))?')
        
        for req in req_lines:
            if not req:
                continue
            
            base_req = req.split(';')[0].strip()
            m = pattern.match(base_req)
            if m:
                name = m.group(1)
                operator = m.group(2)
                version_val = m.group(3)
                
                if operator and version_val:
                    if operator == '==':
                        version = version_val
                    else:
                        version = f"{operator}{version_val}"
                else:
                    version = '*'
                    
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_direct=True,
                    source_file=basename
                ))
                
        return dependencies

    def _parse_pipfile(self, file_path: str) -> List[DependencyInfo]:
        content = self._safe_read(file_path)
        if not content:
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        sections = {'packages': False, 'dev-packages': False}
        current_section = None
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            if line == '[packages]':
                current_section = 'packages'
                continue
            elif line == '[dev-packages]':
                current_section = 'dev-packages'
                continue
            elif line.startswith('['):
                current_section = None
                continue
                
            if current_section in sections:
                if '=' in line:
                    parts = line.split('=', 1)
                    name = parts[0].strip().strip('"\'')
                    val = parts[1].strip()
                    
                    if val.startswith('{'):
                        # Dict notation, e.g., {version = ">=1.0"}
                        v_match = re.search(r'version\s*=\s*["\']([^"\']+)["\']', val)
                        if v_match:
                            version = v_match.group(1)
                        else:
                            version = '*'
                    else:
                        version = val.strip('"\'')
                        
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        is_direct=True,
                        source_file=basename
                    ))
                    
        return dependencies
