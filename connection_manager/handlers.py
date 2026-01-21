import asyncio
from typing import Set
from datetime import datetime, timedelta

from fastapi import WebSocket

from connection_manager.manager import  ConnectionManager
from connection_manager.settings import SHUTDOWN_TIMEOUT

# Global variables for connection tracking and shutdown
active_connections: Set[WebSocket] = set()
manager = ConnectionManager()
shutdown_event = asyncio.Event()
shutdown_timeout = SHUTDOWN_TIMEOUT


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


async def send_test_notification(message: str = None):
    """Send a test notification to all active clients"""
    if message is None:
        message = f"Test notification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

    await manager.broadcast(message)
    print(f"Sent notification to {len(manager.active_connections)} client(s): {message}")

async def periodic_notification_task(interval: int = 10):
    """Background task that sends notifications every N seconds"""
    while not shutdown_event.is_set():
        if len(manager.active_connections) > 0:
            message = f"Test notification at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            await manager.broadcast(message)
            print(f"Sent notification to {len(manager.active_connections)} client(s)")
        await asyncio.sleep(interval)


def signal_handler(signum, frame):
    """Handle shutdown signals"""
    print(f"\nReceived signal {signum}")
    shutdown_event.set()
