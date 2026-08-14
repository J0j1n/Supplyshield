"""
Module 4 — SBOM Generator: Generator Service

Provides the high-level interface to generate and save SBOMs.
"""
import os
import json
import logging
from .cyclonedx import CycloneDXBuilder
from .spdx import SPDXBuilder

logger = logging.getLogger(__name__)

class SBOMGenerator:
    """Service to generate and export SBOMs."""
    
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
    def generate(self, dependencies: list[dict], scan_id: str, project_name: str, format: str = 'cyclonedx') -> str:
        """
        Generate an SBOM and save it to the output directory.
        format can be 'cyclonedx' or 'spdx'.
        Returns the path to the saved SBOM file.
        """
        metadata = {
            'scan_id': scan_id,
            'project_name': project_name
        }
        
        if format.lower() == 'cyclonedx':
            builder = CycloneDXBuilder()
            bom_data = builder.build(dependencies, metadata)
            filename = f"sbom_{scan_id}_cyclonedx.json"
        elif format.lower() == 'spdx':
            builder = SPDXBuilder()
            bom_data = builder.build(dependencies, metadata)
            filename = f"sbom_{scan_id}_spdx.json"
        else:
            raise ValueError(f"Unsupported SBOM format: {format}")
            
        output_path = os.path.join(self.output_dir, filename)
        
        try:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(bom_data, f, indent=2)
            logger.info(f"Generated {format} SBOM at {output_path}")
            return output_path
        except Exception as e:
            logger.error(f"Failed to write SBOM to {output_path}: {e}")
            raise
