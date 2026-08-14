"""
Module 4 — SBOM Generator: SPDX Builder

Constructs SBOMs conforming to the SPDX 2.3 specification.
"""
import uuid
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

class SPDXBuilder:
    """Builds SPDX format SBOMs."""
    
    def build(self, dependencies: list[dict], metadata: dict) -> dict:
        """
        Build an SPDX 2.3 JSON object.
        """
        timestamp = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
        doc_id = f"SPDXRef-DOCUMENT"
        
        bom = {
            "spdxVersion": "SPDX-2.3",
            "dataLicense": "CC0-1.0",
            "SPDXID": doc_id,
            "name": metadata.get('project_name', 'Unknown Project'),
            "documentNamespace": f"http://spdx.org/spdxdocs/{metadata.get('project_name', 'unknown')}-{uuid.uuid4()}",
            "creationInfo": {
                "creators": [
                    "Tool: SupplyShield-0.1.0"
                ],
                "created": timestamp
            },
            "packages": [],
            "relationships": []
        }
        
        # Root package representing the project itself
        root_package_id = "SPDXRef-RootPackage"
        root_package = {
            "name": metadata.get('project_name', 'Unknown Project'),
            "SPDXID": root_package_id,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False
        }
        bom["packages"].append(root_package)
        
        bom["relationships"].append({
            "spdxElementId": doc_id,
            "relatedSpdxElement": root_package_id,
            "relationshipType": "DESCRIBES"
        })
        
        for i, dep in enumerate(dependencies):
            pkg, rel = self._build_package(dep, i, root_package_id)
            if pkg:
                bom["packages"].append(pkg)
                bom["relationships"].append(rel)
                
        return bom
        
    def _build_package(self, dep: dict, index: int, parent_id: str) -> tuple[dict, dict]:
        """Convert a dependency dict to an SPDX package and relationship."""
        name = dep.get('name')
        if not name:
            return None, None
            
        version = dep.get('version', 'unknown')
        pkg_id = f"SPDXRef-Package-{index}"
        
        pkg = {
            "name": name,
            "SPDXID": pkg_id,
            "versionInfo": version,
            "downloadLocation": "NOASSERTION",
            "filesAnalyzed": False
        }
        
        license_str = dep.get('license')
        if license_str:
            pkg["licenseConcluded"] = license_str
            pkg["licenseDeclared"] = license_str
        else:
            pkg["licenseConcluded"] = "NOASSERTION"
            pkg["licenseDeclared"] = "NOASSERTION"
            
        rel = {
            "spdxElementId": parent_id,
            "relatedSpdxElement": pkg_id,
            "relationshipType": "DEPENDS_ON"
        }
        
        return pkg, rel
