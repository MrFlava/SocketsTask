import os

from dotenv import load_dotenv

load_dotenv()

SHUTDOWN_TIMEOUT = int(os.getenv("SHUTDOWN_TIMEOUT"))
APP_PORT = int(os.getenv("PORT"))
APP_HOST = os.getenv("HOST")