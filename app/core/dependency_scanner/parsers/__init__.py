"""
Module 3 — Dependency Scanner: Parser Registry

Exports all parsers and the base class.
"""
from .base import BaseParser, DependencyInfo
from .pip_parser import PipParser
from .npm_parser import NpmParser
from .maven_parser import MavenParser
from .gradle_parser import GradleParser
from .cargo_parser import CargoParser
from .poetry_parser import PoetryParser

# Registry of all available parsers
ALL_PARSERS = [
    PipParser,
    NpmParser,
    MavenParser,
    GradleParser,
    CargoParser,
    PoetryParser,
]

__all__ = [
    'BaseParser', 'DependencyInfo',
    'PipParser', 'NpmParser', 'MavenParser',
    'GradleParser', 'CargoParser', 'PoetryParser',
    'ALL_PARSERS',
]
