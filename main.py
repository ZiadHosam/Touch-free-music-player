
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

# Project folder
BASE_DIR = Path(__file__).parent

processes = []

try:
    print("Starting Touchless Media Controller...")

    # 1. Start WebSocket server
    print("\nStarting WebSocket server...")

    server = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "websocket_server.py")],
        cwd=BASE_DIR
    )

    processes.append(server)

    # Give the server time to start
    time.sleep(2)

    # 2. Open the website
    print("\nOpening website...")

    website = BASE_DIR / "interface.html"
    webbrowser.open(website.resolve().as_uri())

    # 3. Start Bluetooth scanner
    print("\nStarting Bluetooth scanner...")

    bluetooth = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "bluetooth_scanner.py")],
        cwd=BASE_DIR
    )

    processes.append(bluetooth)

    # 4. Start gesture recognition
    print("\nStarting gesture recognition...")

    gestures = subprocess.Popen(
        [sys.executable, str(BASE_DIR / "2.2.gesture_recognition.py")],
        cwd=BASE_DIR
    )

    processes.append(gestures)

    print("\nAll components started!")
    print("Press CTRL+C to stop the application.")

    # Keep main.py running
    while True:
        time.sleep(1)

except KeyboardInterrupt:
    print("\nStopping application...")

finally:

    for process in processes:
        process.terminate()

    for process in processes:
        process.wait()

    print("Application stopped.")
