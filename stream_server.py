import asyncio
import websockets
import cv2
import numpy as np

clients = {}

async def handler(websocket):
    client_id = f"Client_{len(clients)+1}"
    clients[websocket] = client_id
    print(f"✅ {client_id} connected")

    try:
        async for message in websocket:
            # Декодируем JPEG → OpenCV
            nparr = np.frombuffer(message, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            if frame is not None:
                cv2.imshow(client_id, frame)
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except websockets.ConnectionClosed:
        print(f"❌ {client_id} disconnected")
    finally:
        del clients[websocket]
        cv2.destroyWindow(client_id)

async def main():
    async with websockets.serve(handler, "0.0.0.0", 8765):
        print("🚀 WebSocket server started on ws://0.0.0.0:8765")
        await asyncio.Future()  # run forever

asyncio.run(main())
