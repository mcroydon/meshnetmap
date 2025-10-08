"""Tests for the inference module"""
import pytest
from meshnetmap.inference import (
    find_colocated_nodes,
    extract_routing_evidence,
    infer_connections_from_hops
)


class TestCoLocationDetection:
    """Tests for co-located node detection"""

    def test_find_colocated_nodes_basic(self, colocated_topology):
        """Test basic co-location detection with GPS coordinates"""
        colocated = find_colocated_nodes(colocated_topology)

        # Should find one location with 3 nodes
        assert len(colocated) == 1

        location, nodes = colocated[0]
        assert location == (30.4873, -97.8584)
        assert len(nodes) == 3

        # Extract node IDs
        node_ids = [node_id for node_id, _ in nodes]
        assert "!source01" in node_ids
        assert "!collect1" in node_ids
        assert "!mobile01" in node_ids

    def test_find_colocated_nodes_no_gps(self, topology_without_gps):
        """Test co-location detection when nodes lack GPS"""
        colocated = find_colocated_nodes(topology_without_gps)

        # Should find no co-located nodes (no GPS coordinates)
        assert len(colocated) == 0

    def test_find_colocated_nodes_gps_precision(self, simple_topology):
        """Test GPS rounding precision (4 decimal places)"""
        # Add two nodes very close together (within 11m)
        simple_topology["nodes"]["!close1"] = {
            "id": "!close1",
            "position": {"latitude": 37.77490, "longitude": -122.41940}
        }
        simple_topology["nodes"]["!close2"] = {
            "id": "!close2",
            "position": {"latitude": 37.77491, "longitude": -122.41941}
        }

        colocated = find_colocated_nodes(simple_topology)

        # Should find one co-located pair due to rounding
        assert len(colocated) >= 1


class TestRoutingEvidence:
    """Tests for routing evidence extraction"""

    def test_extract_routing_evidence_basic(self, routing_evidence_topology):
        """Test basic routing evidence extraction"""
        evidence = extract_routing_evidence(routing_evidence_topology)

        assert len(evidence) > 0
        assert "!node0001" in evidence
        assert "!node0002" in evidence["!node0001"]

        # Check evidence details
        node1_to_node2 = evidence["!node0001"]["!node0002"]
        assert len(node1_to_node2) == 1
        assert node1_to_node2[0]["packet_type"] == "position"
        assert node1_to_node2[0]["hops"] == 1

    def test_extract_routing_evidence_empty(self, simple_topology):
        """Test routing evidence extraction with no routing paths"""
        evidence = extract_routing_evidence(simple_topology)

        # Should return empty dict
        assert evidence == {}

    def test_extract_routing_evidence_multiple_packets(self):
        """Test routing evidence with multiple packets"""
        topology = {
            "routing_paths": [
                {"from": "!a", "to": "!b", "packet_type": "position", "hops_away": 1},
                {"from": "!a", "to": "!b", "packet_type": "telemetry", "hops_away": 1},
                {"from": "!a", "to": "!b", "packet_type": "text", "hops_away": 1},
            ]
        }

        evidence = extract_routing_evidence(topology)

        assert "!a" in evidence
        assert "!b" in evidence["!a"]
        assert len(evidence["!a"]["!b"]) == 3


class TestConnectionInference:
    """Tests for connection inference"""

    def test_infer_basic_topology(self, simple_topology):
        """Test inference on basic 3-node topology"""
        connections = infer_connections_from_hops(simple_topology)

        assert len(connections) > 0

        # Check for direct connection (0 -> 1 hop)
        direct_connections = [c for c in connections if c["type"] == "inferred_direct"]
        assert len(direct_connections) > 0

        # Verify connection structure
        conn = direct_connections[0]
        assert "from" in conn
        assert "to" in conn
        assert "snr" in conn
        assert "confidence" in conn
        assert "type" in conn

    def test_infer_colocated_connections(self, colocated_topology):
        """Test that co-located nodes are connected"""
        connections = infer_connections_from_hops(colocated_topology)

        # Should have co-located connections
        colocated_conns = [c for c in connections if c["type"] == "colocated"]
        assert len(colocated_conns) > 0

        # Check for Bluetooth pair connection (hopsAway: -1 to hopsAway: 0)
        bluetooth_conns = [
            c for c in colocated_conns
            if c.get("evidence") == "bluetooth_connection"
        ]
        assert len(bluetooth_conns) > 0

    def test_infer_bluetooth_pair_without_gps(self, topology_without_gps):
        """Test Bluetooth pair detection works without GPS"""
        connections = infer_connections_from_hops(topology_without_gps)

        # Should still create Bluetooth pair connection
        bluetooth_conns = [
            c for c in connections
            if c.get("evidence") == "bluetooth_connection"
        ]
        assert len(bluetooth_conns) == 1

        conn = bluetooth_conns[0]
        assert conn["from"] == "!collect1"  # hopsAway: 0
        assert conn["to"] == "!source01"    # hopsAway: -1
        assert conn["confidence"] == "high"

    def test_infer_multi_hop_paths(self, multi_hop_topology):
        """Test inference across multiple hops"""
        connections = infer_connections_from_hops(multi_hop_topology)

        # Should have connections between different hop levels
        hop_connections = [c for c in connections if c["type"] == "inferred_hop"]

        # Should have some inferred hop connections
        assert len(hop_connections) > 0

        # Verify hop connections have proper fields
        for conn in hop_connections:
            assert "total_hops_from_origin" in conn
            assert conn["confidence"] in ["high", "medium", "low"]

    def test_infer_with_routing_validation(self, routing_evidence_topology):
        """Test that routing evidence increases confidence"""
        connections = infer_connections_from_hops(routing_evidence_topology)

        # Look for validated connections
        validated_conns = [
            c for c in connections
            if c.get("evidence") == "routing_validated"
        ]

        # Should have some routing-validated connections
        assert len(validated_conns) > 0

        # Validated connections should have high confidence
        for conn in validated_conns:
            assert conn["confidence"] == "high"
            assert conn["evidence_count"] > 0

    def test_connection_deduplication(self, simple_topology):
        """Test that duplicate connections are not created"""
        connections = infer_connections_from_hops(simple_topology)

        # Create set of connection pairs
        connection_pairs = set()
        for conn in connections:
            pair = tuple(sorted([conn["from"], conn["to"]]))
            assert pair not in connection_pairs, "Duplicate connection found"
            connection_pairs.add(pair)

    def test_connection_statistics(self, multi_hop_topology):
        """Test that connection statistics are reasonable"""
        connections = infer_connections_from_hops(multi_hop_topology)

        # Count by type
        types = {}
        for c in connections:
            t = c["type"]
            types[t] = types.get(t, 0) + 1

        # Should have multiple types
        assert len(types) > 0

        # Count by confidence
        confidences = {}
        for c in connections:
            conf = c.get("confidence", "unknown")
            confidences[conf] = confidences.get(conf, 0) + 1

        # Should have at least one confidence level
        assert len(confidences) > 0

    def test_connection_fields(self, simple_topology):
        """Test that all connections have required fields"""
        connections = infer_connections_from_hops(simple_topology)

        required_fields = ["from", "to", "type", "confidence", "timestamp"]

        for conn in connections:
            for field in required_fields:
                assert field in conn, f"Missing required field: {field}"

    def test_snr_handling(self, simple_topology):
        """Test SNR handling in connections"""
        connections = infer_connections_from_hops(simple_topology)

        for conn in connections:
            # SNR should be present
            assert "snr" in conn

            # SNR should be numeric or None
            if conn["snr"] is not None:
                assert isinstance(conn["snr"], (int, float))


class TestEdgeCases:
    """Tests for edge cases and error handling"""

    def test_empty_topology(self):
        """Test handling of empty topology"""
        topology = {"nodes": {}, "connections": [], "routing_paths": []}
        connections = infer_connections_from_hops(topology)

        # Should return empty list without crashing
        assert connections == []

    def test_single_node(self):
        """Test topology with single node"""
        topology = {
            "nodes": {
                "!only": {
                    "id": "!only",
                    "hopsAway": 0,
                    "snr": 10.0
                }
            },
            "connections": [],
            "routing_paths": []
        }

        connections = infer_connections_from_hops(topology)

        # Should handle gracefully (no connections possible)
        assert len(connections) == 0

    def test_nodes_without_hopsaway(self):
        """Test nodes missing hopsAway field"""
        topology = {
            "nodes": {
                "!node1": {"id": "!node1", "snr": 10.0},
                "!node2": {"id": "!node2", "snr": 5.0}
            },
            "connections": [],
            "routing_paths": []
        }

        # Should not crash
        connections = infer_connections_from_hops(topology)
        assert isinstance(connections, list)

    def test_nodes_with_negative_snr(self):
        """Test handling of negative SNR values"""
        topology = {
            "nodes": {
                "!base": {"id": "!base", "hopsAway": 0, "snr": 10.0},
                "!weak": {"id": "!weak", "hopsAway": 1, "snr": -25.0}
            },
            "connections": [],
            "routing_paths": []
        }

        connections = infer_connections_from_hops(topology)

        # Should create connection even with poor SNR
        assert len(connections) > 0

        # Connection should have the negative SNR value
        direct_conns = [c for c in connections if c["type"] == "inferred_direct"]
        if direct_conns:
            assert direct_conns[0]["snr"] == -25.0
