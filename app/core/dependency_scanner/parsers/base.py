"""
Base class for all package manager parsers.
"""
from abc import ABC, abstractmethod
from typing import Optional, List

class BaseParser(ABC):
    """
    Abstract base class for dependency manifest parsers.
    """
    
    @abstractmethod
    def parse(self, file_path: str) -> List['DependencyInfo']:
        """
        Parse the manifest file and return a list of dependencies.
        """
        pass

    @abstractmethod
    def detect(self, workspace_path: str) -> Optional[str]:
        """
        Detect if the ecosystem is present in the workspace.
        Returns the manifest file path if found, else None.
        """
        pass

    @property
    @abstractmethod
    def ecosystem(self) -> str:
        """
        The name of the ecosystem this parser handles.
        """
        pass
