#!/usr/bin/env python3
"""
Aggregator module for combining topology data from multiple collection sessions
"""

import json
import logging
from typing import Dict, Any, List
from pathlib import Path
from datetime import datetime
import yaml

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class TopologyAggregator:
    """Aggregates network topology data from multiple sources"""
    
    def __init__(self):
        self.aggregated_data: Dict[str, Any] = {
            'nodes': {},
            'connections': {},
            'routing_paths': [],
            'metadata': {
                'aggregation_time': None,
                'sources': []
            }
        }
    
    def load_topology_file(self, filepath: str) -> Dict[str, Any]:
        """
        Load topology data from a JSON file
        
        Args:
            filepath: Path to the JSON file
            
        Returns:
            Topology data dictionary
        """
        try:
            with open(filepath, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {str(e)}")
            return None
    
    def add_topology_data(self, topology: Dict[str, Any], source: str = None):
        """
        Add topology data to the aggregation
        
        Args:
            topology: Topology data dictionary
            source: Optional source identifier
        """
        if not topology:
            return
        
        # Add nodes
        for node_id, node_info in topology.get('nodes', {}).items():
            if node_id not in self.aggregated_data['nodes']:
                self.aggregated_data['nodes'][node_id] = node_info
            else:
                # Merge node information, preferring newer data
                existing = self.aggregated_data['nodes'][node_id]
                if node_info.get('lastHeard', 0) > existing.get('lastHeard', 0):
                    self.aggregated_data['nodes'][node_id].update(node_info)
        
        # Add connections
        for connection in topology.get('connections', []):
            # Create unique connection key
            conn_key = f"{connection['from']}->{connection['to']}"

            if conn_key not in self.aggregated_data['connections']:
                self.aggregated_data['connections'][conn_key] = connection
            else:
                # Update connection based on type and quality
                existing = self.aggregated_data['connections'][conn_key]

                # Prefer confirmed connections over implied
                if connection.get('type') == 'confirmed' and existing.get('type') == 'implied':
                    self.aggregated_data['connections'][conn_key] = connection
                elif existing.get('type') == connection.get('type'):
                    # Same type - prefer newer or better SNR
                    if (connection.get('timestamp', '') > existing.get('timestamp', '') or
                        connection.get('snr', 0) > existing.get('snr', 0)):
                        self.aggregated_data['connections'][conn_key] = connection
                # For implied connections, merge evidence counts
                elif connection.get('type') == 'implied' and existing.get('type') == 'implied':
                    existing['evidence_count'] = existing.get('evidence_count', 1) + connection.get('evidence_count', 1)

        # Add routing paths
        for path in topology.get('routing_paths', []):
            self.aggregated_data['routing_paths'].append(path)
        
        # Add source to metadata
        if source:
            self.aggregated_data['metadata']['sources'].append({
                'source': source,
                'timestamp': topology.get('metadata', {}).get('collection_time'),
                'device': topology.get('metadata', {}).get('collection_device')
            })
        
        logger.info(f"Added topology data from {source or 'unknown source'}")
    
    def aggregate_from_directory(self, directory: str = "data"):
        """
        Aggregate all topology files from a directory
        
        Args:
            directory: Directory containing topology JSON files
        """
        data_path = Path(directory)
        if not data_path.exists():
            logger.error(f"Directory {directory} does not exist")
            return
        
        json_files = list(data_path.glob("network_topology_*.json"))
        logger.info(f"Found {len(json_files)} topology files to aggregate")
        
        for json_file in json_files:
            topology = self.load_topology_file(str(json_file))
            if topology:
                self.add_topology_data(topology, str(json_file))
    
    def aggregate_from_config(self, config_file: str):
        """
        Aggregate topology data from multiple nodes specified in config
        
        Args:
            config_file: YAML configuration file with node addresses
        """
        try:
            with open(config_file, 'r') as f:
                config = yaml.safe_load(f)
            
            nodes_config = config.get('nodes', [])
            
            from .collect import NetworkTopologyCollector
            
            for node_config in nodes_config:
                address = node_config.get('address')
                name = node_config.get('name', address)
                duration = node_config.get('duration', 30)
                
                logger.info(f"Collecting from {name} ({address})")
                
                collector = NetworkTopologyCollector()
                if collector.connect(address):
                    topology = collector.collect_topology(duration)
                    self.add_topology_data(topology, name)
                    collector.disconnect()
                else:
                    logger.warning(f"Failed to connect to {name}")
                    
        except Exception as e:
            logger.error(f"Failed to process config file: {str(e)}")
    
    def get_aggregated_topology(self) -> Dict[str, Any]:
        """
        Get the aggregated topology data
        
        Returns:
            Aggregated topology dictionary
        """
        # Convert connections dict back to list
        self.aggregated_data['connections'] = list(self.aggregated_data['connections'].values())
        self.aggregated_data['metadata']['aggregation_time'] = datetime.now().isoformat()
        
        # Calculate statistics
        self.aggregated_data['statistics'] = {
            'total_nodes': len(self.aggregated_data['nodes']),
            'total_connections': len(self.aggregated_data['connections']),
            'sources': len(self.aggregated_data['metadata']['sources'])
        }
        
        return self.aggregated_data
    
    def save_aggregated_data(self, filename: str = None):
        """
        Save aggregated topology data to file
        
        Args:
            filename: Output filename
        """
        if not filename:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"data/aggregated_topology_{timestamp}.json"
        
        Path("data").mkdir(exist_ok=True)
        
        aggregated = self.get_aggregated_topology()
        
        with open(filename, 'w') as f:
            json.dump(aggregated, f, indent=2, default=str)
        
        logger.info(f"Aggregated topology saved to {filename}")
        logger.info(f"Statistics: {aggregated['statistics']}")


def main():
    """Main entry point for aggregator"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Aggregate Meshtastic topology data')
    parser.add_argument('--directory', '-d', default='data',
                       help='Directory containing topology files')
    parser.add_argument('--config', '-c', help='YAML config file for multi-node collection')
    parser.add_argument('--output', '-o', help='Output filename for aggregated data')
    
    args = parser.parse_args()
    
    aggregator = TopologyAggregator()
    
    if args.config:
        aggregator.aggregate_from_config(args.config)
    else:
        aggregator.aggregate_from_directory(args.directory)
    
    aggregator.save_aggregated_data(args.output)


if __name__ == "__main__":
    main()