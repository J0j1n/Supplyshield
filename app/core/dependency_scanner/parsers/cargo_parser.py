"""
Module 3 — Dependency Scanner: Cargo Parser

Parses Rust dependency manifests:
- Cargo.toml (dependency declarations)
- Cargo.lock (exact resolved versions)
"""
import os
import logging
import tomllib
from typing import List
from .base import BaseParser, DependencyInfo

logger = logging.getLogger(__name__)


class CargoParser(BaseParser):
    @property
    def ecosystem(self) -> str:
        return 'cargo'
    
    @property
    def manifest_files(self) -> List[str]:
        return ['Cargo.toml', 'Cargo.lock']
    
    def parse(self, file_path: str) -> List[DependencyInfo]:
        basename = os.path.basename(file_path)
        if basename == 'Cargo.toml':
            return self._parse_cargo_toml(file_path)
        elif basename == 'Cargo.lock':
            return self._parse_cargo_lock(file_path)
        return []

    def _parse_cargo_toml(self, file_path: str) -> List[DependencyInfo]:
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse TOML in {file_path}: {e}")
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        sections = ['dependencies', 'dev-dependencies', 'build-dependencies']
        
        for section in sections:
            if section in data and isinstance(data[section], dict):
                for name, value in data[section].items():
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

    def _parse_cargo_lock(self, file_path: str) -> List[DependencyInfo]:
        try:
            with open(file_path, 'rb') as f:
                data = tomllib.load(f)
        except Exception as e:
            logger.error(f"Failed to parse TOML in {file_path}: {e}")
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        if 'package' in data and isinstance(data['package'], list):
            for i, pkg in enumerate(data['package']):
                if i == 0:
                    continue  # Usually the root package
                
                name = pkg.get('name')
                version = pkg.get('version', '*')
                
                if name:
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        is_direct=False,  # lock file has transitive deps
                        source_file=basename
                    ))
                    
        return dependencies
