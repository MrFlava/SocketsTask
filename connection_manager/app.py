import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, WebSocket, WebSocketDisconnect

from connection_manager.manager import manager
from connection_manager.handlers import (
    periodic_notification_task,
    notification_task,
    graceful_shutdown_handler,
    shutdown_event,
)


logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.setup()
    notification_task = asyncio.create_task(periodic_notification_task())
    logger.info("Server started")
    yield
    await graceful_shutdown_handler()
    await manager.teardown()
    logger.info("Server stopped")


app = FastAPI(lifespan=lifespan)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while not shutdown_event.is_set():
            data = await websocket.receive_text()
            await websocket.send_text(f"Echo: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
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
