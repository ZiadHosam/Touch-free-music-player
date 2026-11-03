import asyncio
import json
from websockets.asyncio.server import serve

connected_clients = set()

async def handle_client(websocket):

    connected_clients.add(websocket)
    print("Client connected!")

    try:
        async for message in websocket:

            try:
                data = json.loads(message)

                # Forward recognized gestures to the other clients
                if data.get("type") == "gesture":

                    print("Gesture received:", data)

                    for client in connected_clients.copy():

                        if client != websocket:
                            await client.send(json.dumps(data))

                    print("Gesture forwarded:", data["id"])

                else:
                    print("Message received:")
                    print(json.dumps(data, indent=4))

            except json.JSONDecodeError:
                print("Invalid JSON:", message)

    finally:
        connected_clients.discard(websocket)
        print("Client disconnected!")


async def main():

    async with serve(handle_client, "localhost", 8765):

        print("WebSocket server started!")
        print("Address: ws://localhost:8765")

        await asyncio.Future()


if __name__ == "__main__":
    asyncio.run(main())