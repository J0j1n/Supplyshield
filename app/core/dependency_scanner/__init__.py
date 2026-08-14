"""
Module 3 — Dependency Scanner

Scans project workspaces to detect and parse dependency manifests
across multiple package manager ecosystems.
"""
from .scanner import DependencyScanner

__all__ = ['DependencyScanner']
