"""Tests for the visualizer module"""
import pytest
import json
import tempfile
import os
from meshnetmap.visualizer.display import NetworkVisualizer


class TestNetworkVisualizerLoading:
    """Tests for loading topology data"""

    def test_load_topology_from_dict(self, simple_topology):
        """Test loading topology from dictionary"""
        viz = NetworkVisualizer()
        viz.topology_data = simple_topology

        assert viz.topology_data is not None
        assert "nodes" in viz.topology_data
        assert len(viz.topology_data["nodes"]) == 3

    def test_load_topology_from_file(self, simple_topology):
        """Test loading topology from JSON file"""
        viz = NetworkVisualizer()

        # Write to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(simple_topology, f)
            temp_path = f.name

        try:
            result = viz.load_topology(temp_path)
            assert result is True
            assert viz.topology_data is not None
            assert len(viz.topology_data["nodes"]) == 3
        finally:
            os.unlink(temp_path)

    def test_load_topology_missing_file(self):
        """Test loading from non-existent file"""
        viz = NetworkVisualizer()
        result = viz.load_topology("/nonexistent/file.json")

        assert result is False

    def test_load_topology_invalid_json(self):
        """Test loading invalid JSON"""
        viz = NetworkVisualizer()

        # Write invalid JSON to temp file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{invalid json content")
            temp_path = f.name

        try:
            result = viz.load_topology(temp_path)
            assert result is False
        finally:
            os.unlink(temp_path)


class TestNetworkGraphBuilding:
    """Tests for building network graphs"""

    def test_build_network_graph_basic(self, simple_topology):
        """Test basic graph building"""
        viz = NetworkVisualizer()
        viz.topology_data = simple_topology

        viz.build_network_graph()

        assert viz.graph is not None
        assert viz.graph.number_of_nodes() == 3

    def test_build_network_graph_with_connections(self, simple_topology):
        """Test graph building with connections"""
        # Add connections to topology
        simple_topology["connections"] = [
            {
                "from": "!node0001",
                "to": "!node0002",
                "snr": 5.0,
                "type": "inferred_direct"
            }
        ]

        viz = NetworkVisualizer()
        viz.topology_data = simple_topology
        viz.build_network_graph()

        assert viz.graph.number_of_nodes() == 3
        assert viz.graph.number_of_edges() >= 1

    def test_graph_node_attributes(self, simple_topology):
        """Test that graph nodes have correct attributes"""
        viz = NetworkVisualizer()
        viz.topology_data = simple_topology
        viz.build_network_graph()

        # Check node attributes
        for node_id in viz.graph.nodes():
            node_data = viz.graph.nodes[node_id]
            assert "hopsAway" in node_data or "hops_away" in node_data


class TestNetworkStatistics:
    """Tests for network statistics"""

    def test_get_network_statistics_basic(self, simple_topology):
        """Test basic statistics calculation"""
        viz = NetworkVisualizer()
        viz.topology_data = simple_topology
        viz.build_network_graph()

        stats = viz.get_network_statistics()

        assert "nodes" in stats
        assert "edges" in stats
        assert stats["nodes"] == 3

    def test_get_network_statistics_with_connections(self, simple_topology):
        """Test statistics with connections"""
        simple_topology["connections"] = [
            {"from": "!node0001", "to": "!node0002", "snr": 5.0},
            {"from": "!node0002", "to": "!node0003", "snr": -5.0}
        ]

        viz = NetworkVisualizer()
        viz.topology_data = simple_topology
        viz.build_network_graph()

        stats = viz.get_network_statistics()

        assert stats["nodes"] == 3
        assert stats["edges"] >= 2
        assert "avg_degree" in stats
        assert "density" in stats


class TestDynamicVisualization:
    """Tests for dynamic visualization generation"""

    def test_create_dynamic_visualization(self, simple_topology):
        """Test dynamic visualization creation"""
        viz = NetworkVisualizer()
        viz.topology_data = simple_topology
        viz.build_network_graph()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name

        try:
            result = viz.create_dynamic_visualization(output_path)
            assert result is True
            assert os.path.exists(output_path)

            # Check that file contains D3.js content
            with open(output_path, 'r') as f:
                content = f.read()
                assert "d3.forceSimulation" in content
                assert "TOPOLOGY_DATA" not in content  # Should be replaced
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_dynamic_visualization_with_connections(self, simple_topology):
        """Test dynamic visualization with connections"""
        simple_topology["connections"] = [
            {
                "from": "!node0001",
                "to": "!node0002",
                "snr": 5.0,
                "type": "colocated",
                "confidence": "high"
            }
        ]

        viz = NetworkVisualizer()
        viz.topology_data = simple_topology
        viz.build_network_graph()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name

        try:
            result = viz.create_dynamic_visualization(output_path)
            assert result is True

            # Verify connection data is embedded
            with open(output_path, 'r') as f:
                content = f.read()
                assert "colocated" in content
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_visualization_dynamic_flag(self, simple_topology):
        """Test save_visualization with dynamic flag"""
        viz = NetworkVisualizer()
        viz.topology_data = simple_topology
        viz.build_network_graph()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name

        try:
            viz.save_visualization(output_path, dynamic=True)
            assert os.path.exists(output_path)

            # Should be dynamic visualization
            with open(output_path, 'r') as f:
                content = f.read()
                assert "d3.forceSimulation" in content
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)


class TestVisualizationEdgeCases:
    """Tests for edge cases in visualization"""

    def test_empty_topology_visualization(self):
        """Test visualization with empty topology"""
        viz = NetworkVisualizer()
        viz.topology_data = {"nodes": {}, "connections": []}
        viz.build_network_graph()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name

        try:
            # Should not crash with empty topology
            result = viz.create_dynamic_visualization(output_path)
            assert result is True
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_visualization_with_missing_node_data(self):
        """Test visualization when nodes have minimal data"""
        topology = {
            "nodes": {
                "!minimal": {
                    "id": "!minimal"
                    # Missing most fields
                }
            },
            "connections": []
        }

        viz = NetworkVisualizer()
        viz.topology_data = topology
        viz.build_network_graph()

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            output_path = f.name

        try:
            # Should handle gracefully
            result = viz.create_dynamic_visualization(output_path)
            assert result is True
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_large_topology_handling(self, multi_hop_topology):
        """Test handling of larger topology"""
        viz = NetworkVisualizer()
        viz.topology_data = multi_hop_topology
        viz.build_network_graph()

        # Should handle 15 nodes (5 hops * 3 nodes) without issues
        assert viz.graph.number_of_nodes() == 15

        stats = viz.get_network_statistics()
        assert stats["nodes"] == 15


class TestTemplateHandling:
    """Tests for template file handling"""

    def test_template_exists(self):
        """Test that dynamic visualization template exists"""
        from meshnetmap.visualizer import display
        import os

        template_path = os.path.join(
            os.path.dirname(display.__file__),
            'templates',
            'dynamic_network.html'
        )

        assert os.path.exists(template_path), "Template file not found"

    def test_template_has_placeholder(self):
        """Test that template contains data placeholder"""
        from meshnetmap.visualizer import display
        import os

        template_path = os.path.join(
            os.path.dirname(display.__file__),
            'templates',
            'dynamic_network.html'
        )

        with open(template_path, 'r') as f:
            content = f.read()
            assert "{{TOPOLOGY_DATA}}" in content, "Template placeholder missing"
