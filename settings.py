import os

from dotenv import load_dotenv

load_dotenv()

shutdown_timeout = int(os.getenv("SHUTDOWN_TIMEOUT"))