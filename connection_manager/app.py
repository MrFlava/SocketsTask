import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocketDisconnect, WebSocket


from connection_manager.handlers import shutdown_event, graceful_shutdown_handler, periodic_notification_task, manager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Server starting up...")
    task = asyncio.create_task(periodic_notification_task(interval=10))
    yield
    # Shutdown
    task.cancel()
    if shutdown_event.is_set():
        await graceful_shutdown_handler()
    print("Server shut down complete.")


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()
            print(f"Received: {data}")

            # Echo back to sender
            await websocket.send_text(f"Echo: {data}")

            # Broadcast to all clients
            await manager.broadcast(f"Notification: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)


@app.post("/notify")
async def send_notification(message: str):
    """Endpoint to trigger notifications to all connected clients"""
    await manager.broadcast(f"Server notification: {message}")
    return {"status": "notification sent", "recipients": len(manager.active_connections)}


@app.get("/status")
async def get_status():
    """Check server status and active connections"""
    return {
        "active_connections": len(manager.active_connections),
        "shutdown_pending": shutdown_event.is_set()
    }