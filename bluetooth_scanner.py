
import asyncio
import json
import statistics

from pathlib import Path
from datetime import datetime
from collections import defaultdict
from bleak import BleakScanner
from websockets.asyncio.client import connect


# Registered users identified by BLE advertised name
REGISTERED_USERS = {
    "realme c55": {
        "user_id": "1001",
        "name": "Mohamed",
        "context": "focus"
    },

    "pixel 5": {
        "user_id": "1002",
        "name": "Mohsen",
        "context": "workout"
    },
    
    "poco x3 gt": {
            "user_id": "1003",
            "name": "Ziad",
            "context": "chill"
        },
}

SCAN_DURATION = 10
JSON_FILE = Path("bluetooth_users.json")


# Send nearest user to the HTML website
async def send_user_to_webapp(user):

    if user is None:
        return

    message = {
        "type": "user",
        "id": user["user_id"],
        "name": user["registered_user"],
        "context": user["context"]
    }

    try:

        async with connect("ws://localhost:8765") as websocket:

            await websocket.send(json.dumps(message))

            print("\nUser sent to web app!")
            print("UserID:", user["user_id"])
            print("Name:", user["registered_user"])
            print("Context:", user["context"])

    except OSError as error:

        print("Could not send user to web app.")
        print(error)


async def scan_bluetooth_devices():

    rssi_samples = defaultdict(list)
    latest_devices = {}

    def detection_callback(device, advertisement_data):

        # Read the advertised device name
        device_name = (
            advertisement_data.local_name
            or device.name
            or ""
        )

        # Identify by name, not MAC address
        name_key = device_name.strip().casefold()

        user = REGISTERED_USERS.get(name_key)

        # Ignore unregistered devices
        if not user:
            return

        rssi = advertisement_data.rssi

        if rssi is None:
            return

        user_id = user["user_id"]

        # Collect RSSI measurements
        rssi_samples[user_id].append(rssi)

        # Keep the latest Bluetooth address
        latest_devices[user_id] = {
            "device_name": device_name,
            "bluetooth_address": device.address,
            "user_id": user_id,
            "registered_user": user["name"],
            "context": user["context"]
        }

        print(
            f"Detected: {device_name} | "
            f"RSSI: {rssi} dBm | "
            f"UserID: {user_id}"
        )

    scanner = BleakScanner(
        detection_callback=detection_callback
    )

    print("Starting BLE discovery...")
    print(f"Scanning for {SCAN_DURATION} seconds...\n")

    try:

        await scanner.start()

        await asyncio.sleep(SCAN_DURATION)

    finally:

        await scanner.stop()

    # Calculate median RSSI for every registered device
    detected_users = []

    for user_id, samples in rssi_samples.items():

        device = latest_devices[user_id]

        detected_users.append({
            **device,
            "median_rssi": statistics.median(samples),
            "average_rssi": round(statistics.mean(samples), 2),
            "samples_count": len(samples)
        })

    # Select strongest registered device
    if detected_users:

        nearest = max(
            detected_users,
            key=lambda x: x["median_rssi"]
        )

        print("\n" + "=" * 40)
        print("NEAREST REGISTERED USER")
        print("=" * 40)

        print("Name:", nearest["registered_user"])
        print("UserID:", nearest["user_id"])
        print("Device:", nearest["device_name"])
        print("Current MAC:", nearest["bluetooth_address"])
        print("Median RSSI:", nearest["median_rssi"], "dBm")

        # Send identified user to the website
        await send_user_to_webapp(nearest)

    else:

        nearest = None
        print("\nNo registered users detected.")

    # Save scan results
    record = {
        "scan_time": datetime.now().astimezone().isoformat(),
        "nearest_user": nearest,
        "detected_users": detected_users
    }

    history = []

    if JSON_FILE.exists():

        try:

            with open(JSON_FILE, "r", encoding="utf-8") as file:
                history = json.load(file)

            if not isinstance(history, list):
                raise ValueError("Expected JSON history to be a list.")

        except (json.JSONDecodeError, ValueError) as error:

            print("Cannot read existing JSON:", error)
            return

    history.append(record)

    with open(JSON_FILE, "w", encoding="utf-8") as file:
        json.dump(history, file, indent=4, ensure_ascii=False)

    print("\nResults saved to:", JSON_FILE)


if __name__ == "__main__":
    asyncio.run(scan_bluetooth_devices())
