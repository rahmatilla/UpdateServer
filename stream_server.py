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

async def send_command(target_id: str, command: str):
    """Отправить команду конкретному клиенту"""
    for ws, cid in clients.items():
        if cid == target_id:
            await ws.send(command)
            print(f"📤 Sent '{command}' to {target_id}")
            return
    print(f"⚠️ Client {target_id} not found")

async def list_clients():
    """Вывести список подключённых клиентов"""
    if not clients:
        print("⚠️ No active clients")
    else:
        print("🔗 Connected clients:")
        for cid in clients.values():
            print(f"   - {cid}")

async def cli_loop():
    """Асинхронный CLI для управления"""
    while True:
        cmd = (await asyncio.to_thread(input, "Введите команду (LIST / START <id> / STOP <id> / EXIT): ")).strip().split()
        if not cmd:
            continue

        if cmd[0].upper() == "LIST":
            await list_clients()
        elif cmd[0].upper() in ("START", "STOP") and len(cmd) == 2:
            await send_command(cmd[1], cmd[0].upper())
        elif cmd[0].upper() == "EXIT":
            print("👋 Exiting server...")
            for ws in list(clients.keys()):
                await ws.close()
            break
        else:
            print("❓ Unknown command")

async def main():
    server = await websockets.serve(handler, "0.0.0.0", 8765)
    print("🚀 WebSocket server started on ws://0.0.0.0:8765")

    # Запускаем сервер и CLI параллельно
    await asyncio.gather(
        server.wait_closed(),
        cli_loop()
    )

if __name__ == "__main__":
    asyncio.run(main())
