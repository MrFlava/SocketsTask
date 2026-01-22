import logging
import uvicorn

from connection_manager.app import app
from connection_manager.settings import APP_PORT, APP_HOST

logging.basicConfig(level=logging.INFO)


if __name__ == "__main__":
    uvicorn.run(
        app,
        host=APP_HOST,
        port=APP_PORT,
        # workers=4
    )
