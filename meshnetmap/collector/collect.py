#!/usr/bin/env python3
"""
Main collection module for gathering network topology data from Meshtastic nodes
"""

import sys
import json
import time
import logging
import argparse
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

try:
    import meshtastic
    import meshtastic.ble_interface
    from pubsub import pub
except ImportError:
    print("Error: Required libraries not installed. Run: pip install -r requirements.txt")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NetworkTopologyCollector:
    """Collects network topology data from Meshtastic nodes via Bluetooth"""
    
    def __init__(self):
        self.interface: Optional[meshtastic.ble_interface.BLEInterface] = None
        self.topology_data: Dict[str, Any] = {
            'nodes': {},
            'connections': [],
            'routing_paths': [],  # Store observed routing paths
            'metadata': {
                'collection_time': None,
                'collection_device': None
            }
        }
        self.received_packets = []
        
    def connect(self, address: str, pin: Optional[str] = None) -> bool:
        """
        Connect to a Meshtastic device via Bluetooth
        
        Args:
            address: Bluetooth address or name of the device
            pin: Optional PIN for pairing (default is usually 123456)
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            logger.info(f"Connecting to device: {address}")
            
            # Set default PIN if not provided
            if not pin:
                pin = "123456"  # Default Meshtastic PIN
                logger.info(f"Using default PIN: {pin}")
            
            self.interface = meshtastic.ble_interface.BLEInterface(address)
            
            # Subscribe to packet reception
            pub.subscribe(self.on_receive, "meshtastic.receive")
            pub.subscribe(self.on_node_updated, "meshtastic.node.updated")
            pub.subscribe(self.on_connection, "meshtastic.connection.established")
            
            # Wait for initial nodeDB sync
            logger.info("Waiting for initial node database sync...")
            time.sleep(5)
            
            logger.info("Connection established successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect: {str(e)}")
            if "Encryption is insufficient" in str(e):
                logger.error("")
                logger.error("PAIRING REQUIRED:")
                logger.error("The device requires pairing for encrypted communication.")
                logger.error("")
                logger.error("Alternative: Use the --pin flag to specify a different PIN")
            return False
    
    def on_receive(self, packet, interface):
        """Handle incoming packets"""
        self.received_packets.append(packet)

        # Log packet type for debugging
        packet_type = "Unknown"
        if 'decoded' in packet:
            packet_type = packet['decoded'].get('portnum', 'Unknown')

        from_node = packet.get('fromId', packet.get('from', 'Unknown'))
        logger.debug(f"Received {packet_type} packet from {from_node}")

        # Extract routing information from all packets
        self.process_routing_info(packet)

        # Process different packet types
        if 'decoded' in packet and 'portnum' in packet['decoded']:
            portnum = packet['decoded']['portnum']

            if portnum == 'NEIGHBORINFO_APP':
                self.process_neighbor_info(packet)
            elif portnum == 'NODEINFO_APP':
                logger.info(f"Received NodeInfo from {from_node}")
            elif portnum == 'POSITION_APP':
                logger.debug(f"Received Position update from {from_node}")
    
    def process_routing_info(self, packet):
        """Extract routing path information from any packet type"""
        try:
            from_node = packet.get('fromId', packet.get('from'))
            to_node = packet.get('toId', packet.get('to'))

            # Check for routing information in packet
            hop_start = packet.get('hopStart', 0)
            hop_limit = packet.get('hopLimit', 0)
            hops_away = packet.get('hopsAway', 0)
            rx_snr = packet.get('rxSnr', 0)
            rx_rssi = packet.get('rxRssi', 0)

            # Debug: log first few packets to understand structure
            if len(self.received_packets) <= 3:
                logger.debug(f"Packet structure: from={from_node}, to={to_node}, hopsAway={hops_away}, hopStart={hop_start}, hopLimit={hop_limit}")
                logger.debug(f"Full packet keys: {list(packet.keys())}")

            # Build routing path
            path = []

            # The 'via' field in rxSnr indicates which node we received it from
            # This is different from 'from' which is the originator
            via_node = None

            # Only process packets with valid from_node
            if not from_node:
                return

            packet_type = packet.get('decoded', {}).get('portnum', 'Unknown')

            # Record routing path for any packet we receive
            if hops_away >= 0:
                routing_path = {
                    'from': from_node,
                    'to': to_node,
                    'hops_away': hops_away,
                    'hop_start': hop_start,
                    'hop_limit': hop_limit,
                    'rx_snr': rx_snr,
                    'rx_rssi': rx_rssi,
                    'packet_type': packet_type,
                    'timestamp': datetime.now().isoformat()
                }
                self.topology_data['routing_paths'].append(routing_path)

            # Create connections based on node database hopsAway
            # We'll do this in a separate method after collection

        except Exception as e:
            logger.debug(f"Error extracting routing info: {str(e)}")

    def on_node_updated(self, node):
        """Handle node updates"""
        logger.info(f"Node updated: {node}")

    def on_connection(self, interface, topic=pub.AUTO_TOPIC):
        """Handle connection establishment"""
        logger.info("Connection established, nodeDB sync complete")
    
    def process_neighbor_info(self, packet):
        """Process neighbor info packets for topology data"""
        try:
            from_node = packet.get('fromId', packet.get('from'))
            logger.info(f"Processing NeighborInfo packet from {from_node}")
            
            # Check different possible locations for neighbor data
            neighbor_data = None
            
            # Try decoded.neighborinfo first
            if 'decoded' in packet and 'neighborinfo' in packet['decoded']:
                neighbor_data = packet['decoded']['neighborinfo']
            # Try decoded.neighbors
            elif 'decoded' in packet and 'neighbors' in packet['decoded']:
                neighbor_data = {'neighbors': packet['decoded']['neighbors']}
            # Try direct neighbors field
            elif 'neighbors' in packet:
                neighbor_data = {'neighbors': packet['neighbors']}
                
            if neighbor_data:
                # Store neighbor relationships
                if 'neighbors' in neighbor_data and neighbor_data['neighbors']:
                    neighbor_count = len(neighbor_data['neighbors'])
                    logger.info(f"Found {neighbor_count} neighbors for {from_node}")
                    
                    for neighbor in neighbor_data['neighbors']:
                        to_node = neighbor.get('nodeId', neighbor.get('node_id', neighbor.get('id')))
                        snr = neighbor.get('snr', neighbor.get('last_rx_snr', 0))
                        
                        if to_node:
                            connection = {
                                'from': from_node,
                                'to': to_node,
                                'snr': snr,
                                'type': 'confirmed',  # From NEIGHBORINFO_APP
                                'confidence': 'high',
                                'timestamp': datetime.now().isoformat()
                            }
                            self.topology_data['connections'].append(connection)
                            logger.debug(f"Added confirmed connection: {from_node} -> {to_node} (SNR: {snr})")
                else:
                    logger.warning(f"NeighborInfo packet from {from_node} has no neighbors list")
            else:
                logger.warning(f"Could not find neighbor data in packet from {from_node}")
                logger.debug(f"Packet structure: {packet}")
                        
        except Exception as e:
            logger.error(f"Error processing neighbor info: {str(e)}")
            logger.debug(f"Problematic packet: {packet}")

    def infer_connections_from_hops(self):
        """Infer mesh connections based on hopsAway data from node database"""
        logger.info("Inferring mesh topology from hop distance data...")

        # Organize nodes by hop distance
        nodes_by_hop = {}
        for node_id, node_info in self.topology_data['nodes'].items():
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
            logger.warning("No nodes with valid hop distances found")
            return

        logger.info(f"Hop distribution: {[(h, len(nodes_by_hop[h])) for h in sorted(nodes_by_hop.keys())]}")

        # Create direct connections (0 -> 1 hop)
        if 0 in nodes_by_hop and 1 in nodes_by_hop:
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
                    self.topology_data['connections'].append(connection)
                    logger.debug(f"Direct: {zero_hop['id'][:8]} -> {one_hop['id'][:8]} (SNR: {one_hop['snr']})")

        # Infer intermediate hop connections (N -> N+1)
        # Nodes at hop N+1 must route through at least one node at hop N
        max_hop = max(nodes_by_hop.keys())
        for hop_level in range(1, max_hop):
            if hop_level not in nodes_by_hop or hop_level + 1 not in nodes_by_hop:
                continue

            current_hop_nodes = nodes_by_hop[hop_level]
            next_hop_nodes = nodes_by_hop[hop_level + 1]

            logger.info(f"Inferring {len(next_hop_nodes)} connections between hop {hop_level} and {hop_level + 1}")

            # For each node at hop N+1, infer which node at hop N it likely routes through
            for next_node in next_hop_nodes:
                # Strategy: prefer nodes with better SNR as likely intermediate routers
                # Sort current hop nodes by SNR (better signal = more likely to be router)
                potential_routers = sorted(current_hop_nodes, key=lambda x: x['snr'], reverse=True)

                # Create connections to top candidates
                # Use all nodes with positive SNR, or top 3 if none have positive SNR
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
                        'hops_away': 1,  # Connection is 1 hop
                        'total_hops_from_origin': hop_level + 1,
                        'evidence': f'hop_inference_via_{router["id"][:8]}',
                        'router_snr': router['snr'],
                        'timestamp': datetime.now().isoformat()
                    }
                    self.topology_data['connections'].append(connection)

        logger.info(f"Inferred {len(self.topology_data['connections'])} total connections from hop topology")

    def collect_topology(self, duration: int = 120) -> Dict[str, Any]:
        """
        Collect network topology data for specified duration
        
        Args:
            duration: Collection duration in seconds
            
        Returns:
            Dictionary containing topology data
        """
        if not self.interface:
            logger.error("Not connected to a device")
            return self.topology_data
        
        logger.info(f"Collecting topology data for {duration} seconds...")
        logger.info("Note: Neighbor info packets are sent periodically by nodes.")
        logger.info("Longer collection duration increases chances of receiving them.")
        
        # Get initial node database
        initial_nodes = 0
        if hasattr(self.interface, 'nodes') and self.interface.nodes:
            for node_id, node_info in self.interface.nodes.items():
                self.topology_data['nodes'][node_id] = {
                    'id': node_id,
                    'num': node_info.get('num'),
                    'user': node_info.get('user', {}),
                    'position': node_info.get('position', {}),
                    'lastHeard': node_info.get('lastHeard'),
                    'snr': node_info.get('snr'),
                    'hopsAway': node_info.get('hopsAway', -1)
                }
                initial_nodes += 1
        
        logger.info(f"Initial nodes in database: {initial_nodes}")
        
        # Try to request neighbor info (may not be supported by all nodes)
        logger.info("Requesting neighbor info from mesh...")
        try:
            if hasattr(self.interface, 'sendData'):
                # Send broadcast request for neighbor info
                self.interface.sendData(
                    b'',
                    portNum=meshtastic.portnums_pb2.PortNum.NEIGHBORINFO_APP,
                    wantAck=False,
                    wantResponse=True,
                    destinationId='^all'  # Broadcast to all nodes
                )
                logger.info("Neighbor info request sent to all nodes")
        except Exception as e:
            logger.warning(f"Could not request neighbor info: {str(e)}")
            logger.info("Will passively listen for neighbor info packets...")
        
        # Collect data for specified duration with progress updates
        start_time = time.time()
        last_update = start_time
        update_interval = 10  # Show progress every 10 seconds
        
        while time.time() - start_time < duration:
            time.sleep(1)
            elapsed = int(time.time() - start_time)
            remaining = duration - elapsed
            
            # Show progress every 10 seconds
            if time.time() - last_update >= update_interval:
                logger.info(f"Collection progress: {elapsed}/{duration}s elapsed, {remaining}s remaining")
                logger.info(f"Current stats: {len(self.topology_data['nodes'])} nodes, "
                          f"{len(self.topology_data['connections'])} connections")
                last_update = time.time()
            
            # Update nodes from current nodeDB
            if hasattr(self.interface, 'nodes') and self.interface.nodes:
                for node_id, node_info in self.interface.nodes.items():
                    if node_id not in self.topology_data['nodes']:
                        self.topology_data['nodes'][node_id] = {
                            'id': node_id,
                            'num': node_info.get('num'),
                            'user': node_info.get('user', {}),
                            'position': node_info.get('position', {}),
                            'lastHeard': node_info.get('lastHeard'),
                            'snr': node_info.get('snr'),
                            'hopsAway': node_info.get('hopsAway', -1)
                        }
                        logger.info(f"New node discovered: {node_id}")
        
        # Update metadata
        self.topology_data['metadata']['collection_time'] = datetime.now().isoformat()
        if self.interface and hasattr(self.interface, 'myInfo'):
            self.topology_data['metadata']['collection_device'] = str(self.interface.myInfo)
        
        # Log packet statistics
        logger.info(f"Total packets received: {len(self.received_packets)}")
        packet_types = {}
        for packet in self.received_packets:
            if 'decoded' in packet and 'portnum' in packet['decoded']:
                ptype = packet['decoded']['portnum']
                packet_types[ptype] = packet_types.get(ptype, 0) + 1
        
        if packet_types:
            logger.info("Packet types received:")
            for ptype, count in packet_types.items():
                logger.info(f"  - {ptype}: {count}")
        
        logger.info(f"Collection complete. Found {len(self.topology_data['nodes'])} nodes")
        logger.info(f"Recorded {len(self.topology_data['connections'])} connections from neighbor info")

        # If we didn't get neighbor info, infer connections from hop data
        if len(self.topology_data['connections']) == 0:
            logger.warning("No neighbor connections were captured via NEIGHBORINFO_APP packets.")
            logger.info("Attempting to infer connections from hop distance data...")
            self.infer_connections_from_hops()

        logger.info(f"Total connections: {len(self.topology_data['connections'])}")

        return self.topology_data
    
    def save_topology(self, filename: str = None):
        """
        Save topology data to JSON file
        
        Args:
            filename: Output filename (defaults to timestamp-based name)
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/network_topology_{timestamp}.json"
        
        # Ensure data directory exists
        Path("data").mkdir(exist_ok=True)
        
        with open(filename, 'w') as f:
            json.dump(self.topology_data, f, indent=2, default=str)
        
        logger.info(f"Topology data saved to {filename}")
    
    def disconnect(self):
        """Disconnect from the Meshtastic device"""
        if self.interface:
            try:
                pub.unsubscribe(self.on_receive, "meshtastic.receive")
                pub.unsubscribe(self.on_node_updated, "meshtastic.node.updated")
                pub.unsubscribe(self.on_connection, "meshtastic.connection.established")
                self.interface.close()
                logger.info("Disconnected from device")
            except Exception as e:
                logger.error(f"Error during disconnect: {str(e)}")


def main():
    """Main entry point for collector"""
    parser = argparse.ArgumentParser(description='Collect Meshtastic network topology')
    parser.add_argument('--address', '-a', required=True,
                       help='Bluetooth address or name of Meshtastic device')
    parser.add_argument('--duration', '-d', type=int, default=30,
                       help='Collection duration in seconds (default: 30)')
    parser.add_argument('--output', '-o', help='Output filename for topology data')
    parser.add_argument('--pin', '-p', help='Bluetooth PIN for pairing')

    args = parser.parse_args()

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

            if topology['nodes']:
                print("\nNodes:")
                for node_id, node_info in topology['nodes'].items():
                    user = node_info.get('user', {})
                    name = user.get('longName', user.get('shortName', 'Unknown'))
                    print(f"  - {name} ({node_id})")
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


if __name__ == "__main__":
    main()