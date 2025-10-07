# Meshtastic Network Topology Mapper

A Python application that connects to Meshtastic nodes via Bluetooth to collect and visualize network topology.

## Features

- Direct Bluetooth connection to Meshtastic nodes (no MQTT intermediary required)
- Collects network topology information including:
  - Node names and IDs
  - Neighbor relationships
  - Link quality (SNR)
  - Position data
- Supports collecting data from multiple nodes and aggregating results
- Separate collection and visualization modules
- Interactive network graph visualization

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

### Collecting Network Data

```bash
# Scan for available Meshtastic devices
meshnetmap scan

# Collect data from a specific node
meshnetmap collect -a <BLE_ADDRESS>

# Collect from multiple nodes using config file
meshnetmap aggregate -c nodes.yaml
```

### Visualizing Network Topology

```bash
# Visualize the collected network data
meshnetmap visualize -i data/network_topology.json --show

# Generate static HTML graph
meshnetmap visualize -i data/network_topology.json -o network_map.html
```

## Architecture

- `collector/`: Bluetooth connection and data collection modules
- `visualizer/`: Network visualization components
- `data/`: Storage for collected network topology data

## Data Format

Network topology is stored in JSON format with node information, connections, and metadata.