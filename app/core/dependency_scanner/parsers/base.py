"""
Module 3 — Dependency Scanner: Base Parser

Abstract base class for all package manager parsers.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from typing import Optional
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class DependencyInfo:
    """Represents a single dependency."""
    name: str
    version: str = '*'  # '*' means unspecified/any
    ecosystem: str = ''
    is_direct: bool = True
    license: Optional[str] = None
    source_file: str = ''  # which manifest file it came from
    
    def to_dict(self) -> dict:
        return asdict(self)


class BaseParser(ABC):
    """Abstract base class for dependency manifest parsers."""
    
    @property
    @abstractmethod
    def ecosystem(self) -> str:
        """Return the ecosystem name (e.g., 'pypi', 'npm')."""
        pass
    
    @property
    @abstractmethod
    def manifest_files(self) -> list[str]:
        """Return list of manifest filenames this parser handles."""
        pass
    
    @abstractmethod
    def parse(self, file_path: str) -> list[DependencyInfo]:
        """Parse a manifest file and return list of dependencies."""
        pass
    
    def detect(self, workspace_path: str) -> list[str]:
        """
        Search workspace for manifest files this parser handles.
        Returns list of found manifest file paths (absolute).
        Walks the entire directory tree to find manifests.
        Skips common non-project dirs (node_modules, .git, __pycache__, venv, .venv, target, build).
        """
        found = []
        skip_dirs = {'node_modules', '.git', '__pycache__', 'venv', '.venv', 
                     'target', 'build', 'dist', '.tox', '.eggs', 'egg-info'}
        
        for root, dirs, files in os.walk(workspace_path):
            # Skip irrelevant directories
            dirs[:] = [d for d in dirs if d not in skip_dirs and not d.endswith('.egg-info')]
            
            for manifest in self.manifest_files:
                if manifest in files:
                    found.append(os.path.join(root, manifest))
        
        return found
    
    def _safe_read(self, file_path: str) -> str:
        """Safely read file contents with error handling."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Failed to read {file_path}: {e}")
            return ''
