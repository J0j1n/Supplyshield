"""
Module 3 — Dependency Scanner: Gradle Parser

Parses Java Gradle dependency manifests:
- build.gradle (Groovy DSL)
- build.gradle.kts (Kotlin DSL)
"""
import re
import os
import logging
from typing import List
from .base import BaseParser, DependencyInfo

logger = logging.getLogger(__name__)


class GradleParser(BaseParser):
    @property
    def ecosystem(self) -> str:
        return 'gradle'
    
    @property
    def manifest_files(self) -> List[str]:
        return ['build.gradle', 'build.gradle.kts']
    
    def parse(self, file_path: str) -> List[DependencyInfo]:
        content = self._safe_read(file_path)
        if not content:
            return []
            
        dependencies = []
        basename = os.path.basename(file_path)
        is_kotlin = basename.endswith('.kts')
        
        # Pattern for Groovy: implementation 'group:artifact:version'
        groovy_pattern = re.compile(
            r'(?:implementation|compile|api|runtimeOnly|compileOnly|testImplementation|testCompile|annotationProcessor)\s*[\'"]([^\'"]+)[\'"]'
        )
        
        # Pattern for Kotlin: implementation("group:artifact:version")
        kotlin_pattern = re.compile(
            r'(?:implementation|compile|api|runtimeOnly|compileOnly|testImplementation|testCompile|annotationProcessor)\s*\([\'"]([^\'"]+)[\'"]\)'
        )
        
        pattern = kotlin_pattern if is_kotlin else groovy_pattern
        
        for line in content.splitlines():
            line = line.strip()
            if not line or line.startswith('//'):
                continue
                
            # Warn on version catalogs reference
            if re.search(r'\blibs\.[a-zA-Z0-9_.]+', line):
                logger.warning(f"Found version catalog reference in {file_path}, cannot resolve: {line}")
                continue
                
            match = pattern.search(line)
            if match:
                dep_str = match.group(1)
                parts = dep_str.split(':')
                
                if len(parts) >= 2:
                    group_id = parts[0]
                    artifact_id = parts[1]
                    name = f"{group_id}:{artifact_id}"
                    version = parts[2] if len(parts) > 2 else '*'
                    
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        ecosystem=self.ecosystem,
                        is_direct=True,
                        source_file=basename
                    ))
                    
        return dependencies
