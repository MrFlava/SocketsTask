# WebSocket Server with Graceful Shutdown

## Setup Instructions

1. **Clone the repository**  
   `git clone <repo-url> && cd SocketsTask`

2. **Start Redis using Docker Compose**  
   ```bash
   docker-compose up -d

3. Install Python dependencies
   ```bash
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt

4. Run the server
   ```bash
    uvicorn main:app --workers 4 
   
## How to Test the WebSocket 
* Connect to the WebSocket endpoint at ws://localhost:8000/ws using Postman or browser tools
* Send messages and receive echo responses.

## Graceful Shutdown Logic
* On receiving a SIGTERM or SIGINT (e.g., Ctrl+C or docker-compose stop), the server:
    * Signals all workers to begin shutdown via Redis.
    * Waits for all active WebSocket clients to disconnect.
    * If clients remain after 30 minutes, it forcefully closes remaining connections.
    * Logs shutdown progress, including connection count and remaining time, throughout the process.