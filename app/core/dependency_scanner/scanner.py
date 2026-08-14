"""
Module 3 — Dependency Scanner: Scanner Orchestrator

Detects which package ecosystems are present in a workspace,
runs the appropriate parsers, deduplicates results, and returns
a comprehensive dependency inventory.
"""
import logging
from typing import Optional
from .parsers import ALL_PARSERS, DependencyInfo, BaseParser

logger = logging.getLogger(__name__)

class DependencyScanner:
    def __init__(self):
        self.parsers = [ParserClass() for ParserClass in ALL_PARSERS]
        
    def scan(self, workspace_path: str) -> dict:
        ecosystems_found = self.detect_ecosystems(workspace_path)
        all_dependencies = []
        manifest_records = []
        
        for ecosystem, manifests in ecosystems_found.items():
            parser = self.get_parser(ecosystem)
            if not parser:
                continue
                
            for manifest_path in manifests:
                manifest_records.append({
                    'ecosystem': ecosystem,
                    'file': manifest_path.split('/')[-1] if '/' in manifest_path else manifest_path.split('\\')[-1],
                    'path': manifest_path
                })
                
                try:
                    deps = parser.parse(manifest_path)
                    all_dependencies.extend(deps)
                except Exception as e:
                    logger.error(f"Error parsing {manifest_path} for {ecosystem}: {str(e)}")
                    
        deduped_deps = self._deduplicate(all_dependencies)
        
        # Calculate summary
        direct_count = sum(1 for d in deduped_deps if d.is_direct)
        transitive_count = len(deduped_deps) - direct_count
        by_ecosystem = {}
        for d in deduped_deps:
            by_ecosystem[d.ecosystem] = by_ecosystem.get(d.ecosystem, 0) + 1
            
        summary = {
            'total': len(deduped_deps),
            'by_ecosystem': by_ecosystem,
            'direct': direct_count,
            'transitive': transitive_count
        }
        
        logger.info(f"Scan complete. Summary: {summary}")
        
        return {
            'ecosystems': list(ecosystems_found.keys()),
            'manifests': manifest_records,
            'dependencies': [dep.to_dict() for dep in deduped_deps],
            'summary': summary
        }

    def detect_ecosystems(self, workspace_path: str) -> dict:
        detected = {}
        for parser in self.parsers:
            manifests = parser.detect(workspace_path)
            if manifests:
                detected[parser.ecosystem] = manifests
        return detected

    def _deduplicate(self, dependencies: list[DependencyInfo]) -> list[DependencyInfo]:
        grouped = {}
        for dep in dependencies:
            key = (dep.name, dep.ecosystem)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(dep)
            
        deduplicated = []
        for key, deps in grouped.items():
            if len(deps) == 1:
                deduplicated.append(deps[0])
            else:
                # Sort dependencies to pick the best one
                # Prefer specific version over '*'
                # Prefer direct over transitive
                # In this simplified logic, we just sort by a score
                def score(d):
                    score = 0
                    if d.version and d.version != '*': score += 10
                    # Lockfile vs manifest would require source_file analysis, simplified here
                    if d.source_file and 'lock' in d.source_file.lower(): score += 5
                    if d.is_direct: score += 2
                    return score
                    
                best_dep = sorted(deps, key=score, reverse=True)[0]
                deduplicated.append(best_dep)
                
        return deduplicated

    def get_parser(self, ecosystem: str) -> Optional[BaseParser]:
        for parser in self.parsers:
            if parser.ecosystem == ecosystem:
                return parser
        return None
