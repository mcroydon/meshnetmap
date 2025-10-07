#!/usr/bin/env python3
"""
Helper script for pairing with Meshtastic devices on macOS
"""

import sys
import time
import subprocess
import argparse

def check_paired_devices():
    """Check for paired Meshtastic devices using system_profiler"""
    print("Checking for paired Bluetooth devices...")
    try:
        result = subprocess.run(
            ["system_profiler", "SPBluetoothDataType", "-json"],
            capture_output=True,
            text=True
        )
        
        import json
        data = json.loads(result.stdout)
        
        # Look for Meshtastic devices
        paired_devices = []
        if "SPBluetoothDataType" in data:
            for item in data["SPBluetoothDataType"]:
                if isinstance(item, dict):
                    # Check connected devices
                    if "device_connected" in item and isinstance(item["device_connected"], dict):
                        for device_key, device_info in item["device_connected"].items():
                            if "Meshtastic" in device_key or "🫘" in device_key:
                                paired_devices.append({
                                    "name": device_key,
                                    "address": device_info.get("device_address", "Unknown")
                                })
                    # Check other device lists
                    for key in ["device_title", "device_not_connected"]:
                        if key in item:
                            if isinstance(item[key], dict):
                                for device_name in item[key]:
                                    if "Meshtastic" in device_name or "🫘" in device_name:
                                        paired_devices.append({
                                            "name": device_name,
                                            "address": "Check in Bluetooth settings"
                                        })
        
        return paired_devices
    except Exception as e:
        print(f"Error checking devices: {e}")
        return []


def open_bluetooth_settings():
    """Open Bluetooth settings on macOS"""
    print("Opening Bluetooth settings...")
    subprocess.run(["open", "/System/Library/PreferencePanes/Bluetooth.prefPane"])


def main():
    parser = argparse.ArgumentParser(description='Help pair Meshtastic devices on macOS')
    parser.add_argument('--check', action='store_true', help='Check for paired devices')
    parser.add_argument('--auto', action='store_true', help='Automatically open Bluetooth settings')
    args = parser.parse_args()
    
    print("=" * 60)
    print("MESHTASTIC BLUETOOTH PAIRING HELPER")
    print("=" * 60)
    print()
    
    if args.check:
        paired = check_paired_devices()
        if paired:
            print("Found paired Meshtastic devices:")
            for device in paired:
                print(f"  - {device['name']} ({device['address']})")
        else:
            print("No paired Meshtastic devices found.")
        return
    
    print("PAIRING INSTRUCTIONS FOR macOS:")
    print("-" * 40)
    print()
    print("1. The Bluetooth settings will open automatically")
    print("2. Look for your Meshtastic device (e.g., '🫘_e885')")
    print("3. Click 'Connect' or 'Pair' next to the device")
    print("4. If prompted for a PIN, enter: 123456")
    print("   (This is the default Meshtastic PIN)")
    print("5. Wait for the pairing to complete")
    print("6. The device should show as 'Connected'")
    print()
    print("TROUBLESHOOTING:")
    print("-" * 40)
    print("- If the device doesn't appear, make sure:")
    print("  * The Meshtastic device is powered on")
    print("  * Bluetooth is enabled on the device")
    print("  * You're within range (< 10 meters)")
    print()
    print("- If pairing fails with PIN 123456:")
    print("  * Try PIN: 654321 (alternative default)")
    print("  * Check device settings via the Meshtastic app")
    print()
    print("- If you see 'Encryption is insufficient' error:")
    print("  * Remove any existing pairing and re-pair")
    print("  * Restart Bluetooth: sudo killall bluetoothd")
    print()
    
    if args.auto:
        open_bluetooth_settings()
        print()
        print("Bluetooth settings opened automatically.")
    else:
        try:
            response = input("Open Bluetooth settings now? (y/n): ")
            if response.lower() == 'y':
                open_bluetooth_settings()
                print()
                print("Bluetooth settings opened.")
        except (EOFError, KeyboardInterrupt):
            print("\nYou can open Bluetooth settings manually from System Settings")
            pass
    
    print()
    print("After pairing is complete, run:")
    print("  meshnetmap collect -a <DEVICE_ADDRESS>")
    print()
    print("To find the device address, run:")
    print("  meshnetmap scan")


if __name__ == "__main__":
    main()