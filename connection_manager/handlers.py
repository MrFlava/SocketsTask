import asyncio
import logging
from datetime import datetime, timedelta

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


async def graceful_shutdown_handler():
    logger.info("Graceful shutdown initiated...")
    shutdown_event.set()

    if notification_task and not notification_task.done():
        notification_task.cancel()
        try:
            await notification_task
        except asyncio.CancelledError:
            pass

    start_time = datetime.now()
    timeout_time = start_time + timedelta(seconds=SHUTDOWN_TIMEOUT)

    while True:
        total = await manager.get_total_connections()
        now = datetime.now()

        if total == 0:
            logger.info("All connections closed.")
            break

        if now >= timeout_time:
            logger.warning(f"Timeout reached with {total} connections. Forcing shutdown...")
            break

        remaining = (timeout_time - now).total_seconds()
        logger.info(f"Active connections: {total}, Time remaining: {remaining:.0f}s")
        await asyncio.sleep(5)

    logger.info("Shutdown complete.")
