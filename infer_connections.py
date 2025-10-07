#!/usr/bin/env python3
"""
Standalone script to infer connections from existing topology JSON files
"""
import json
import sys
from datetime import datetime

def infer_connections_from_hops(topology_data):
    """Infer mesh connections based on hopsAway data from node database"""
    print("Inferring connections from hop distance data...")

    # Get our connected node (hopsAway == 0)
    our_nodes = []
    one_hop_nodes = []
    multi_hop_nodes = {}

    for node_id, node_info in topology_data['nodes'].items():
        hops = node_info.get('hopsAway', -1)
        snr = node_info.get('snr', 0)

        if hops == 0:
            our_nodes.append(node_id)
        elif hops == 1:
            one_hop_nodes.append((node_id, snr))
        elif hops > 1:
            if hops not in multi_hop_nodes:
                multi_hop_nodes[hops] = []
            multi_hop_nodes[hops].append((node_id, snr))

    print(f"Found {len(our_nodes)} directly connected nodes, {len(one_hop_nodes)} 1-hop neighbors")

    connections = []

    # Create direct connections (1 hop = direct radio link)
    for node_id, snr in one_hop_nodes:
        our_node = our_nodes[0] if our_nodes else None
        if our_node:
            connection = {
                'from': our_node,
                'to': node_id,
                'snr': snr,
                'type': 'inferred_direct',
                'confidence': 'high',
                'hops_away': 1,
                'evidence': 'node_database',
                'timestamp': datetime.now().isoformat()
            }
            connections.append(connection)
            print(f"  Direct: {our_node[:8]} -> {node_id[:8]} (SNR: {snr})")

    # Create implied multi-hop connections
    for hops, nodes in multi_hop_nodes.items():
        for node_id, snr in nodes:
            our_node = our_nodes[0] if our_nodes else None
            if our_node:
                connection = {
                    'from': our_node,
                    'to': node_id,
                    'snr': snr,
                    'type': 'inferred_multihop',
                    'confidence': 'medium',
                    'hops_away': hops,
                    'evidence': 'node_database',
                    'timestamp': datetime.now().isoformat()
                }
                connections.append(connection)

    print(f"Inferred {len(connections)} total connections")
    return connections

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 infer_connections.py <topology_file.json>")
        sys.exit(1)

    input_file = sys.argv[1]

    # Load topology
    with open(input_file, 'r') as f:
        topology = json.load(f)

    # Infer connections
    connections = infer_connections_from_hops(topology)

    # Update topology
    topology['connections'] = connections

    # Save
    output_file = input_file.replace('.json', '_inferred.json')
    with open(output_file, 'w') as f:
        json.dump(topology, f, indent=2, default=str)

    print(f"\nSaved to {output_file}")
