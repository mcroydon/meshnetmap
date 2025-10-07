#!/usr/bin/env python3
"""
Simple test script for dynamic visualization
"""
import json
import os

# Read topology data
with open('data/network_topology_20251006_221020_topo_v2.json', 'r') as f:
    topology_data = json.load(f)

# Read template
template_path = 'meshnetmap/visualizer/templates/dynamic_network.html'
with open(template_path, 'r') as f:
    template = f.read()

# Inject topology data
topology_json = json.dumps(topology_data, indent=2, default=str)
html_content = template.replace('{{TOPOLOGY_DATA}}', topology_json)

# Write output
output_path = 'data/dynamic_test.html'
with open(output_path, 'w') as f:
    f.write(html_content)

print(f"✓ Dynamic visualization created: {output_path}")
print(f"  - Nodes: {len(topology_data['nodes'])}")
print(f"  - Connections: {len(topology_data.get('connections', []))}")
print(f"\nOpen in browser: file://{os.path.abspath(output_path)}")
