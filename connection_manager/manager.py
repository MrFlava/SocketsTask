import asyncio
import logging

import redis.asyncio as redis
from fastapi import WebSocket


from connection_manager.settings import REDIS_URL, REDIS_KEY, REDIS_SHUTDOWN_KEY

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    def __init__(self):
        self.redis_client = None
        self.local_connections = set()
        self._shutdown_check_task = None

    async def setup(self):
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Redis connection established")
        # Start monitoring shutdown signal
        self._shutdown_check_task = asyncio.create_task(self._monitor_shutdown())

    async def teardown(self):
        if self._shutdown_check_task:
            self._shutdown_check_task.cancel()
            try:
                await self._shutdown_check_task
            except asyncio.CancelledError:
                pass
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def _monitor_shutdown(self):
        """Monitor Redis for shutdown signal"""
        while True:
            try:
                should_shutdown = await self.redis_client.get(REDIS_SHUTDOWN_KEY)
                if should_shutdown == "1":
                    from connection_manager.handlers import shutdown_event
                    shutdown_event.set()
                    logger.info("Shutdown signal received from Redis")
                    break
                await asyncio.sleep(1)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error monitoring shutdown: {e}")
                await asyncio.sleep(1)

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.local_connections.add(websocket)
        await self.redis_client.incr(REDIS_KEY)
        total = await self.get_total_connections()
        logger.info(f"Client connected. Total across workers: {total}")

    async def disconnect(self, websocket: WebSocket):
        self.local_connections.discard(websocket)
        # Atomic decrement with floor at 0
        new_count = await self.redis_client.decr(REDIS_KEY)
        if new_count < 0:
            await self.redis_client.set(REDIS_KEY, 0)
        total = await self.get_total_connections()
        logger.info(f"Client disconnected. Total across workers: {total}")

    async def get_total_connections(self) -> int:
        count = await self.redis_client.get(REDIS_KEY)
        return int(count or 0)

    async def broadcast(self, message: str):
        for connection in self.local_connections.copy():
            try:
                await connection.send_text(message)
            except Exception as e:
                logger.error(f"Error broadcasting: {e}")
                await self.disconnect(connection)

    async def close_all_connections(self):
        """Close all local WebSocket connections"""
        for ws in self.local_connections.copy():
            try:
                await ws.close(code=1001, reason="Server shutting down")
            except Exception as e:
                logger.error(f"Error closing websocket: {e}")
        self.local_connections.clear()

    async def signal_shutdown(self):
        """Signal all workers to begin shutdown"""
        await self.redis_client.set(REDIS_SHUTDOWN_KEY, "1")
        logger.info("Shutdown signal sent to all workers")

    async def clear_shutdown_signal(self):
        """Clear shutdown signal (for startup)"""
        await self.redis_client.delete(REDIS_SHUTDOWN_KEY)



manager = RedisConnectionManager()
