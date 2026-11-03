
# pip install bleak

import asyncio
from bleak import BleakScanner
from datetime import datetime

# Registered devices: Bluetooth address -> User information
REGISTERED_USERS = {
    "AA:BB:CC:DD:EE:FF": {
        "user_id": "1001",
        "name": "Mohamed"
    },
    "11:22:33:44:55:66": {
        "user_id": "1002",
        "name": "Nour"
    }
}


async def scan_bluetooth_devices():

    print("Scanning for Bluetooth devices...")

    try:
        # Discover nearby BLE devices and their advertisements
        devices = await BleakScanner.discover(
            timeout=20,
            return_adv=True
        )

        scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        print(f"\nScan completed at {scan_time}")
        print(f"Found {len(devices)} devices:\n")

        for address, (device, adv) in devices.items():

            device_name = adv.local_name or device.name or "Unknown"

            # Check whether the device belongs to a registered user
            user = REGISTERED_USERS.get(address.upper())

            print(f"Device Name: {device_name}")
            print(f"Bluetooth Address: {address}")
            print(f"RSSI: {adv.rssi} dBm")
            if user:
                print(f"UserID: {user['user_id']}")
                print(f"Registered User: {user['name']}")
                print("Status: Registered")
            else:
                print("UserID: Not identified")
                print("Status: Unknown device")

            print(f"Signal Strength: {adv.rssi} dBm")
            print("-" * 40)

    except Exception as e:
        print(f"An error occurred: {str(e)}")


async def main():
    print("Starting Bluetooth scan...")
    await scan_bluetooth_devices()


if __name__ == "__main__":
    asyncio.run(main())