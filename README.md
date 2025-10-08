# Meshtastic Network Topology Mapper

A Python application that connects to Meshtastic nodes via Bluetooth to collect and visualize network topology.

## Features

- Direct Bluetooth connection to Meshtastic nodes (no MQTT intermediary required)
- Collects network topology information including:
  - Node names and IDs
  - Neighbor relationships
  - Link quality (SNR)
  - Position data
- Intelligent connection inference:
  - GPS-based co-location detection (nodes at same physical site)
  - Bluetooth pair detection (collection source ↔ collection node)
  - Multi-hop path inference with routing evidence validation
  - Confidence levels based on observed packet flows
- Supports collecting data from multiple nodes and aggregating results
- Separate collection and visualization modules
- Interactive network graph visualization with physics-based layout

## Installation

Using uv (recommended):

```bash
# Install uv if you haven't already
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment and install dependencies
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
uv pip install -e .
```

Or with standard pip:

```bash
pip install -r requirements.txt
```

## Usage

### Important: Bluetooth Pairing on macOS

Before connecting to a Meshtastic device on macOS, you must pair it first:

1. Run the pairing helper:
   ```bash
   python pair_device.py
   ```

2. Or manually pair:
   - Open System Settings > Bluetooth
   - Find your Meshtastic device (e.g., "🫘_e885")
   - Click "Connect" or "Pair"
   - Enter PIN: `123456` (default Meshtastic PIN)
   - Wait for pairing to complete

### Quick Start Workflow

```bash
# 1. Scan for available Meshtastic devices
meshnetmap scan

# 2. Collect topology data from a device (5+ minutes recommended)
meshnetmap collect -a <BLE_ADDRESS> -d 300

# 3. Infer connections (co-located nodes, multi-hop paths)
meshnetmap infer -i data/network_topology_TIMESTAMP.json

# 4. Visualize with dynamic physics-based layout
meshnetmap visualize -i data/network_topology_TIMESTAMP_topo_v2.json --show --dynamic
```

### Collecting Network Data

```bash
# Scan for available Meshtastic devices
meshnetmap scan

# Collect data from a specific node (duration in seconds)
meshnetmap collect -a <BLE_ADDRESS> -d 300

# Collect from multiple nodes using config file
meshnetmap aggregate -c nodes.yaml
```

### Inferring Mesh Connections

The `infer` command analyzes collected topology data to detect:
- **Co-located nodes**: Devices at the same GPS location (same physical site)
- **Bluetooth pairs**: Collection source connected to collection node
- **Multi-hop paths**: Validated routing paths with confidence levels
- **Direct connections**: 1-hop neighbors

```bash
# Infer connections from collected data
meshnetmap infer -i data/network_topology.json

# Creates: data/network_topology_topo_v2.json

# Custom output filename
meshnetmap infer -i data/network_topology.json -o my_inferred.json
```

### Visualizing Network Topology

```bash
# Dynamic visualization with physics-based layout (recommended)
meshnetmap visualize -i data/network_topology_topo_v2.json --show --dynamic

# Static Plotly visualization
meshnetmap visualize -i data/network_topology_topo_v2.json --show

# Save to HTML file
meshnetmap visualize -i data/network_topology_topo_v2.json -o network.html --dynamic
```

#### Dynamic Visualization Features

The `--dynamic` flag enables an interactive D3.js force-directed graph with:
- **Physics simulation**: Nodes naturally spread out, avoiding overlaps
- **Node selection**: Click nodes to center and highlight neighbors
- **Clickable edges**: View connection details (SNR, confidence, evidence)
- **Color coding**:
  - Nodes colored by hop distance from collection point
  - Edges colored by signal quality and confidence
- **Interactive controls**: Adjust physics parameters, drag nodes, pan/zoom

## Architecture

- `collector/`: Bluetooth connection and data collection modules
- `inference.py`: Connection inference with co-location detection
- `visualizer/`: Network visualization components (static Plotly + dynamic D3.js)
- `data/`: Storage for collected network topology data

## Data Format

Network topology is stored in JSON format with node information, connections, and metadata.

### Connection Inference Output

The `infer` command adds a `connections` array to the topology JSON:

```json
{
  "connections": [
    {
      "from": "!node1",
      "to": "!node2",
      "snr": 7.5,
      "type": "colocated",           // colocated, inferred_direct, inferred_hop
      "confidence": "high",            // high, medium, low
      "evidence": "same_gps_location", // same_gps_location, bluetooth_connection, routing_validated, snr_heuristic
      "evidence_count": 1,
      "timestamp": "2025-10-07T..."
    }
  ]
}
```

## Documentation

- `DYNAMIC_VIZ.md` - Detailed documentation of dynamic visualization features
- `CO_LOCATION_FIX.md` - Co-location detection implementation details
- `FINAL_SUMMARY.md` - Complete feature summary