"""
Module 3 — Dependency Scanner: Poetry Parser

Parses Python Poetry dependency manifests:
- pyproject.toml (under [tool.poetry.dependencies])
- poetry.lock (resolved dependencies)
"""
import os
import logging
import tomllib
from typing import List
from .base import BaseParser, DependencyInfo

logger = logging.getLogger(__name__)


class PoetryParser(BaseParser):
    @property
    def ecosystem(self) -> str:
        return 'poetry'
    
    @property
    def manifest_files(self) -> List[str]:
        return ['pyproject.toml', 'poetry.lock']
    
    def parse(self, file_path: str) -> List[DependencyInfo]:
        basename = os.path.basename(file_path)
        if basename == 'pyproject.toml':
            return self._parse_pyproject_toml(file_path)
        elif basename == 'poetry.lock':
            return self._parse_poetry_lock(file_path)
        return []

    def _parse_pyproject_toml(self, file_path: str) -> List[DependencyInfo]:
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse TOML in {file_path}: {e}")
            return []
            
        # Check if it's actually a Poetry project
        tool = data.get('tool', {})
        poetry = tool.get('poetry')
        if not poetry:
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        # Main dependencies
        if 'dependencies' in poetry and isinstance(poetry['dependencies'], dict):
            for name, value in poetry['dependencies'].items():
                if name == 'python':
                    continue
                if isinstance(value, str):
                    version = value
                elif isinstance(value, dict):
                    version = value.get('version', '*')
                else:
                    version = '*'
                    
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_direct=True,
                    source_file=basename
                ))
                
        # Dev dependencies (older format)
        if 'dev-dependencies' in poetry and isinstance(poetry['dev-dependencies'], dict):
            for name, value in poetry['dev-dependencies'].items():
                if isinstance(value, str):
                    version = value
                elif isinstance(value, dict):
                    version = value.get('version', '*')
                else:
                    version = '*'
                    
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    ecosystem=self.ecosystem,
                    is_direct=True,
                    source_file=basename
                ))
                
        # Poetry 1.2+ groups
        if 'group' in poetry and isinstance(poetry['group'], dict):
            for group_name, group_data in poetry['group'].items():
                if 'dependencies' in group_data and isinstance(group_data['dependencies'], dict):
                    for name, value in group_data['dependencies'].items():
                        if isinstance(value, str):
                            version = value
                        elif isinstance(value, dict):
                            version = value.get('version', '*')
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

    def _parse_poetry_lock(self, file_path: str) -> List[DependencyInfo]:
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse TOML in {file_path}: {e}")
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        if 'package' in data and isinstance(data['package'], list):
            for pkg in data['package']:
                name = pkg.get('name')
                version = pkg.get('version', '*')
                category = pkg.get('category', 'main')
                
                if name:
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        is_direct=(category == 'main'),
                        source_file=basename
                    ))
                    
        return dependencies
