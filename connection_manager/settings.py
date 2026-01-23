import os

from dotenv import load_dotenv

load_dotenv()

SHUTDOWN_TIMEOUT = int(os.getenv("SHUTDOWN_TIMEOUT"))
NOTIFICATION_INTERVAL = int(os.getenv("NOTIFICATION_INTERVAL"))
APP_PORT = int(os.getenv("PORT"))
APP_HOST = os.getenv("HOST")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_KEY = "websocket:connections"
REDIS_SHUTDOWN_KEY = "websocket:shutdown"
