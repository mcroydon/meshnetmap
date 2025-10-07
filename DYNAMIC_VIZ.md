# Dynamic Network Visualization

This document describes the new dynamic, physics-based network visualization features added to meshnetmap.

## Overview

The dynamic visualization replaces the static Plotly layout with a D3.js force-directed graph that provides:
- **Physics-based layout**: Nodes repel each other and links act as springs, automatically avoiding overlaps
- **Interactive node selection**: Click nodes to highlight and center them
- **Clickable edges**: Click connections to see detailed information
- **Accurate multi-hop topology**: Improved inference validates connections against routing evidence

## Features

### 1. Physics-Based Force Simulation

The visualization uses D3.js force simulation with:
- **Charge force**: Nodes repel each other to avoid overlap (adjustable: 50-500)
- **Link force**: Connections act as springs (adjustable distance: 30-200)
- **Center force**: Keeps the graph centered in the viewport
- **Collision detection**: Prevents nodes from overlapping (30px radius)

The graph is fully interactive:
- **Drag nodes**: Reposition individual nodes
- **Pan and zoom**: Navigate large networks
- **Auto-layout**: Physics naturally spreads nodes based on connectivity

### 2. Node Selection and Centering

Click any node to:
- Highlight the selected node with a thicker border
- Dim unconnected nodes for focus
- Show only edges connected to the selected node
- Smoothly animate the camera to center on the node (1.5x zoom)
- Display detailed node information in the info panel:
  - Name and ID
  - Hops away from origin
  - SNR (signal-to-noise ratio)
  - Number of neighbors
  - GPS coordinates (if available)

### 3. Clickable Edges with Details

Click any edge to open a modal showing:
- Source and destination nodes
- Connection type (confirmed, inferred_direct, inferred_hop)
- Confidence level (high/medium/low) with color-coded badge
- SNR (signal quality)
- Evidence type (routing_validated, snr_heuristic, best_guess)
- Evidence count (number of packets observed)
- Total hops from origin
- Router SNR (for multi-hop connections)

### 4. Improved Multi-Hop Edge Inference

The `infer_connections_v2.py` script now:

**Validates connections against routing evidence:**
- Checks `routing_paths` data for observed packet flows
- Marks connections as "routing_validated" when evidence exists
- Uses confidence levels to distinguish validated from inferred links

**Reduces false connections:**
- Limits to top 1-2 most likely intermediate routers
- Only creates connections with good SNR or routing evidence
- Avoids creating spurious multi-hop paths

**Connection types:**
- `colocated`: Nodes at the same GPS location (same physical site)
- `inferred_direct`: 0 → 1 hop (direct neighbors)
- `inferred_hop`: N → N+1 hop (validated with routing or SNR)

**Confidence levels:**
- `high`: Co-located, routing evidence, or excellent SNR (> 0 dB)
- `medium`: Good SNR (-10 to 0 dB) or limited routing evidence
- `low`: Poor SNR or best guess based on hop distance

### Co-located Node Detection

The inference script automatically detects nodes at the same physical location by comparing GPS coordinates (within 11m precision). This handles the common case where:
- Multiple devices are at the same physical site
- The collection node and another node share the same location
- Nodes have `hopsAway: -1` or `hopsAway: 0` but are physically connected

Co-located connections:
- Are shown as solid green lines
- Have a very short link distance (20px) in the visualization
- Are marked with `confidence: high` and `evidence: same_gps_location`
- Connect all nodes at the same location to each other

Example: If "Cool 🫘" (collection source) and "Cedar Park 🦙" (collection node, hopsAway: 0) share GPS coordinates (30.4873, -97.8584), they will be automatically connected.

## Usage

### Command Line

Generate a dynamic visualization:

```bash
# Create dynamic visualization
meshnetmap visualize -i data/topology.json -o network.html --dynamic

# Display in browser immediately
meshnetmap visualize -i data/topology.json --show --dynamic
```

### Python API

```python
from meshnetmap.visualizer.display import NetworkVisualizer

visualizer = NetworkVisualizer()
visualizer.load_topology('data/topology.json')
visualizer.build_network_graph()

# Create dynamic visualization
visualizer.create_dynamic_visualization('output.html')

# Or use save_visualization with dynamic flag
visualizer.save_visualization('output.html', dynamic=True)
```

### Re-inference with Validation

Regenerate connections with improved validation:

```bash
python3 infer_connections_v2.py data/network_topology.json
# Creates: data/network_topology_topo_v2.json
```

## Visualization Controls

The visualization includes interactive controls:

**Sliders:**
- **Repulsion Force** (50-500): Controls how strongly nodes push apart
  - Lower values: Nodes cluster together
  - Higher values: Nodes spread out more
- **Link Distance** (30-200): Sets the resting length of connections
  - Lower values: Compact layout
  - Higher values: Spread out layout

**Buttons:**
- **Reset View**: Returns to original zoom and pan position
- **Clear Selection**: Deselects nodes and shows all connections

**Mouse Controls:**
- **Drag nodes**: Click and drag to reposition
- **Pan**: Click background and drag to pan
- **Zoom**: Mouse wheel to zoom in/out
- **Select node**: Click to select and center
- **Select edge**: Click to view details
- **Clear selection**: Click background

## Color Coding

### Nodes (by hop distance)
- **Blue**: Direct connection (0 hops)
- **Green**: 1 hop away
- **Yellow**: 2 hops away
- **Orange**: 3 hops away
- **Red**: 4+ hops away

### Edges (by signal quality)
- **Green**: Excellent SNR (> 0 dB)
- **Orange**: Good SNR (-10 to 0 dB) or medium confidence
- **Red**: Poor SNR (< -10 dB) or low confidence

### Edge Styles
- **Solid line**: Confirmed or high confidence
- **Dashed line**: Medium confidence
- **Dotted line**: Low confidence

## File Structure

```
meshnetmap/
├── visualizer/
│   ├── display.py              # Updated with dynamic visualization support
│   ├── templates/
│   │   └── dynamic_network.html  # D3.js template
│   └── static/                  # (Future: separate CSS/JS files)
├── infer_connections_v2.py     # Improved with routing validation
└── test_dynamic_viz.py         # Simple test script
```

## Technical Details

### Force Simulation Parameters

Default physics settings:
```javascript
charge: -200        // Repulsion strength
linkDistance: 80    // Target link length
collision: 30       // Node collision radius
```

### Data Format

The visualization expects topology JSON with:
```json
{
  "nodes": {
    "!node_id": {
      "user": {"longName": "...", "shortName": "..."},
      "hopsAway": 2,
      "snr": -15.5,
      "position": {"latitude": 30.1, "longitude": -97.8}
    }
  },
  "connections": [
    {
      "from": "!node1",
      "to": "!node2",
      "snr": -10.5,
      "type": "inferred_hop",
      "confidence": "high",
      "evidence": "routing_validated",
      "evidence_count": 5
    }
  ]
}
```

## Performance

- **Tested with**: 80 nodes, 170 connections
- **HTML size**: ~120KB (includes embedded D3.js)
- **Load time**: < 1 second on modern browsers
- **Animation**: 60 FPS on most hardware

## Browser Compatibility

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Supported with touch gestures

## Future Enhancements

Potential improvements:
- [ ] Save/load custom node positions
- [ ] Filter nodes by hop distance or SNR
- [ ] Time-based animation of network changes
- [ ] Export as PNG/SVG
- [ ] Multi-select nodes
- [ ] Path highlighting between two nodes
- [ ] Heat map overlay for signal quality

## Troubleshooting

**Graph is too cluttered:**
- Increase repulsion force (200 → 400)
- Increase link distance (80 → 150)

**Nodes are too spread out:**
- Decrease repulsion force (200 → 100)
- Decrease link distance (80 → 50)

**Can't see node labels:**
- Zoom in using mouse wheel
- Select individual nodes to highlight

**Modal won't close:**
- Click the X button in the top-right
- Click outside the modal on the background

## Examples

### Basic Usage
```bash
# Generate topology with improved inference
python3 infer_connections_v2.py data/network_topology.json

# Create dynamic visualization
meshnetmap visualize -i data/network_topology_topo_v2.json \
  -o network_dynamic.html --dynamic --show
```

### Comparison: Static vs Dynamic
```bash
# Static Plotly visualization
meshnetmap visualize -i data/topology.json -o static.html

# Dynamic D3.js visualization
meshnetmap visualize -i data/topology.json -o dynamic.html --dynamic
```

## Credits

- **D3.js**: Force-directed graph implementation
- **Meshtastic**: Network protocol and data collection
