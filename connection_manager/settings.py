import os

from dotenv import load_dotenv

load_dotenv()

SHUTDOWN_TIMEOUT = 1800 # 30 minutes in seconds
NOTIFICATION_INTERVAL =10 # 10 seconds
APP_PORT = int(os.getenv("PORT"))
APP_HOST = os.getenv("HOST")
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
REDIS_KEY = "websocket:connections"
REDIS_SHUTDOWN_KEY = "websocket:shutdown"
