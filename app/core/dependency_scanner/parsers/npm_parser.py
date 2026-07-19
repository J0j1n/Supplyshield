"""
Parser for npm ecosystem.
"""
from typing import Optional, List
from .base import BaseParser

class NpmParser(BaseParser):
    """
    Parses package.json and package-lock.json.
    """
    
    @property
    def ecosystem(self) -> str:
        return 'npm'

    def parse(self, file_path: str) -> List['DependencyInfo']:
        # TODO: Implement npm manifest parsing
        return []

    def detect(self, workspace_path: str) -> Optional[str]:
        # TODO: Implement detection for package.json, package-lock.json
        return None
