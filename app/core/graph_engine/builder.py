"""
Module 5 — Dependency Graph Engine: Graph Builder

Builds dependency graphs from parsed dependency data,
detects circular dependencies, computes transitive chains,
and serializes to D3.js-compatible JSON for frontend visualization.
"""
import logging
from collections import defaultdict, deque

logger = logging.getLogger(__name__)

class GraphBuilder:
    def build_graph(self, dependencies: list[dict], project_name: str = 'Project') -> dict:
        nodes = {}
        edges = []
        adjacency = defaultdict(list)
        ecosystems = set()

        root_id = 'root'
        nodes[root_id] = {
            'name': project_name,
            'version': '',
            'ecosystem': '',
            'is_direct': True,
            'type': 'root'
        }

        for i, dep in enumerate(dependencies):
            name = dep.get('name', f'unknown-{i}')
            version = dep.get('version', '')
            ecosystem = dep.get('ecosystem', 'unknown')
            is_direct = dep.get('is_direct', True)
            
            node_id = f"{ecosystem}:{name}@{version}"
            ecosystems.add(ecosystem)
            
            nodes[node_id] = {
                'name': name,
                'version': version,
                'ecosystem': ecosystem,
                'is_direct': is_direct,
                'type': 'dependency'
            }
            
            edges.append({
                'source': root_id,
                'target': node_id
            })
            
            adjacency[root_id].append(node_id)
            if node_id not in adjacency:
                adjacency[node_id] = []

        return {
            'nodes': nodes,
            'edges': edges,
            'adjacency': dict(adjacency),
            'root': root_id,
            'ecosystems': list(ecosystems),
            'stats': {
                'total_nodes': len(nodes),
                'total_edges': len(edges),
                'ecosystems_count': len(ecosystems)
            }
        }

    def detect_circular(self, graph: dict) -> list:
        adjacency = graph.get('adjacency', {})
        cycles = []
        
        visited = set()
        rec_stack = set()
        path = []
        
        def dfs(node):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)
            
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor)
                elif neighbor in rec_stack:
                    # Found a cycle
                    cycle_start_index = path.index(neighbor)
                    cycle = path[cycle_start_index:]
                    cycles.append(cycle)
                    
            rec_stack.remove(node)
            path.pop()

        for node in adjacency:
            if node not in visited:
                dfs(node)
                
        return cycles

    def get_transitive(self, graph: dict, package: str) -> list:
        adjacency = graph.get('adjacency', {})
        if package not in adjacency:
            return []
            
        visited = set()
        queue = deque([package])
        
        while queue:
            node = queue.popleft()
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
                    
        return list(visited)

    def calculate_depth(self, graph: dict) -> dict:
        adjacency = graph.get('adjacency', {})
        root = graph.get('root', 'root')
        
        depths = {root: 0}
        queue = deque([(root, 0)])
        visited = {root}
        
        while queue:
            node, depth = queue.popleft()
            
            for neighbor in adjacency.get(node, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    depths[neighbor] = depth + 1
                    queue.append((neighbor, depth + 1))
                    
        return depths

    def to_d3_json(self, graph: dict, vulnerability_map: dict = None) -> dict:
        nodes = []
        links = []
        
        ecosystems = graph.get('ecosystems', [])
        eco_map = {eco: i for i, eco in enumerate(ecosystems)}
        
        vuln_map = vulnerability_map or {}
        
        for node_id, node_data in graph.get('nodes', {}).items():
            node_type = node_data.get('type', 'dependency')
            name = node_data.get('name', '')
            
            vuln_info = vuln_map.get(name, {})
            vuln_count = vuln_info.get('count', 0)
            max_severity = vuln_info.get('max_severity', 'none')
            
            group = eco_map.get(node_data.get('ecosystem', ''), -1)
            if node_type == 'root':
                group = -1
                
            nodes.append({
                'id': node_id,
                'name': name,
                'version': node_data.get('version', ''),
                'ecosystem': node_data.get('ecosystem', ''),
                'group': group,
                'type': node_type,
                'is_direct': node_data.get('is_direct', True),
                'size': 20 if node_type == 'root' else 10,
                'vuln_count': vuln_count,
                'max_severity': max_severity
            })
            
        for edge in graph.get('edges', []):
            links.append({
                'source': edge['source'],
                'target': edge['target'],
                'value': 1
            })
            
        return {
            'nodes': nodes,
            'links': links
        }
