import asyncio
import logging

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from connection_manager.manager import manager
from connection_manager.handlers import shutdown_event, lifespan


logger = logging.getLogger(__name__)


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while not shutdown_event.is_set():
            try:
                data = await asyncio.wait_for(websocket.receive_text(), timeout=1.0)
                await websocket.send_text(f"Echo: {data}")
            except asyncio.TimeoutError:
                continue
    except WebSocketDisconnect:
        await manager.disconnect(websocket)


@app.post("/notify")
async def send_notification(message: str):
    await manager.broadcast(f"Manual notification: {message}")
    total = await manager.get_total_connections()
    return {"status": "sent", "total_recipients": total}


@app.get("/status")
async def get_status():
    return {
        "active_connections": await manager.get_total_connections(),
        "shutdown_pending": shutdown_event.is_set()
    }
