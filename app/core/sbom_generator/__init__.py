"""
Module 4 — SBOM Generator

Generates standard Software Bill of Materials (SBOM) documents
in CycloneDX and SPDX formats based on discovered dependencies.
"""
from .generator import SBOMGenerator

__all__ = ['SBOMGenerator']
