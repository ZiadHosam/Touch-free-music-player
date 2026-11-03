
import asyncio
import json
from websockets.asyncio.server import serve

connected_clients = set()


async def handle_client(websocket):

    connected_clients.add(websocket)
    print("Client connected!")
    #print("Total connected clients:", len(connected_clients))

    try:
        async for message in websocket:

            try:
                data = json.loads(message)
                message_type = data.get("type")

                if message_type in ["gesture", "user"]:

                    print("\nMessage received:")
                    print(json.dumps(data, indent=4))

                    sent_count = 0

                    for client in list(connected_clients):

                        if client != websocket:

                            try:
                                await client.send(json.dumps(data))
                                sent_count += 1

                            except Exception as error:
                                print("Could not forward message:", error)

                    print("Forwarded to", sent_count, "client(s)")

                else:
                    print("Other message:", data)

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
