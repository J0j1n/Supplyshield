import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.graph_engine.builder import GraphBuilder

class TestGraphBuilder(unittest.TestCase):
    def setUp(self):
        self.builder = GraphBuilder()
        self.deps = [
            {'name': 'flask', 'version': '3.0.0', 'ecosystem': 'pypi', 'is_direct': True},
            {'name': 'express', 'version': '4.18.0', 'ecosystem': 'npm', 'is_direct': True},
            {'name': 'lodash', 'version': '4.17.21', 'ecosystem': 'npm', 'is_direct': False},
        ]

    def test_build_graph(self):
        graph = self.builder.build_graph(self.deps, "TestProject")
        self.assertIn('root', graph['nodes'])
        self.assertEqual(graph['nodes']['root']['name'], 'TestProject')
        self.assertEqual(graph['stats']['total_nodes'], 4)
        self.assertEqual(graph['stats']['total_edges'], 3)
        self.assertEqual(graph['stats']['ecosystems_count'], 2)
        self.assertCountEqual(graph['ecosystems'], ['pypi', 'npm'])

    def test_detect_circular_no_cycles(self):
        graph = self.builder.build_graph(self.deps)
        cycles = self.builder.detect_circular(graph)
        self.assertEqual(cycles, [])

    def test_detect_circular_with_cycles(self):
        graph = self.builder.build_graph(self.deps)
        # Inject a cycle: flask depends on lodash, lodash depends on flask
        flask_id = 'pypi:flask@3.0.0'
        lodash_id = 'npm:lodash@4.17.21'
        graph['adjacency'][flask_id].append(lodash_id)
        graph['adjacency'][lodash_id].append(flask_id)
        
        cycles = self.builder.detect_circular(graph)
        self.assertTrue(len(cycles) > 0)

    def test_get_transitive(self):
        graph = self.builder.build_graph(self.deps)
        # Manually add transitive dep for testing
        flask_id = 'pypi:flask@3.0.0'
        transitive_dep = 'pypi:werkzeug@3.0.0'
        graph['adjacency'][flask_id].append(transitive_dep)
        
        reachable = self.builder.get_transitive(graph, flask_id)
        self.assertIn(transitive_dep, reachable)

    def test_calculate_depth(self):
        graph = self.builder.build_graph(self.deps)
        depths = self.builder.calculate_depth(graph)
        
        self.assertEqual(depths['root'], 0)
        self.assertEqual(depths['pypi:flask@3.0.0'], 1)
        self.assertEqual(depths['npm:express@4.18.0'], 1)

    def test_to_d3_json(self):
        graph = self.builder.build_graph(self.deps)
        d3_json = self.builder.to_d3_json(graph)
        
        self.assertEqual(len(d3_json['nodes']), 4)
        self.assertEqual(len(d3_json['links']), 3)
        
        root_node = next((n for n in d3_json['nodes'] if n['type'] == 'root'), None)
        self.assertIsNotNone(root_node)
        self.assertEqual(root_node['size'], 20)
        
        dep_node = next((n for n in d3_json['nodes'] if n['type'] == 'dependency'), None)
        self.assertIsNotNone(dep_node)
        self.assertEqual(dep_node['size'], 10)

    def test_d3_json_with_vulnerability_map(self):
        graph = self.builder.build_graph(self.deps)
        vuln_map = {
            'flask': {'count': 2, 'max_severity': 'high'}
        }
        
        d3_json = self.builder.to_d3_json(graph, vuln_map)
        
        flask_node = next(n for n in d3_json['nodes'] if n['name'] == 'flask')
        self.assertEqual(flask_node['vuln_count'], 2)
        self.assertEqual(flask_node['max_severity'], 'high')
        
        express_node = next(n for n in d3_json['nodes'] if n['name'] == 'express')
        self.assertEqual(express_node['vuln_count'], 0)
        self.assertEqual(express_node['max_severity'], 'none')

    def test_empty_dependencies(self):
        graph = self.builder.build_graph([])
        self.assertEqual(graph['stats']['total_nodes'], 1)
        self.assertEqual(graph['stats']['total_edges'], 0)
        self.assertEqual(len(graph['nodes']), 1)
        self.assertIn('root', graph['nodes'])

if __name__ == '__main__':
    unittest.main()
