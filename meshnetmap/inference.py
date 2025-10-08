#!/usr/bin/env python3
"""
Standalone script to infer hop-by-hop topology from existing topology JSON files
"""
import json
import sys
from datetime import datetime
from collections import defaultdict

def extract_routing_evidence(topology_data):
    """Extract routing evidence from routing_paths to validate inferred connections"""
    routing_paths = topology_data.get('routing_paths', [])
    if not routing_paths:
        return {}

    # Build a map of observed routing: from -> to -> evidence
    routing_evidence = defaultdict(lambda: defaultdict(list))

    for path in routing_paths:
        from_node = path.get('from')
        to_node = path.get('to')
        packet_type = path.get('packet_type', 'unknown')
        hops = path.get('hops_away', 0)

        if from_node and to_node:
            routing_evidence[from_node][to_node].append({
                'packet_type': packet_type,
                'hops': hops,
                'timestamp': path.get('timestamp')
            })

    return routing_evidence

def find_colocated_nodes(topology_data):
    """Find nodes at the same physical location (same GPS coordinates)"""
    location_map = {}  # (lat, lon) -> [node_ids]

    for node_id, node_info in topology_data['nodes'].items():
        position = node_info.get('position', {})
        lat = position.get('latitude')
        lon = position.get('longitude')

        if lat and lon:
            # Round to 4 decimal places (~11m precision)
            loc_key = (round(lat, 4), round(lon, 4))
            if loc_key not in location_map:
                location_map[loc_key] = []
            location_map[loc_key].append((node_id, node_info))

    # Find locations with multiple nodes
    colocated = []
    for loc_key, nodes in location_map.items():
        if len(nodes) > 1:
            colocated.append((loc_key, nodes))

    return colocated

def infer_connections_from_hops(topology_data):
    """Infer mesh connections based on hopsAway data and validate with routing paths"""
    print("Inferring mesh topology from hop distance data...")

    # Extract routing evidence for validation
    routing_evidence = extract_routing_evidence(topology_data)
    if routing_evidence:
        print(f"Found routing evidence for {len(routing_evidence)} source nodes")

    # Find co-located nodes (same physical location)
    colocated = find_colocated_nodes(topology_data)
    if colocated:
        print(f"Found {len(colocated)} locations with multiple nodes:")
        for loc, nodes in colocated:
            node_names = [n[1].get('user', {}).get('longName', n[0][:8]) for n in nodes]
            print(f"  {loc}: {', '.join(node_names)}")

    # Organize nodes by hop distance
    nodes_by_hop = {}
    node_lookup = {}  # For quick node info lookup

    for node_id, node_info in topology_data['nodes'].items():
        hops = node_info.get('hopsAway', -1)
        node_lookup[node_id] = node_info

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
    connection_set = set()  # Track unique connections to avoid duplicates

    # Special case: Connect collection source (hopsAway: -1) to collection node (hopsAway: 0)
    # These are always physically co-located (Bluetooth connection)
    collection_sources = [n for n in topology_data['nodes'].items() if n[1].get('hopsAway') == -1]
    collection_nodes = [n for n in topology_data['nodes'].items() if n[1].get('hopsAway') == 0]

    if collection_sources and collection_nodes:
        print("\nConnecting collection source to collection node(s):")
        for source_id, source_info in collection_sources:
            for node_id, node_info in collection_nodes:
                conn_key = tuple(sorted([source_id, node_id]))
                if conn_key in connection_set:
                    continue

                source_name = source_info.get('user', {}).get('longName', source_id[:8])
                node_name = node_info.get('user', {}).get('longName', node_id[:8])

                # Use collection node's SNR or assume excellent
                snr = node_info.get('snr') or 10.0

                connection = {
                    'from': node_id,  # Collection node (hopsAway: 0) as source
                    'to': source_id,  # Collection source (hopsAway: -1) as target
                    'snr': snr,
                    'type': 'colocated',
                    'confidence': 'high',
                    'hops_away': 0,
                    'evidence': 'bluetooth_connection',
                    'evidence_count': 1,
                    'timestamp': datetime.now().isoformat()
                }
                connections.append(connection)
                connection_set.add(conn_key)
                print(f"  {source_name} ↔ {node_name} (Bluetooth collection pair)")

    # Create connections for co-located nodes
    # These are physically at the same location, so they should be directly connected
    if colocated:
        print("\nCreating connections for co-located nodes (GPS-based):")
        for loc, nodes in colocated:
            # Connect all nodes at this location to each other
            for i, (node1_id, node1_info) in enumerate(nodes):
                for node2_id, node2_info in nodes[i+1:]:
                    # Check if either has hopsAway: 0 (collection node)
                    hops1 = node1_info.get('hopsAway', -1)
                    hops2 = node2_info.get('hopsAway', -1)

                    # Create bidirectional connection
                    conn_key = tuple(sorted([node1_id, node2_id]))
                    if conn_key in connection_set:
                        continue

                    # Use the SNR from whichever node has it
                    snr = node1_info.get('snr') or node2_info.get('snr') or 10.0  # Assume excellent SNR for co-located

                    name1 = node1_info.get('user', {}).get('longName', node1_id[:8])
                    name2 = node2_info.get('user', {}).get('longName', node2_id[:8])

                    connection = {
                        'from': node1_id,
                        'to': node2_id,
                        'snr': snr,
                        'type': 'colocated',
                        'confidence': 'high',
                        'hops_away': 0,
                        'evidence': 'same_gps_location',
                        'evidence_count': 1,
                        'timestamp': datetime.now().isoformat()
                    }
                    connections.append(connection)
                    connection_set.add(conn_key)
                    print(f"  {name1} ↔ {name2} (co-located at {loc})")

                    # If one has hopsAway: 0, make it the "from" node for consistency
                    if hops2 == 0 and hops1 != 0:
                        connection['from'], connection['to'] = connection['to'], connection['from']

    # Create direct connections (0 -> 1 hop)
    if 0 in nodes_by_hop and 1 in nodes_by_hop:
        print(f"\nDirect connections (0 -> 1 hop):")
        for zero_hop in nodes_by_hop[0]:
            for one_hop in nodes_by_hop[1]:
                # Check if we have routing evidence for this connection
                has_evidence = len(routing_evidence.get(zero_hop['id'], {}).get(one_hop['id'], [])) > 0

                connection = {
                    'from': zero_hop['id'],
                    'to': one_hop['id'],
                    'snr': one_hop['snr'],
                    'type': 'inferred_direct',
                    'confidence': 'high' if has_evidence else 'medium',
                    'hops_away': 1,
                    'evidence': 'hop_distance_with_routing' if has_evidence else 'hop_distance',
                    'evidence_count': len(routing_evidence.get(zero_hop['id'], {}).get(one_hop['id'], [])),
                    'timestamp': datetime.now().isoformat()
                }
                connections.append(connection)
                connection_set.add((zero_hop['id'], one_hop['id']))
                print(f"  {zero_hop['id'][:8]} -> {one_hop['id'][:8]} (SNR: {one_hop['snr']}, evidence: {has_evidence})")

    # Infer intermediate hop connections (N -> N+1)
    # Strategy: Only create connections that are likely to be actual physical links
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

            # Check routing evidence to validate connections
            validated_routers = []
            for router in potential_routers:
                # Check if we have routing evidence
                evidence = routing_evidence.get(router['id'], {}).get(next_node['id'], [])
                if evidence:
                    validated_routers.append((router, len(evidence), 'routing_validated'))

            # If no validated routers, use SNR-based heuristic but with lower confidence
            if not validated_routers:
                # Only use best router with good SNR
                good_routers = [n for n in potential_routers if n['snr'] > -10]
                if good_routers:
                    validated_routers.append((good_routers[0], 0, 'snr_heuristic'))
                elif potential_routers:
                    # If no good SNR, only take the single best option
                    validated_routers.append((potential_routers[0], 0, 'best_guess'))

            # Create connections only for validated or highly likely routers
            for router, evidence_count, validation_type in validated_routers[:2]:  # Limit to top 2
                conn_key = (router['id'], next_node['id'])
                if conn_key in connection_set:
                    continue  # Skip duplicates

                if validation_type == 'routing_validated':
                    confidence = 'high'
                elif validation_type == 'snr_heuristic' and router['snr'] > 0:
                    confidence = 'medium'
                else:
                    confidence = 'low'

                connection = {
                    'from': router['id'],
                    'to': next_node['id'],
                    'snr': next_node['snr'],
                    'type': 'inferred_hop',
                    'confidence': confidence,
                    'hops_away': 1,
                    'total_hops_from_origin': hop_level + 1,
                    'evidence': validation_type,
                    'evidence_count': evidence_count,
                    'router_snr': router['snr'],
                    'timestamp': datetime.now().isoformat()
                }
                connections.append(connection)
                connection_set.add(conn_key)

    print(f"\nTotal connections inferred: {len(connections)}")

    # Show statistics
    by_type = {}
    by_confidence = {}
    for c in connections:
        t = c['type']
        conf = c.get('confidence', 'unknown')
        by_type[t] = by_type.get(t, 0) + 1
        by_confidence[conf] = by_confidence.get(conf, 0) + 1

    print(f"Connection types: {by_type}")
    print(f"Confidence levels: {by_confidence}")

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
