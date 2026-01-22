import logging
import redis.asyncio as redis
from fastapi import WebSocket

from connection_manager.settings import REDIS_URL, REDIS_KEY

logger = logging.getLogger(__name__)


class RedisConnectionManager:
    def __init__(self):
        self.redis_client = None
        self.local_connections = set()

    async def setup(self):
        self.redis_client = await redis.from_url(REDIS_URL, decode_responses=True)
        logger.info("Redis connection established")

    async def teardown(self):
        if self.redis_client:
            await self.redis_client.close()
            logger.info("Redis connection closed")

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.local_connections.add(websocket)
        await self.redis_client.incr(REDIS_KEY)
        total = await self.get_total_connections()
        logger.info(f"Client connected. Total across workers: {total}")

    async def disconnect(self, websocket: WebSocket):
        self.local_connections.discard(websocket)
        current = await self.get_total_connections()
        if current > 0:
            await self.redis_client.decr(REDIS_KEY)
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


manager = RedisConnectionManager()
