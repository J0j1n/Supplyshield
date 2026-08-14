"""
Tests for Module 4 — SBOM Generator
"""
import os
import sys
import json
import tempfile
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.sbom_generator import SBOMGenerator

def test_cyclonedx_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SBOMGenerator(tmpdir)
        scan_id = str(uuid.uuid4())
        
        deps = [
            {"name": "flask", "version": "3.0.0", "ecosystem": "pypi", "is_direct": True},
            {"name": "org.springframework:spring-core", "version": "5.3.20", "ecosystem": "maven", "is_direct": True, "license": "Apache-2.0"}
        ]
        
        output_path = generator.generate(deps, scan_id, "TestProject", format="cyclonedx")
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            bom = json.load(f)
            
        assert bom["bomFormat"] == "CycloneDX"
        assert len(bom["components"]) == 2
        
        # Check Flask component
        flask_comp = next(c for c in bom["components"] if c["name"] == "flask")
        assert flask_comp["version"] == "3.0.0"
        assert flask_comp["purl"] == "pkg:pypi/flask@3.0.0"
        
        # Check Maven component
        spring_comp = next(c for c in bom["components"] if c["name"] == "spring-core")
        assert spring_comp["group"] == "org.springframework"
        assert spring_comp["purl"] == "pkg:maven/org.springframework/spring-core@5.3.20"
        assert spring_comp["licenses"][0]["license"]["name"] == "Apache-2.0"

def test_spdx_generation():
    with tempfile.TemporaryDirectory() as tmpdir:
        generator = SBOMGenerator(tmpdir)
        scan_id = str(uuid.uuid4())
        
        deps = [
            {"name": "express", "version": "4.18.0", "ecosystem": "npm", "is_direct": True, "license": "MIT"}
        ]
        
        output_path = generator.generate(deps, scan_id, "TestProject", format="spdx")
        
        assert os.path.exists(output_path)
        with open(output_path, 'r') as f:
            bom = json.load(f)
            
        assert bom["spdxVersion"] == "SPDX-2.3"
        
        # 1 root package + 1 dep package
        assert len(bom["packages"]) == 2
        
        express_pkg = next(p for p in bom["packages"] if p["name"] == "express")
        assert express_pkg["versionInfo"] == "4.18.0"
        assert express_pkg["licenseConcluded"] == "MIT"
        
        # Check relationships (DESCRIBES for root, DEPENDS_ON for dep)
        assert len(bom["relationships"]) == 2
        depends_rel = next(r for r in bom["relationships"] if r["relationshipType"] == "DEPENDS_ON")
        assert depends_rel["relatedSpdxElement"] == express_pkg["SPDXID"]

if __name__ == '__main__':
    test_cyclonedx_generation()
    print("  PASSED: test_cyclonedx_generation")
    test_spdx_generation()
    print("  PASSED: test_spdx_generation")
    print("\n2/2 SBOM tests passed")
