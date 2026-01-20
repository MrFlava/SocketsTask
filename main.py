import asyncio
import signal
from datetime import datetime, timedelta
from typing import Set
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from contextlib import asynccontextmanager
import uvicorn

# Global variables for connection tracking and shutdown
active_connections: Set[WebSocket] = set()
shutdown_event = asyncio.Event()
shutdown_timeout = 1800  # 30 minutes in seconds

# DRAFT VERSION
class ConnectionManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.add(websocket)
        print(f"Client connected. Total connections: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket):
        self.active_connections.discard(websocket)
        print(f"Client disconnected. Total connections: {len(self.active_connections)}")

    async def broadcast(self, message: str):
        """Send message to all connected clients"""
        for connection in self.active_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                print(f"Error sending message: {e}")
                self.disconnect(connection)

    def has_active_connections(self) -> bool:
        return len(self.active_connections) > 0


manager = ConnectionManager()


async def graceful_shutdown_handler():
    """Handle graceful shutdown with timeout"""
    print("Shutdown signal received. Waiting for connections to close...")
    start_time = datetime.now()
    timeout_time = start_time + timedelta(seconds=shutdown_timeout)

    while manager.has_active_connections():
        if datetime.now() >= timeout_time:
            print("Shutdown timeout reached. Forcing shutdown...")
            break

        remaining = len(manager.active_connections)
        print(f"Waiting for {remaining} connection(s) to close...")
        await asyncio.sleep(5)

    print("All connections closed or timeout reached. Shutting down...")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    print("Server starting up...")
    yield
    # Shutdown
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


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}")
    shutdown_event.set()


if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    uvicorn.run(app, host="0.0.0.0", port=8000)
