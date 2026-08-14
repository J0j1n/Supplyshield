"""
Module 3 — Dependency Scanner: Maven Parser

Parses Java Maven dependency manifests:
- pom.xml (dependency declarations)
"""
import xml.etree.ElementTree as ET
import os
import re
import logging
from typing import List
from .base import BaseParser, DependencyInfo

logger = logging.getLogger(__name__)


class MavenParser(BaseParser):
    @property
    def ecosystem(self) -> str:
        return 'maven'
    
    @property
    def manifest_files(self) -> List[str]:
        return ['pom.xml']
    
    def parse(self, file_path: str) -> List[DependencyInfo]:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
        except ET.ParseError as e:
            logger.error(f"Failed to parse XML in {file_path}: {e}")
            return []
        except Exception as e:
            logger.error(f"Error reading {file_path}: {e}")
            return []

        # Handle namespace if present
        ns = ''
        if root.tag.startswith('{'):
            ns = root.tag.split('}')[0] + '}'
            
        dependencies = []
        basename = os.path.basename(file_path)
        
        def process_dependencies(deps_element):
            for dep in deps_element.findall(f'{ns}dependency'):
                group_id_elem = dep.find(f'{ns}groupId')
                artifact_id_elem = dep.find(f'{ns}artifactId')
                version_elem = dep.find(f'{ns}version')
                scope_elem = dep.find(f'{ns}scope')
                
                if group_id_elem is not None and artifact_id_elem is not None:
                    group_id = group_id_elem.text.strip() if group_id_elem.text else ''
                    artifact_id = artifact_id_elem.text.strip() if artifact_id_elem.text else ''
                    name = f"{group_id}:{artifact_id}"
                    
                    version = version_elem.text.strip() if version_elem is not None and version_elem.text else '*'
                    version = self._resolve_properties(root, ns, version)
                    
                    scope = scope_elem.text.strip() if scope_elem is not None and scope_elem.text else 'compile'
                    if scope in ('test', 'provided'):
                        logger.info(f"Found {scope} scoped dependency: {name}")
                        
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        is_direct=True,
                        source_file=basename
                    ))

        # Main dependencies
        deps = root.find(f'{ns}dependencies')
        if deps is not None:
            process_dependencies(deps)
            
        # Dependency management
        dep_mgmt = root.find(f'{ns}dependencyManagement')
        if dep_mgmt is not None:
            mgmt_deps = dep_mgmt.find(f'{ns}dependencies')
            if mgmt_deps is not None:
                process_dependencies(mgmt_deps)
                
        return dependencies

    def _resolve_properties(self, root, ns: str, value: str) -> str:
        if not value or '${' not in value:
            return value
            
        properties = root.find(f'{ns}properties')
        
        def replacer(match):
            prop_name = match.group(1)
            if prop_name == 'project.version':
                v = root.find(f'{ns}version')
                if v is not None and v.text:
                    return v.text.strip()
            
            if properties is not None:
                prop_elem = properties.find(f'{ns}{prop_name}')
                if prop_elem is not None and prop_elem.text:
                    return prop_elem.text.strip()
            return match.group(0)
            
        return re.sub(r'\$\{([^}]+)\}', replacer, value)
