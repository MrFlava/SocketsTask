import logging
import uvicorn


from connection_manager.app import app
from connection_manager.settings import APP_HOST, APP_PORT

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    # Workers > 1 now supported via Redis shutdown signaling
    uvicorn.run(
        app,
        host=APP_HOST,
        port=APP_PORT,
        workers=4,
        log_level="info"
    )
