#!/usr/bin/env python3
"""
Visualization module for displaying Meshtastic network topology
"""

import json
import logging
import argparse
from typing import Dict, Any, List, Tuple
from pathlib import Path

import networkx as nx
import plotly.graph_objects as go
from plotly.subplots import make_subplots

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class NetworkVisualizer:
    """Visualizes Meshtastic network topology"""
    
    def __init__(self):
        self.graph = nx.Graph()
        self.topology_data = None
    
    def load_topology(self, filepath: str) -> bool:
        """
        Load topology data from JSON file
        
        Args:
            filepath: Path to topology JSON file
            
        Returns:
            True if successful, False otherwise
        """
        try:
            with open(filepath, 'r') as f:
                self.topology_data = json.load(f)
            logger.info(f"Loaded topology data from {filepath}")
            return True
        except Exception as e:
            logger.error(f"Failed to load topology: {str(e)}")
            return False
    
    def build_network_graph(self):
        """Build NetworkX graph from topology data"""
        if not self.topology_data:
            logger.error("No topology data loaded")
            return
        
        # Add nodes
        for node_id, node_info in self.topology_data.get('nodes', {}).items():
            user = node_info.get('user', {})
            self.graph.add_node(
                node_id,
                label=user.get('longName', user.get('shortName', node_id[:8])),
                num=node_info.get('num'),
                lastHeard=node_info.get('lastHeard'),
                hopsAway=node_info.get('hopsAway', -1),
                position=node_info.get('position', {})
            )
        
        # Add edges (connections)
        for connection in self.topology_data.get('connections', []):
            from_node = connection.get('from')
            to_node = connection.get('to')

            if from_node and to_node:
                # Check if both nodes exist in graph
                if from_node in self.graph.nodes and to_node in self.graph.nodes:
                    self.graph.add_edge(
                        from_node,
                        to_node,
                        snr=connection.get('snr', 0),
                        type=connection.get('type', 'unknown'),
                        confidence=connection.get('confidence', 'unknown'),
                        evidence_count=connection.get('evidence_count', 1),
                        timestamp=connection.get('timestamp')
                    )
        
        logger.info(f"Built graph with {self.graph.number_of_nodes()} nodes and {self.graph.number_of_edges()} edges")
    
    def create_interactive_plot(self) -> go.Figure:
        """
        Create an interactive Plotly network visualization
        
        Returns:
            Plotly figure object
        """
        if self.graph.number_of_nodes() == 0:
            logger.warning("Graph is empty")
            return None
        
        # Use spring layout for positioning
        pos = nx.spring_layout(self.graph, k=2, iterations=50)
        
        # Create edge traces - separate confirmed and implied connections
        edge_traces = []
        for edge in self.graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            snr = edge[2].get('snr', 0)
            conn_type = edge[2].get('type', 'unknown')
            confidence = edge[2].get('confidence', 'unknown')
            evidence_count = edge[2].get('evidence_count', 1)

            # Determine line style based on connection type
            if conn_type == 'confirmed':
                dash_style = 'solid'
                opacity = 1.0
            elif conn_type == 'inferred_direct':
                dash_style = 'solid'
                opacity = 0.9
            elif conn_type == 'inferred_hop':
                # Hop-to-hop inferred connections
                if confidence == 'high':
                    dash_style = 'solid'
                    opacity = 0.8
                elif confidence == 'medium':
                    dash_style = 'dash'
                    opacity = 0.6
                else:
                    dash_style = 'dot'
                    opacity = 0.4
            elif conn_type == 'inferred_multihop':
                dash_style = 'dash'
                opacity = 0.5
            elif conn_type == 'implied':
                dash_style = 'dash'
                opacity = 0.6 if confidence == 'medium' else 0.8
            else:
                dash_style = 'dot'
                opacity = 0.5

            # Color code by SNR (signal quality)
            if snr > 0:
                color = 'green'
                width = 3
            elif snr > -5:
                color = 'yellow'
                width = 2
            elif snr > -10:
                color = 'orange'
                width = 1.5
            else:
                color = 'red'
                width = 1

            # Build hover text
            hover_parts = [f"SNR: {snr} dB"]
            if conn_type == 'confirmed':
                hover_parts.append("Type: Direct neighbor (confirmed)")
            elif conn_type == 'inferred_direct':
                hover_parts.append("Type: Direct link (1 hop)")
                hover_parts.append("Inferred from hop distance")
            elif conn_type == 'inferred_hop':
                total_hops = edge[2].get('total_hops_from_origin', '?')
                router_snr = edge[2].get('router_snr', '?')
                hover_parts.append(f"Type: Inferred routing hop (confidence: {confidence})")
                hover_parts.append(f"Total distance from origin: {total_hops} hops")
                hover_parts.append(f"Router signal: {router_snr} dB")
            elif conn_type == 'inferred_multihop':
                hops_away = edge[2].get('hops_away', 0)
                hover_parts.append(f"Type: Multi-hop path ({hops_away} hops)")
                hover_parts.append("Inferred from hop distance")
            elif conn_type == 'implied':
                hover_parts.append(f"Type: Implied from routing (confidence: {confidence})")
                hover_parts.append(f"Evidence: {evidence_count} packet(s)")
            hover_text = "<br>".join(hover_parts)

            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=width, color=color, dash=dash_style),
                opacity=opacity,
                hoverinfo='text',
                text=hover_text,
                showlegend=False
            )
            edge_traces.append(edge_trace)
        
        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_hover = []
        node_colors = []
        
        for node in self.graph.nodes(data=True):
            x, y = pos[node[0]]
            node_x.append(x)
            node_y.append(y)
            
            # Node label
            label = node[1].get('label', node[0][:8])
            node_text.append(label)
            
            # Hover information
            hover_info = [
                f"<b>{label}</b>",
                f"ID: {node[0]}",
                f"Hops: {node[1].get('hopsAway', 'Unknown')}"
            ]
            
            if node[1].get('position'):
                lat = node[1]['position'].get('latitude')
                lon = node[1]['position'].get('longitude')
                if lat and lon:
                    hover_info.append(f"Position: {lat:.4f}, {lon:.4f}")
            
            node_hover.append("<br>".join(hover_info))
            
            # Color by hops away
            hops = node[1].get('hopsAway', -1)
            if hops == 0:
                node_colors.append('blue')  # Direct node
            elif hops == 1:
                node_colors.append('green')
            elif hops == 2:
                node_colors.append('yellow')
            elif hops == 3:
                node_colors.append('orange')
            else:
                node_colors.append('red')
        
        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(
                size=20,
                color=node_colors,
                line=dict(width=2, color='black')
            ),
            text=node_text,
            textposition="top center",
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=node_hover,
            showlegend=False
        )
        
        # Create figure
        fig = go.Figure(data=edge_traces + [node_trace])
        
        # Update layout
        fig.update_layout(
            title={
                'text': 'Meshtastic Network Topology',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=800
        )
        
        # Add legend for node colors (hops)
        legend_data = [
            ('Direct Connection', 'blue'),
            ('1 Hop', 'green'),
            ('2 Hops', 'yellow'),
            ('3 Hops', 'orange'),
            ('4+ Hops', 'red')
        ]

        for i, (label, color) in enumerate(legend_data):
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='markers',
                marker=dict(size=10, color=color),
                showlegend=True,
                name=label,
                legendgroup='nodes',
                legendgrouptitle_text='Node Distance'
            ))

        # Add legend for connection types
        connection_legend = [
            ('Confirmed (neighbor)', 'gray', 'solid', 1.0),
            ('Direct (1 hop)', 'gray', 'solid', 0.6),
            ('Multi-hop (2+)', 'gray', 'dash', 0.5)
        ]

        for label, color, dash, opacity in connection_legend:
            fig.add_trace(go.Scatter(
                x=[None], y=[None],
                mode='lines',
                line=dict(color=color, width=2, dash=dash),
                opacity=opacity,
                showlegend=True,
                name=label,
                legendgroup='connections',
                legendgrouptitle_text='Connection Type'
            ))
        
        # Add statistics annotation
        stats = self.get_network_statistics()
        stats_text = (
            f"Nodes: {stats['nodes']}<br>"
            f"Connections: {stats['edges']}<br>"
            f"Avg Degree: {stats['avg_degree']:.2f}<br>"
            f"Density: {stats['density']:.3f}"
        )
        
        fig.add_annotation(
            x=0.02,
            y=0.98,
            xref='paper',
            yref='paper',
            text=stats_text,
            showarrow=False,
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='black',
            borderwidth=1,
            font=dict(size=12),
            align='left',
            xanchor='left',
            yanchor='top'
        )
        
        return fig
    
    def create_routing_paths_visualization(self) -> go.Figure:
        """Create a visualization showing routing paths through the network"""
        if not self.topology_data:
            logger.error("No topology data loaded")
            return None

        routing_paths = self.topology_data.get('routing_paths', [])
        if not routing_paths:
            logger.warning("No routing paths found in topology data")
            return None

        # Get positions from main graph
        pos = nx.spring_layout(self.graph, k=2, iterations=50)

        # Create base network visualization
        edge_traces = []
        for edge in self.graph.edges(data=True):
            x0, y0 = pos[edge[0]]
            x1, y1 = pos[edge[1]]

            edge_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines',
                line=dict(width=1, color='lightgray'),
                hoverinfo='none',
                showlegend=False
            )
            edge_traces.append(edge_trace)

        # Add routing path overlays
        path_colors = ['red', 'blue', 'purple', 'orange', 'pink', 'brown']
        path_traces = []

        # Group paths by from->to pairs
        path_groups = {}
        for path in routing_paths:
            key = (path.get('from'), path.get('to'))
            if key not in path_groups:
                path_groups[key] = []
            path_groups[key].append(path)

        # Visualize unique paths
        for idx, (key, paths) in enumerate(list(path_groups.items())[:10]):  # Limit to 10 paths
            from_node, to_node = key
            if from_node not in pos or to_node not in pos:
                continue

            path_count = len(paths)
            avg_hops = sum(p.get('hops_away', 0) for p in paths) / path_count
            packet_types = set(p.get('packet_type', 'Unknown') for p in paths)

            x0, y0 = pos[from_node]
            x1, y1 = pos[to_node]

            color = path_colors[idx % len(path_colors)]

            path_trace = go.Scatter(
                x=[x0, x1, None],
                y=[y0, y1, None],
                mode='lines+markers',
                line=dict(width=3, color=color),
                marker=dict(size=8, symbol='arrow', angleref='previous'),
                hoverinfo='text',
                text=f"Route: {from_node[:8]} → {to_node[:8]}<br>"
                     f"Packets: {path_count}<br>"
                     f"Avg hops: {avg_hops:.1f}<br>"
                     f"Types: {', '.join(packet_types)}",
                name=f"{from_node[:8]} → {to_node[:8][:8]} ({path_count})",
                showlegend=True
            )
            path_traces.append(path_trace)

        # Create node trace
        node_x = []
        node_y = []
        node_text = []
        node_hover = []

        for node in self.graph.nodes(data=True):
            x, y = pos[node[0]]
            node_x.append(x)
            node_y.append(y)

            label = node[1].get('label', node[0][:8])
            node_text.append(label)
            node_hover.append(f"Node: {label}<br>ID: {node[0][:8]}")

        node_trace = go.Scatter(
            x=node_x,
            y=node_y,
            mode='markers+text',
            marker=dict(
                size=15,
                color='lightblue',
                line=dict(width=2, color='black')
            ),
            text=node_text,
            textposition="top center",
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=node_hover,
            showlegend=False
        )

        # Create figure
        fig = go.Figure(data=edge_traces + path_traces + [node_trace])

        fig.update_layout(
            title={
                'text': 'Routing Paths Visualization',
                'x': 0.5,
                'xanchor': 'center',
                'font': {'size': 24}
            },
            showlegend=True,
            hovermode='closest',
            margin=dict(b=20, l=5, r=5, t=40),
            xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
            plot_bgcolor='white',
            height=800
        )

        return fig

    def get_network_statistics(self) -> Dict[str, Any]:
        """Calculate network statistics"""
        stats = {
            'nodes': self.graph.number_of_nodes(),
            'edges': self.graph.number_of_edges(),
            'avg_degree': 0,
            'density': nx.density(self.graph) if self.graph.number_of_nodes() > 0 else 0,
            'connected_components': nx.number_connected_components(self.graph)
        }

        if self.graph.number_of_nodes() > 0:
            degrees = [d for n, d in self.graph.degree()]
            stats['avg_degree'] = sum(degrees) / len(degrees)

        return stats
    
    def save_visualization(self, output_path: str, include_routing: bool = True):
        """
        Save visualization to HTML file

        Args:
            output_path: Path for output HTML file
            include_routing: If True, also create routing paths visualization
        """
        fig = self.create_interactive_plot()
        if fig:
            fig.write_html(output_path)
            logger.info(f"Topology visualization saved to {output_path}")
        else:
            logger.error("Failed to create visualization")

        # Also create routing paths visualization if requested
        if include_routing:
            routing_fig = self.create_routing_paths_visualization()
            if routing_fig:
                routing_output = output_path.replace('.html', '_routing.html')
                routing_fig.write_html(routing_output)
                logger.info(f"Routing paths visualization saved to {routing_output}")

    def display_visualization(self):
        """Display visualization in browser"""
        fig = self.create_interactive_plot()
        if fig:
            fig.show()
        else:
            logger.error("Failed to create visualization")


def main():
    """Main entry point for visualizer"""
    parser = argparse.ArgumentParser(description='Visualize Meshtastic network topology')
    parser.add_argument('--input', '-i', required=True,
                       help='Input topology JSON file')
    parser.add_argument('--output', '-o',
                       help='Output HTML file for visualization')
    parser.add_argument('--show', action='store_true',
                       help='Display visualization in browser')
    
    args = parser.parse_args()
    
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
    print(f"Connected Components: {stats['connected_components']}")
    
    if args.output:
        visualizer.save_visualization(args.output)
    
    if args.show or not args.output:
        visualizer.display_visualization()


if __name__ == "__main__":
    main()