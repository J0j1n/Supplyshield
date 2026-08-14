"""
Module 4 — SBOM Generator: CycloneDX Builder

Constructs SBOMs conforming to the CycloneDX 1.5 specification.
"""
import uuid
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class CycloneDXBuilder:
    """Builds CycloneDX format SBOMs."""
    
    def build(self, dependencies: list[dict], metadata: dict) -> dict:
        """
        Build a CycloneDX 1.5 JSON object.
        dependencies: list of dicts (from DependencyInfo)
        metadata: dict with project_name, scan_id, etc.
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        
        bom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.5",
            "serialNumber": f"urn:uuid:{uuid.uuid4()}",
            "version": 1,
            "metadata": {
                "timestamp": timestamp,
                "tools": [
                    {
                        "vendor": "SupplyShield",
                        "name": "SupplyShield Scanner",
                        "version": "0.1.0"
                    }
                ],
                "component": {
                    "type": "application",
                    "name": metadata.get('project_name', 'Unknown Project'),
                    "version": "latest",
                    "bom-ref": f"pkg:generic/{metadata.get('project_name', 'unknown')}@latest"
                }
            },
            "components": []
        }
        
        for dep in dependencies:
            comp = self._build_component(dep)
            if comp:
                bom["components"].append(comp)
                
        return bom
        
    def _build_component(self, dep: dict) -> dict:
        """Convert a dependency dict to a CycloneDX component."""
        name = dep.get('name')
        if not name:
            return None
            
        version = dep.get('version', 'unknown')
        ecosystem = dep.get('ecosystem', 'unknown').lower()
        
        # Map our ecosystems to purl types
        purl_type_map = {
            'pypi': 'pypi',
            'npm': 'npm',
            'maven': 'maven',
            'gradle': 'maven',
            'cargo': 'cargo',
            'poetry': 'pypi'
        }
        purl_type = purl_type_map.get(ecosystem, 'generic')
        
        # Handle maven group:artifact
        if ':' in name:
            group, name_part = name.split(':', 1)
            purl = f"pkg:{purl_type}/{group}/{name_part}@{version}"
        else:
            group = ""
            purl = f"pkg:{purl_type}/{name}@{version}"
            
        comp = {
            "type": "library",
            "name": name if not group else name_part,
            "version": version,
            "purl": purl,
            "bom-ref": purl
        }
        
        if group:
            comp["group"] = group
            
        license_str = dep.get('license')
        if license_str:
            comp["licenses"] = [
                {
                    "license": {
                        "name": license_str
                    }
                }
            ]
            
        return comp
