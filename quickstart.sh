#!/bin/bash

# Meshtastic Network Topology Mapper - Quick Start Script

echo "========================================"
echo "Meshtastic Network Topology Mapper"
echo "========================================"
echo

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.local/bin:$PATH"
fi

# Create and activate virtual environment
echo "Setting up Python environment..."
uv venv
source .venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
uv pip install -e .

echo
echo "Setup complete! Generating test data..."
echo

# Generate test data
python test_simulator.py --type small
python test_simulator.py --type large --nodes 20

echo
echo "========================================"
echo "Quick Start Examples:"
echo "========================================"
echo
echo "1. Scan for Meshtastic devices:"
echo "   python meshnetmap.py scan"
echo
echo "2. Collect from a specific device:"
echo "   python meshnetmap.py collect -a <DEVICE_ADDRESS>"
echo
echo "3. Visualize test data:"
echo "   python meshnetmap.py visualize -i data/test_topology_small.json --show"
echo
echo "4. Generate HTML visualization:"
echo "   python meshnetmap.py visualize -i data/test_topology_large_20.json -o network_map.html"
echo
echo "========================================"