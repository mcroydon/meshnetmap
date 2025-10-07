#!/usr/bin/env python3
"""
Standalone script to infer hop-by-hop topology from existing topology JSON files
"""
import json
import sys
from datetime import datetime

def infer_connections_from_hops(topology_data):
    """Infer mesh connections based on hopsAway data from node database"""
    print("Inferring mesh topology from hop distance data...")

    # Organize nodes by hop distance
    nodes_by_hop = {}
    for node_id, node_info in topology_data['nodes'].items():
        hops = node_info.get('hopsAway', -1)
        if hops < 0:
            continue
        if hops not in nodes_by_hop:
            nodes_by_hop[hops] = []
        nodes_by_hop[hops].append({
            'id': node_id,
            'snr': node_info.get('snr', -100),
            'lastHeard': node_info.get('lastHeard', 0)
        })

    if not nodes_by_hop:
        print("WARNING: No nodes with valid hop distances found")
        return []

    print(f"Hop distribution: {[(h, len(nodes_by_hop[h])) for h in sorted(nodes_by_hop.keys())]}")

    connections = []

    # Create direct connections (0 -> 1 hop)
    if 0 in nodes_by_hop and 1 in nodes_by_hop:
        print(f"\nDirect connections (0 -> 1 hop):")
        for zero_hop in nodes_by_hop[0]:
            for one_hop in nodes_by_hop[1]:
                connection = {
                    'from': zero_hop['id'],
                    'to': one_hop['id'],
                    'snr': one_hop['snr'],
                    'type': 'inferred_direct',
                    'confidence': 'high',
                    'hops_away': 1,
                    'evidence': 'hop_distance',
                    'timestamp': datetime.now().isoformat()
                }
                connections.append(connection)
                print(f"  {zero_hop['id'][:8]} -> {one_hop['id'][:8]} (SNR: {one_hop['snr']})")

    # Infer intermediate hop connections (N -> N+1)
    max_hop = max(nodes_by_hop.keys())
    for hop_level in range(1, max_hop):
        if hop_level not in nodes_by_hop or hop_level + 1 not in nodes_by_hop:
            continue

        current_hop_nodes = nodes_by_hop[hop_level]
        next_hop_nodes = nodes_by_hop[hop_level + 1]

        print(f"\nInferring connections: hop {hop_level} -> {hop_level + 1} ({len(next_hop_nodes)} nodes)")

        # For each node at hop N+1, infer which node at hop N it likely routes through
        for next_node in next_hop_nodes:
            # Strategy: prefer nodes with better SNR as likely intermediate routers
            potential_routers = sorted(current_hop_nodes, key=lambda x: x['snr'], reverse=True)

            # Use all nodes with good SNR, or top 3 if none have positive SNR
            good_routers = [n for n in potential_routers if n['snr'] > -15]
            if not good_routers:
                good_routers = potential_routers[:3]

            for router in good_routers[:3]:  # Limit to top 3 candidates
                confidence = 'high' if router['snr'] > 0 else 'medium' if router['snr'] > -15 else 'low'
                connection = {
                    'from': router['id'],
                    'to': next_node['id'],
                    'snr': next_node['snr'],
                    'type': 'inferred_hop',
                    'confidence': confidence,
                    'hops_away': 1,
                    'total_hops_from_origin': hop_level + 1,
                    'evidence': f'hop_inference_via_{router["id"][:8]}',
                    'router_snr': router['snr'],
                    'timestamp': datetime.now().isoformat()
                }
                connections.append(connection)

    print(f"\nTotal connections inferred: {len(connections)}")

    # Show statistics
    by_type = {}
    for c in connections:
        t = c['type']
        by_type[t] = by_type.get(t, 0) + 1
    print(f"Connection types: {by_type}")

    return connections

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 infer_connections_v2.py <topology_file.json>")
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
    output_file = input_file.replace('.json', '_topo_v2.json')
    with open(output_file, 'w') as f:
        json.dump(topology, f, indent=2, default=str)

    print(f"\nSaved to {output_file}")
