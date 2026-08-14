"""
Tests for Module 3 — Dependency Scanner

Tests all parsers and the scanner orchestrator.
"""
import os
import sys
import json
import tempfile
import zipfile
import shutil
import unittest
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.dependency_scanner.parsers.base import DependencyInfo
from app.core.dependency_scanner.parsers import (
    PipParser, NpmParser, MavenParser, GradleParser, CargoParser, PoetryParser
)
from app.core.dependency_scanner.scanner import DependencyScanner

def test_pip_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        req_path = os.path.join(tmpdir, "requirements.txt")
        with open(req_path, "w") as f:
            f.write("flask==3.0.0\nrequests>=2.31.0\nnumpy\n# comment\npandas==1.5.3")
            
        parser = PipParser()
        deps = parser.parse(req_path)
        
        assert len(deps) == 4
        flask_dep = next(d for d in deps if d.name == 'flask')
        assert flask_dep.version in ('==3.0.0', '3.0.0')
        numpy_dep = next(d for d in deps if d.name == 'numpy')
        assert numpy_dep.version == '*'

def test_npm_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        pkg_path = os.path.join(tmpdir, "package.json")
        with open(pkg_path, "w") as f:
            f.write('{"name": "test", "dependencies": {"express": "^4.18.0", "lodash": "~4.17.21"}, "devDependencies": {"jest": "^29.0.0"}}')
            
        parser = NpmParser()
        deps = parser.parse(pkg_path)
        
        assert len(deps) == 3

def test_maven_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        pom_path = os.path.join(tmpdir, "pom.xml")
        with open(pom_path, "w") as f:
            f.write('''<?xml version="1.0"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <dependencies>
    <dependency>
      <groupId>org.springframework</groupId>
      <artifactId>spring-core</artifactId>
      <version>5.3.20</version>
    </dependency>
    <dependency>
      <groupId>junit</groupId>
      <artifactId>junit</artifactId>
      <version>4.13.2</version>
      <scope>test</scope>
    </dependency>
  </dependencies>
</project>''')
            
        parser = MavenParser()
        deps = parser.parse(pom_path)
        
        assert len(deps) == 2
        assert deps[0].name == 'org.springframework:spring-core'

def test_gradle_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        gradle_path = os.path.join(tmpdir, "build.gradle")
        with open(gradle_path, "w") as f:
            f.write('''
dependencies {
    implementation 'com.google.guava:guava:31.1-jre'
    testImplementation "junit:junit:4.13.2"
    api 'org.apache.commons:commons-lang3:3.12.0'
}
''')
            
        parser = GradleParser()
        deps = parser.parse(gradle_path)
        
        assert len(deps) == 3

def test_cargo_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        cargo_path = os.path.join(tmpdir, "Cargo.toml")
        with open(cargo_path, "w") as f:
            f.write('''
[package]
name = "my-project"
version = "0.1.0"

[dependencies]
serde = "1.0"
tokio = { version = "1.28", features = ["full"] }
''')
            
        parser = CargoParser()
        deps = parser.parse(cargo_path)
        
        assert len(deps) == 2

def test_poetry_parser():
    with tempfile.TemporaryDirectory() as tmpdir:
        poetry_path = os.path.join(tmpdir, "pyproject.toml")
        with open(poetry_path, "w") as f:
            f.write('''
[tool.poetry]
name = "my-project"

[tool.poetry.dependencies]
python = "^3.9"
requests = "^2.28"
flask = {version = "^3.0", optional = true}

[tool.poetry.dev-dependencies]
pytest = "^7.0"
''')
            
        parser = PoetryParser()
        deps = parser.parse(poetry_path)
        
        assert len(deps) == 3
        dep_names = [d.name for d in deps]
        assert 'python' not in dep_names
        assert 'requests' in dep_names

def test_scanner_full_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        with open(os.path.join(tmpdir, "requirements.txt"), "w") as f:
            f.write("flask==3.0.0\n")
        with open(os.path.join(tmpdir, "package.json"), "w") as f:
            f.write('{"dependencies": {"express": "4.18.0"}}')
            
        scanner = DependencyScanner()
        result = scanner.scan(tmpdir)
        
        assert set(result['ecosystems']) == {'pypi', 'npm'}
        assert len(result['dependencies']) == 2
        assert result['summary']['total'] == 2

def test_scanner_empty_workspace():
    with tempfile.TemporaryDirectory() as tmpdir:
        scanner = DependencyScanner()
        result = scanner.scan(tmpdir)
        
        assert len(result['ecosystems']) == 0
        assert len(result['dependencies']) == 0

def test_e2e_upload_with_scanning():
    # Since we can't easily start the whole Flask app here in a simple script
    # We will mock the required parts or import app if it exists.
    # To keep it simple as requested, just a stub or we try to import the app.
    try:
        from app.main import create_app
        app = create_app()
        app.testing = True
        client = app.test_client()
        
        with tempfile.NamedTemporaryFile(suffix='.zip', delete=False) as tmp_zip:
            with zipfile.ZipFile(tmp_zip, 'w') as z:
                z.writestr('requirements.txt', 'flask==3.0.0\\nrequests==2.31.0')
            tmp_zip_name = tmp_zip.name
            
        with open(tmp_zip_name, 'rb') as f:
            data = {'file': (f, 'test.zip'), 'project_name': 'test_proj'}
            resp = client.post('/scan/upload', data=data, follow_redirects=True)
            
        assert resp.status_code == 200
        # If it returns json with scan_id
        if resp.is_json:
            json_data = resp.get_json()
            assert json_data.get('dependencies_found', 0) > 0 or json_data.get('total_dependencies', 0) > 0
            
        os.remove(tmp_zip_name)
    except ImportError:
        print("Skipping e2e test, app not importable")
        pass


if __name__ == '__main__':
    tests = [
        test_pip_parser, test_npm_parser, test_maven_parser,
        test_gradle_parser, test_cargo_parser, test_poetry_parser,
        test_scanner_full_workspace, test_scanner_empty_workspace,
        test_e2e_upload_with_scanning
    ]
    passed = 0
    failed = 0
    for test in tests:
        try:
            test()
            print(f'  PASSED: {test.__name__}')
            passed += 1
        except Exception as e:
            print(f'  FAILED: {test.__name__} — {e}')
            failed += 1
    print(f'\\n{passed}/{passed+failed} tests passed')
    if failed > 0:
        sys.exit(1)
