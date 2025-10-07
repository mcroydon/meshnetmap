#!/usr/bin/env python3
"""
Scanner module to discover Meshtastic devices via Bluetooth
"""

import sys
import asyncio
import logging
import warnings
from typing import List, Dict, Any

try:
    import meshtastic.ble_interface
except ImportError:
    print("Error: meshtastic library not installed. Run: pip install meshtastic")
    sys.exit(1)

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MeshtasticScanner:
    """Scanner for discovering Meshtastic devices via Bluetooth"""
    
    @staticmethod
    def scan_devices(timeout: int = 10) -> List[Dict[str, Any]]:
        """
        Scan for available Meshtastic devices
        
        Args:
            timeout: Scan timeout in seconds
            
        Returns:
            List of discovered devices with name and address
        """
        logger.info(f"Scanning for Meshtastic devices (timeout: {timeout}s)...")
        
        try:
            devices = meshtastic.ble_interface.BLEInterface.scan()
            
            device_list = []
            for device in devices:
                # The meshtastic library returns BLEDevice objects
                # Try to get RSSI without triggering deprecation warning
                rssi = None
                try:
                    # Try new method first (if available)
                    if hasattr(device, 'details') and 'props' in device.details:
                        rssi = device.details.get('props', {}).get('RSSI')
                except:
                    pass
                
                # Fall back to deprecated method if needed
                if rssi is None:
                    try:
                        with warnings.catch_warnings():
                            warnings.simplefilter("ignore", FutureWarning)
                            if hasattr(device, 'rssi'):
                                rssi = device.rssi
                    except:
                        pass
                
                device_info = {
                    'name': device.name if hasattr(device, 'name') else 'Unknown',
                    'address': device.address if hasattr(device, 'address') else 'Unknown',
                    'rssi': rssi
                }
                device_list.append(device_info)
                logger.info(f"Found device: {device_info['name']} ({device_info['address']})")
            
            if not device_list:
                logger.warning("No Meshtastic devices found")
            else:
                logger.info(f"Found {len(device_list)} Meshtastic device(s)")
                
            return device_list
            
        except Exception as e:
            logger.error(f"Error during scan: {str(e)}")
            return []


def main():
    """Main entry point for scanner"""
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
        print("\nNo Meshtastic devices found. Please ensure:")
        print("1. Bluetooth is enabled on your computer")
        print("2. Meshtastic device is powered on and has Bluetooth enabled")
        print("3. You have necessary permissions to access Bluetooth")


if __name__ == "__main__":
    main()