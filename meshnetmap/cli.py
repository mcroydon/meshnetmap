#!/usr/bin/env python3
"""
Main entry point for Meshtastic Network Topology Mapper
"""

import sys
import argparse
import logging

from .collector.scanner import MeshtasticScanner
from .collector.collect import NetworkTopologyCollector
from .collector.aggregator import TopologyAggregator
from .visualizer.display import NetworkVisualizer
from .inference import infer_connections_from_hops

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def scan_command(args):
    """Handle scan command"""
    scanner = MeshtasticScanner()
    devices = scanner.scan_devices()
    
    if devices:
        print("\n" + "="*50)
        print("DISCOVERED MESHTASTIC DEVICES")
        print("="*50)
        for idx, device in enumerate(devices, 1):
            print(f"\n{idx}. Name: {device['name']}")
            print(f"   Address: {device['address']}")
            if device['rssi']:
                print(f"   RSSI: {device['rssi']} dBm")
    else:
        print("\nNo Meshtastic devices found")


def collect_command(args):
    """Handle collect command"""
    collector = NetworkTopologyCollector()

    try:
        if collector.connect(args.address, args.pin):
            topology = collector.collect_topology(args.duration)
            collector.save_topology(args.output)

            # Print summary
            print(f"\n{'='*50}")
            print("COLLECTION SUMMARY")
            print(f"{'='*50}")
            print(f"Nodes discovered: {len(topology['nodes'])}")
            print(f"Connections mapped: {len(topology['connections'])}")
        else:
            logger.error("Failed to connect to device")
            sys.exit(1)

    except KeyboardInterrupt:
        logger.info("Collection interrupted by user")
        sys.exit(0)

    finally:
        collector.disconnect()
        # Force exit after collection completes
        sys.exit(0)


def aggregate_command(args):
    """Handle aggregate command"""
    aggregator = TopologyAggregator()

    if args.config:
        aggregator.aggregate_from_config(args.config)
    else:
        aggregator.aggregate_from_directory(args.directory)

    aggregator.save_aggregated_data(args.output)


def infer_command(args):
    """Handle infer command"""
    import json

    logger.info(f"Loading topology from {args.input}")

    try:
        with open(args.input, 'r') as f:
            topology_data = json.load(f)
    except FileNotFoundError:
        logger.error(f"Input file not found: {args.input}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in input file: {e}")
        sys.exit(1)

    # Run inference
    connections = infer_connections_from_hops(topology_data)

    # Update topology with inferred connections
    topology_data['connections'] = connections

    # Determine output filename
    if args.output:
        output_file = args.output
    else:
        # Default: add _topo_v2 suffix before .json extension
        output_file = args.input.replace('.json', '_topo_v2.json')
        if output_file == args.input:  # If no .json extension
            output_file = args.input + '_topo_v2'

    # Save inferred topology
    try:
        with open(output_file, 'w') as f:
            json.dump(topology_data, f, indent=2, default=str)
        logger.info(f"Inferred topology saved to {output_file}")

        print(f"\n{'='*50}")
        print("INFERENCE SUMMARY")
        print(f"{'='*50}")
        print(f"Input: {args.input}")
        print(f"Output: {output_file}")
        print(f"Connections inferred: {len(connections)}")

    except IOError as e:
        logger.error(f"Failed to write output file: {e}")
        sys.exit(1)


def visualize_command(args):
    """Handle visualize command"""
    visualizer = NetworkVisualizer()

    if not visualizer.load_topology(args.input):
        return

    visualizer.build_network_graph()

    # Print statistics
    stats = visualizer.get_network_statistics()
    print(f"\n{'='*50}")
    print("NETWORK STATISTICS")
    print(f"{'='*50}")
    print(f"Nodes: {stats['nodes']}")
    print(f"Connections: {stats['edges']}")
    print(f"Average Degree: {stats['avg_degree']:.2f}")
    print(f"Network Density: {stats['density']:.3f}")

    if args.output:
        visualizer.save_visualization(args.output, dynamic=args.dynamic)

    if args.show or not args.output:
        if args.dynamic:
            import webbrowser
            import os
            output = args.output or 'temp_visualization.html'
            if not args.output:
                visualizer.create_dynamic_visualization(output)
            webbrowser.open('file://' + os.path.abspath(output))
        else:
            visualizer.display_visualization()


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='Meshtastic Network Topology Mapper - Map and visualize mesh network topology via Bluetooth',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quick Start:
  1. Scan for devices:     %(prog)s scan
  2. Pair device in macOS Bluetooth settings (PIN: 123456)
  3. Collect topology:      %(prog)s collect -a <ADDRESS> -d 300
  4. Infer connections:     %(prog)s infer -i <FILE>
  5. Visualize network:     %(prog)s visualize -i <FILE_topo_v2.json> --show --dynamic

Common Examples:
  # Scan for Meshtastic devices
  %(prog)s scan
  
  # Collect for 5 minutes (recommended)
  %(prog)s collect -a "AA:BB:CC:DD:EE:FF" -d 300
  
  # Collect for 10 minutes with custom output
  %(prog)s collect -a "🫘_e885" -d 600 -o my_network.json
  
  # Aggregate multiple collection files
  %(prog)s aggregate -d data/

  # Infer connections from collected topology
  %(prog)s infer -i data/network_topology.json

  # Visualize network in browser (dynamic mode)
  %(prog)s visualize -i data/network_topology_topo_v2.json --show --dynamic

  # Save visualization as HTML
  %(prog)s visualize -i data/network_topology_topo_v2.json -o network.html --dynamic

Tips:
  - Longer collection times (300+ seconds) capture more neighbor info
  - Neighbor info packets are sent periodically (15min - 4hr intervals)
  - Enable Neighbor Info module on nodes for connection data
  - On macOS, pair device first via System Settings > Bluetooth
  - Run 'infer' command after 'collect' to detect co-located nodes and multi-hop paths
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='Commands')
    
    # Scan command
    scan_parser = subparsers.add_parser('scan', 
                                       help='Scan for Meshtastic devices via Bluetooth',
                                       formatter_class=argparse.RawDescriptionHelpFormatter,
                                       epilog="""
This command scans for available Meshtastic devices over Bluetooth.
The scan takes approximately 10 seconds and displays all found devices
with their names, addresses, and signal strength (RSSI).

Use the address from this scan in the 'collect' command.
                                       """)
    
    # Collect command
    collect_parser = subparsers.add_parser('collect', 
                                          help='Collect topology from a device',
                                          formatter_class=argparse.RawDescriptionHelpFormatter,
                                          epilog="""
Examples:
  # Collect for default 2 minutes
  %(prog)s -a "AA:BB:CC:DD:EE:FF"
  
  # Collect for 5 minutes
  %(prog)s -a "AA:BB:CC:DD:EE:FF" -d 300
  
  # Collect for 10 minutes with custom output
  %(prog)s -a "AA:BB:CC:DD:EE:FF" -d 600 -o my_network.json
  
  # Use device name instead of address
  %(prog)s -a "🫘_e885" -d 300
  
Note: Neighbor info packets are sent periodically by nodes.
      Longer collection times (300+ seconds) increase chances
      of capturing complete network topology.
                                          """)
    collect_parser.add_argument('--address', '-a', required=True,
                               help='Bluetooth address or device name (e.g., "AA:BB:CC:DD:EE:FF" or "🫘_e885")')
    collect_parser.add_argument('--duration', '-d', type=int, default=120, metavar='SECONDS',
                               help='Collection duration in seconds (default: 120, recommended: 300+)')
    collect_parser.add_argument('--output', '-o', metavar='FILE',
                               help='Output JSON filename (default: data/network_topology_TIMESTAMP.json)')
    collect_parser.add_argument('--pin', '-p', default='123456', metavar='PIN',
                               help='Bluetooth pairing PIN (default: 123456)')
    
    # Aggregate command
    aggregate_parser = subparsers.add_parser('aggregate', 
                                            help='Aggregate topology data from multiple sources',
                                            formatter_class=argparse.RawDescriptionHelpFormatter,
                                            epilog="""
Examples:
  # Aggregate all JSON files in data directory
  %(prog)s -d data/
  
  # Collect from multiple nodes using config file
  %(prog)s -c nodes.yaml
  
  # Aggregate with custom output
  %(prog)s -d data/ -o combined_topology.json
                                            """)
    aggregate_parser.add_argument('--directory', '-d', default='data', metavar='DIR',
                                 help='Directory containing topology JSON files (default: data/)')
    aggregate_parser.add_argument('--config', '-c', metavar='FILE',
                                 help='YAML config file for collecting from multiple nodes')
    aggregate_parser.add_argument('--output', '-o', metavar='FILE',
                                 help='Output filename for aggregated data')

    # Infer command
    infer_parser = subparsers.add_parser('infer',
                                        help='Infer mesh connections from collected topology data',
                                        formatter_class=argparse.RawDescriptionHelpFormatter,
                                        epilog="""
This command analyzes collected topology data and infers mesh connections using:
  - GPS co-location detection (nodes at same physical location)
  - Bluetooth pair detection (collection source ↔ collection node)
  - Hop-by-hop path inference with routing evidence validation
  - SNR-based connection quality assessment

The inferred connections include:
  - Co-located nodes (same GPS coordinates, within ~11m)
  - Direct mesh connections (0 → 1 hop)
  - Multi-hop paths (N → N+1) with confidence levels
  - Routing validation using observed packet flows

Output file will have "_topo_v2" suffix added before .json extension.

Examples:
  # Infer connections with default output
  %(prog)s -i data/network_topology.json
  # Output: data/network_topology_topo_v2.json

  # Infer with custom output filename
  %(prog)s -i data/network_topology.json -o data/inferred.json

Workflow:
  1. meshnetmap collect -a <ADDRESS> -d 300
  2. meshnetmap infer -i data/network_topology_TIMESTAMP.json
  3. meshnetmap visualize -i data/network_topology_TIMESTAMP_topo_v2.json --show --dynamic
                                        """)
    infer_parser.add_argument('--input', '-i', required=True, metavar='FILE',
                             help='Input topology JSON file (from collect command)')
    infer_parser.add_argument('--output', '-o', metavar='FILE',
                             help='Output filename for inferred topology (default: <input>_topo_v2.json)')

    # Visualize command
    viz_parser = subparsers.add_parser('visualize',
                                      help='Visualize network topology as interactive graph',
                                      formatter_class=argparse.RawDescriptionHelpFormatter,
                                      epilog="""
Examples:
  # Display visualization in browser
  %(prog)s -i data/network_topology.json --show

  # Save visualization to HTML file
  %(prog)s -i data/network_topology.json -o network.html

  # Create dynamic D3.js visualization with physics
  %(prog)s -i data/network_topology.json -o network.html --dynamic

  # Both display and save
  %(prog)s -i data/network_topology.json -o network.html --show --dynamic

The visualization shows:
  - Nodes colored by hop distance
  - Connections colored by signal quality (SNR)
  - Interactive hover information
  - Network statistics

Dynamic mode (--dynamic) features:
  - Physics-based force-directed layout (avoids overlaps)
  - Click nodes to center and highlight neighbors
  - Click edges to see connection details
  - Adjustable physics parameters
  - Drag nodes to reposition
                                      """)
    viz_parser.add_argument('--input', '-i', required=True, metavar='FILE',
                           help='Input topology JSON file')
    viz_parser.add_argument('--output', '-o', metavar='FILE',
                           help='Output HTML file for saving visualization')
    viz_parser.add_argument('--show', action='store_true',
                           help='Open visualization in web browser')
    viz_parser.add_argument('--dynamic', action='store_true',
                           help='Create dynamic D3.js force-directed visualization')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute command
    if args.command == 'scan':
        scan_command(args)
    elif args.command == 'collect':
        collect_command(args)
    elif args.command == 'aggregate':
        aggregate_command(args)
    elif args.command == 'infer':
        infer_command(args)
    elif args.command == 'visualize':
        visualize_command(args)


if __name__ == "__main__":
    main()