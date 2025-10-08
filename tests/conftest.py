"""Pytest fixtures and configuration"""
import pytest
from datetime import datetime, timedelta


@pytest.fixture
def sample_node():
    """Create a sample node for testing"""
    return {
        "id": "!abcd1234",
        "num": 1234,
        "user": {
            "longName": "Test Node",
            "shortName": "TEST"
        },
        "position": {
            "latitude": 37.7749,
            "longitude": -122.4194
        },
        "lastHeard": datetime.now().isoformat(),
        "snr": 10.5,
        "hopsAway": 0
    }


@pytest.fixture
def simple_topology():
    """Create a simple topology with 3 nodes"""
    return {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "source": "test"
        },
        "nodes": {
            "!node0001": {
                "id": "!node0001",
                "num": 1,
                "user": {"longName": "Base Station", "shortName": "BASE"},
                "position": {"latitude": 37.7749, "longitude": -122.4194},
                "lastHeard": datetime.now().isoformat(),
                "snr": 10.0,
                "hopsAway": 0
            },
            "!node0002": {
                "id": "!node0002",
                "num": 2,
                "user": {"longName": "Node One", "shortName": "NOD1"},
                "position": {"latitude": 37.7850, "longitude": -122.4094},
                "lastHeard": datetime.now().isoformat(),
                "snr": 5.0,
                "hopsAway": 1
            },
            "!node0003": {
                "id": "!node0003",
                "num": 3,
                "user": {"longName": "Node Two", "shortName": "NOD2"},
                "position": {"latitude": 37.7950, "longitude": -122.3994},
                "lastHeard": datetime.now().isoformat(),
                "snr": -5.0,
                "hopsAway": 2
            }
        },
        "connections": [],
        "routing_paths": []
    }


@pytest.fixture
def colocated_topology():
    """Create a topology with co-located nodes"""
    return {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "source": "test"
        },
        "nodes": {
            "!source01": {
                "id": "!source01",
                "num": 1,
                "user": {"longName": "Collection Source", "shortName": "SRC"},
                "position": {"latitude": 30.4873, "longitude": -97.8584},
                "lastHeard": datetime.now().isoformat(),
                "snr": None,
                "hopsAway": -1
            },
            "!collect1": {
                "id": "!collect1",
                "num": 2,
                "user": {"longName": "Collection Node", "shortName": "COL"},
                "position": {"latitude": 30.4873, "longitude": -97.8584},
                "lastHeard": datetime.now().isoformat(),
                "snr": 7.5,
                "hopsAway": 0
            },
            "!mobile01": {
                "id": "!mobile01",
                "num": 3,
                "user": {"longName": "Mobile Node", "shortName": "MOB"},
                "position": {"latitude": 30.4873, "longitude": -97.8584},
                "lastHeard": datetime.now().isoformat(),
                "snr": 8.0,
                "hopsAway": 0
            },
            "!remote01": {
                "id": "!remote01",
                "num": 4,
                "user": {"longName": "Remote Node", "shortName": "REM"},
                "position": {"latitude": 30.5000, "longitude": -97.9000},
                "lastHeard": datetime.now().isoformat(),
                "snr": -10.0,
                "hopsAway": 1
            }
        },
        "connections": [],
        "routing_paths": []
    }


@pytest.fixture
def routing_evidence_topology():
    """Create a topology with routing evidence"""
    base_time = datetime.now()

    return {
        "metadata": {
            "collected_at": base_time.isoformat(),
            "source": "test"
        },
        "nodes": {
            "!node0001": {
                "id": "!node0001",
                "num": 1,
                "user": {"longName": "Base", "shortName": "BASE"},
                "position": {"latitude": 37.7749, "longitude": -122.4194},
                "lastHeard": base_time.isoformat(),
                "snr": 10.0,
                "hopsAway": 0
            },
            "!node0002": {
                "id": "!node0002",
                "num": 2,
                "user": {"longName": "Hop1", "shortName": "HOP1"},
                "position": {"latitude": 37.7850, "longitude": -122.4094},
                "lastHeard": base_time.isoformat(),
                "snr": 5.0,
                "hopsAway": 1
            },
            "!node0003": {
                "id": "!node0003",
                "num": 3,
                "user": {"longName": "Hop2", "shortName": "HOP2"},
                "position": {"latitude": 37.7950, "longitude": -122.3994},
                "lastHeard": base_time.isoformat(),
                "snr": -5.0,
                "hopsAway": 2
            }
        },
        "connections": [],
        "routing_paths": [
            {
                "from": "!node0001",
                "to": "!node0002",
                "packet_type": "position",
                "hops_away": 1,
                "timestamp": (base_time - timedelta(minutes=5)).isoformat()
            },
            {
                "from": "!node0002",
                "to": "!node0003",
                "packet_type": "position",
                "hops_away": 1,
                "timestamp": (base_time - timedelta(minutes=3)).isoformat()
            }
        ]
    }


@pytest.fixture
def multi_hop_topology():
    """Create a topology with multiple hop levels"""
    nodes = {}

    # Create nodes at different hop distances
    for hop in range(5):
        for i in range(3):
            node_id = f"!hop{hop}n{i}"
            nodes[node_id] = {
                "id": node_id,
                "num": hop * 100 + i,
                "user": {
                    "longName": f"Hop {hop} Node {i}",
                    "shortName": f"H{hop}N{i}"
                },
                "position": {
                    "latitude": 37.7749 + (hop * 0.01) + (i * 0.001),
                    "longitude": -122.4194 + (hop * 0.01) + (i * 0.001)
                },
                "lastHeard": datetime.now().isoformat(),
                "snr": 10.0 - (hop * 3) - (i * 0.5),
                "hopsAway": hop
            }

    return {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "source": "test"
        },
        "nodes": nodes,
        "connections": [],
        "routing_paths": []
    }


@pytest.fixture
def topology_without_gps():
    """Create a topology where nodes lack GPS coordinates"""
    return {
        "metadata": {
            "collected_at": datetime.now().isoformat(),
            "source": "test"
        },
        "nodes": {
            "!source01": {
                "id": "!source01",
                "num": 1,
                "user": {"longName": "Source No GPS", "shortName": "SRC"},
                "position": {"time": 1234567890},  # Only time, no lat/lon
                "lastHeard": datetime.now().isoformat(),
                "snr": None,
                "hopsAway": -1
            },
            "!collect1": {
                "id": "!collect1",
                "num": 2,
                "user": {"longName": "Collector No GPS", "shortName": "COL"},
                "position": {"time": 1234567891},  # Only time, no lat/lon
                "lastHeard": datetime.now().isoformat(),
                "snr": 7.5,
                "hopsAway": 0
            }
        },
        "connections": [],
        "routing_paths": []
    }
