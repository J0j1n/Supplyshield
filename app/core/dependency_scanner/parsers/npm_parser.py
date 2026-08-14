"""
Module 3 — Dependency Scanner: npm Parser

Parses Node.js dependency manifests:
- package.json (dependencies + devDependencies)
- package-lock.json (exact resolved versions)
"""
import json
import os
import logging
from typing import List
from .base import BaseParser, DependencyInfo

logger = logging.getLogger(__name__)


class NpmParser(BaseParser):
    @property
    def ecosystem(self) -> str:
        return 'npm'
    
    @property
    def manifest_files(self) -> List[str]:
        return ['package.json', 'package-lock.json']
    
    def parse(self, file_path: str) -> List[DependencyInfo]:
        basename = os.path.basename(file_path)
        if basename == 'package.json':
            return self._parse_package_json(file_path)
        elif basename == 'package-lock.json':
            return self._parse_package_lock(file_path)
        return []

    def _parse_package_json(self, file_path: str) -> List[DependencyInfo]:
        content = self._safe_read(file_path)
        if not content:
            return []
            
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        for section in ['dependencies', 'devDependencies']:
            if section in data and isinstance(data[section], dict):
                for name, version in data[section].items():
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=str(version),
                        ecosystem=self.ecosystem,
                        is_direct=True,
                        source_file=basename
                    ))
                    
        return dependencies

    def _parse_package_lock(self, file_path: str) -> List[DependencyInfo]:
        content = self._safe_read(file_path)
        if not content:
            return []
            
        try:
            data = json.loads(content)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in {file_path}: {e}")
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        # v2/v3 format uses 'packages'
        if 'packages' in data and isinstance(data['packages'], dict):
            for path, pkg_data in data['packages'].items():
                if not path:
                    continue  # Root package
                
                # Extract name from node_modules/express -> express
                # or node_modules/@types/node -> @types/node
                name = path.split('node_modules/')[-1]
                
                version = pkg_data.get('version', '*')
                is_dev = pkg_data.get('dev', False)
                # Mark as direct if it's a top-level node_modules dependency and not purely dev
                # Note: true direct determination requires analyzing the dependency tree
                # For simplicity, we assume if it's right under node_modules it might be direct
                is_direct = not path.count('node_modules') > 1 and not is_dev
                
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_direct=is_direct,
                    source_file=basename
                ))
        # v1 format uses 'dependencies'
        elif 'dependencies' in data and isinstance(data['dependencies'], dict):
            for name, pkg_data in data['dependencies'].items():
                version = pkg_data.get('version', '*')
                is_dev = pkg_data.get('dev', False)
                
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_direct=not is_dev,
                    source_file=basename
                ))
                
        return dependencies
