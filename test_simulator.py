#!/usr/bin/env python3
"""
Test simulator to create sample topology data for testing visualization
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path


def generate_test_topology():
    """Generate sample topology data for testing"""
    
    # Create sample nodes
    nodes = {
        "!abcd1234": {
            "id": "!abcd1234",
            "num": 1234,
            "user": {
                "longName": "Base Station",
                "shortName": "BASE"
            },
            "position": {
                "latitude": 37.7749,
                "longitude": -122.4194
            },
            "lastHeard": (datetime.now() - timedelta(minutes=1)).isoformat(),
            "snr": 10.5,
            "hopsAway": 0
        },
        "!efgh5678": {
            "id": "!efgh5678",
            "num": 5678,
            "user": {
                "longName": "Mobile Node 1",
                "shortName": "MOB1"
            },
            "position": {
                "latitude": 37.7849,
                "longitude": -122.4094
            },
            "lastHeard": (datetime.now() - timedelta(minutes=5)).isoformat(),
            "snr": 5.2,
            "hopsAway": 1
        },
        "!ijkl9012": {
            "id": "!ijkl9012",
            "num": 9012,
            "user": {
                "longName": "Mobile Node 2",
                "shortName": "MOB2"
            },
            "position": {
                "latitude": 37.7649,
                "longitude": -122.4294
            },
            "lastHeard": (datetime.now() - timedelta(minutes=3)).isoformat(),
            "snr": 7.8,
            "hopsAway": 1
        },
        "!mnop3456": {
            "id": "!mnop3456",
            "num": 3456,
            "user": {
                "longName": "Relay Station",
                "shortName": "RELAY"
            },
            "position": {
                "latitude": 37.7949,
                "longitude": -122.3994
            },
            "lastHeard": (datetime.now() - timedelta(minutes=2)).isoformat(),
            "snr": 8.1,
            "hopsAway": 1
        },
        "!qrst7890": {
            "id": "!qrst7890",
            "num": 7890,
            "user": {
                "longName": "Remote Node 1",
                "shortName": "REM1"
            },
            "position": {
                "latitude": 37.8049,
                "longitude": -122.3894
            },
            "lastHeard": (datetime.now() - timedelta(minutes=10)).isoformat(),
            "snr": -2.3,
            "hopsAway": 2
        },
        "!uvwx2468": {
            "id": "!uvwx2468",
            "num": 2468,
            "user": {
                "longName": "Remote Node 2",
                "shortName": "REM2"
            },
            "position": {},
            "lastHeard": (datetime.now() - timedelta(minutes=15)).isoformat(),
            "snr": -5.1,
            "hopsAway": 3
        }
    }
    
    # Create connections with varying SNR values
    connections = [
        # Base station connections
        {
            "from": "!abcd1234",
            "to": "!efgh5678",
            "snr": 8.5,
            "timestamp": datetime.now().isoformat()
        },
        {
            "from": "!abcd1234",
            "to": "!ijkl9012",
            "snr": 9.2,
            "timestamp": datetime.now().isoformat()
        },
        {
            "from": "!abcd1234",
            "to": "!mnop3456",
            "snr": 10.1,
            "timestamp": datetime.now().isoformat()
        },
        # Mobile node connections
        {
            "from": "!efgh5678",
            "to": "!ijkl9012",
            "snr": 4.3,
            "timestamp": datetime.now().isoformat()
        },
        {
            "from": "!efgh5678",
            "to": "!abcd1234",
            "snr": 7.8,
            "timestamp": datetime.now().isoformat()
        },
        # Relay connections
        {
            "from": "!mnop3456",
            "to": "!qrst7890",
            "snr": 5.6,
            "timestamp": datetime.now().isoformat()
        },
        {
            "from": "!mnop3456",
            "to": "!abcd1234",
            "snr": 9.8,
            "timestamp": datetime.now().isoformat()
        },
        {
            "from": "!mnop3456",
            "to": "!uvwx2468",
            "snr": -1.2,
            "timestamp": datetime.now().isoformat()
        },
        # Remote connections
        {
            "from": "!qrst7890",
            "to": "!mnop3456",
            "snr": 4.2,
            "timestamp": datetime.now().isoformat()
        },
        {
            "from": "!qrst7890",
            "to": "!uvwx2468",
            "snr": -3.5,
            "timestamp": datetime.now().isoformat()
        },
        {
            "from": "!uvwx2468",
            "to": "!qrst7890",
            "snr": -4.1,
            "timestamp": datetime.now().isoformat()
        }
    ]
    
    topology_data = {
        "nodes": nodes,
        "connections": connections,
        "metadata": {
            "collection_time": datetime.now().isoformat(),
            "collection_device": "Test Simulator"
        }
    }
    
    return topology_data


def generate_large_test_topology(num_nodes=20):
    """Generate a larger test topology with specified number of nodes"""
    
    nodes = {}
    connections = []
    
    # Generate nodes
    for i in range(num_nodes):
        node_id = f"!node{i:04d}"
        nodes[node_id] = {
            "id": node_id,
            "num": 1000 + i,
            "user": {
                "longName": f"Test Node {i}",
                "shortName": f"NODE{i}"
            },
            "position": {
                "latitude": 37.7749 + random.uniform(-0.1, 0.1),
                "longitude": -122.4194 + random.uniform(-0.1, 0.1)
            } if random.random() > 0.3 else {},  # 70% have position
            "lastHeard": (datetime.now() - timedelta(minutes=random.randint(1, 60))).isoformat(),
            "snr": random.uniform(-10, 15),
            "hopsAway": min(i // 5, 4)  # Groups nodes by hop distance
        }
    
    # Generate connections (create a somewhat realistic mesh)
    for i in range(num_nodes):
        from_node = f"!node{i:04d}"
        
        # Each node connects to 2-5 other nodes
        num_connections = random.randint(2, min(5, num_nodes - 1))
        
        # Prefer connecting to nearby nodes (by index)
        for _ in range(num_connections):
            # Weighted towards nearby nodes
            if random.random() < 0.7:
                # Connect to nearby node
                offset = random.randint(1, 3)
                to_idx = (i + offset) % num_nodes
            else:
                # Connect to random node
                to_idx = random.randint(0, num_nodes - 1)
            
            if to_idx != i:  # Don't connect to self
                to_node = f"!node{to_idx:04d}"
                
                # Calculate SNR based on "distance" (index difference)
                distance = abs(to_idx - i)
                base_snr = 15 - distance * 2
                snr = base_snr + random.uniform(-3, 3)
                
                connections.append({
                    "from": from_node,
                    "to": to_node,
                    "snr": snr,
                    "timestamp": datetime.now().isoformat()
                })
    
    topology_data = {
        "nodes": nodes,
        "connections": connections,
        "metadata": {
            "collection_time": datetime.now().isoformat(),
            "collection_device": "Test Simulator (Large)"
        }
    }
    
    return topology_data


def main():
    """Generate test topology files"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate test topology data')
    parser.add_argument('--type', choices=['small', 'large'], default='small',
                       help='Type of test data to generate')
    parser.add_argument('--nodes', type=int, default=20,
                       help='Number of nodes for large topology')
    parser.add_argument('--output', '-o', help='Output filename')
    
    args = parser.parse_args()
    
    # Generate topology
    if args.type == 'small':
        topology = generate_test_topology()
        default_output = 'data/test_topology_small.json'
    else:
        topology = generate_large_test_topology(args.nodes)
        default_output = f'data/test_topology_large_{args.nodes}.json'
    
    output_file = args.output or default_output
    
    # Ensure data directory exists
    Path("data").mkdir(exist_ok=True)
    
    # Save to file
    with open(output_file, 'w') as f:
        json.dump(topology, f, indent=2)
    
    print(f"Test topology generated: {output_file}")
    print(f"  Nodes: {len(topology['nodes'])}")
    print(f"  Connections: {len(topology['connections'])}")
    print(f"\nTo visualize, run:")
    print(f"  python meshnetmap.py visualize -i {output_file} --show")


if __name__ == "__main__":
    main()