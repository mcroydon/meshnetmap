"""
Meshtastic Network Topology Mapper

A tool for mapping and visualizing Meshtastic mesh network topology
via Bluetooth connections.
"""

__version__ = "1.0.0"

from .cli import main

__all__ = ["main"]