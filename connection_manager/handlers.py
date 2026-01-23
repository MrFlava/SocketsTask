import asyncio
import logging
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from fastapi import FastAPI

from connection_manager.manager import manager
from connection_manager.settings import SHUTDOWN_TIMEOUT, NOTIFICATION_INTERVAL

logger = logging.getLogger(__name__)

shutdown_event = asyncio.Event()
notification_task = None


async def periodic_notification_task():
    """Send notifications every 10 seconds to all connected clients"""
    logger.info("Periodic notification task started")
    while not shutdown_event.is_set():
        try:
            await asyncio.sleep(NOTIFICATION_INTERVAL)
            if manager.local_connections:
                message = f"Periodic notification at {datetime.now().isoformat()}"
                await manager.broadcast(message)
                logger.info(f"Sent periodic notification to {len(manager.local_connections)} clients")
        except asyncio.CancelledError:
            logger.info("Periodic notification task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in periodic notification: {e}")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await manager.setup()
    await manager.clear_shutdown_signal()  # Clear any stale shutdown signals

    global notification_task
    notification_task = asyncio.create_task(periodic_notification_task())
    logger.info("Server started")

    yield

    # Only the parent process should signal shutdown
    import os
    if os.getpid() == os.getppid() or os.environ.get("IS_MAIN_WORKER") == "1":
        await manager.signal_shutdown()

    await graceful_shutdown_handler()
    await manager.close_all_connections()
    await manager.teardown()
    logger.info("Server stopped")


async def graceful_shutdown_handler():
    logger.info("Graceful shutdown initiated...")
    shutdown_event.set()

    # Cancel notification task
    global notification_task
    if notification_task and not notification_task.done():
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass

    # Wait for connections to close
    start_time = datetime.now()
    timeout_time = start_time + timedelta(seconds=SHUTDOWN_TIMEOUT)

    while datetime.now() < timeout_time:
        total = await manager.get_total_connections()
        if total == 0:
            logger.info("All connections closed.")
            return

        remaining = (timeout_time - datetime.now()).total_seconds()
        logger.info(f"Active connections: {total}, Time remaining: {remaining:.0f}s")
        await asyncio.sleep(2)

    # Timeout reached
    total = await manager.get_total_connections()
    logger.warning(f"Timeout reached with {total} connections remaining")
