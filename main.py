import signal
import uvicorn

from connection_manager.settings import *
from connection_manager.app import app
from connection_manager.handlers import signal_handler

if __name__ == "__main__":
    # Register signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    uvicorn.run(app, host=APP_HOST, port=APP_PORT)
