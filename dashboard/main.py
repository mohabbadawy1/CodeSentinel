from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import asyncio
import json
import threading
from pipeline.crew import run_pipeline

app = FastAPI(title="CodeSentinel Dashboard")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Store connected WebSocket clients and log history
connected_clients: list[WebSocket] = []
log_history: list[str] = []
pipeline_status = {"running": False, "pr_url": None}


async def broadcast(message: str):
    """Send a log message to all connected WebSocket clients."""
    log_history.append(message)
    dead = []
    for ws in connected_clients:
        try:
            await ws.send_text(json.dumps({"type": "log", "message": message}))
        except Exception:
            dead.append(ws)
    for ws in dead:
        connected_clients.remove(ws)


def sync_log(message: str):
    """Thread-safe log broadcast called from the pipeline thread."""
    asyncio.run(broadcast(message))


@app.websocket("/ws")
async def websocket_endpoint(ws: WebSocket):
    await ws.accept()
    connected_clients.append(ws)
    # Send all existing logs to the new client
    for log in log_history:
        await ws.send_text(json.dumps({"type": "log", "message": log}))
    try:
        while True:
            await ws.receive_text()
    except WebSocketDisconnect:
        if ws in connected_clients:
            connected_clients.remove(ws)


@app.post("/run")
async def run(repo_url: str):
    """Start the CodeSentinel pipeline on a GitHub repository."""
    if pipeline_status["running"]:
        return {"error": "Pipeline already running. Please wait."}

    log_history.clear()
    pipeline_status["running"] = True
    pipeline_status["pr_url"] = None

    def run_in_thread():
        result = run_pipeline(repo_url, log_callback=sync_log)
        pipeline_status["running"] = False
        pipeline_status["pr_url"] = result.get("pr_url")
        sync_log(f"[DONE] Pipeline finished. PR: {result.get('pr_url', 'N/A')}")

    thread = threading.Thread(target=run_in_thread, daemon=True)
    thread.start()

    return {"status": "started", "repo": repo_url}


@app.get("/status")
def get_status():
    return pipeline_status


@app.get("/logs")
def get_logs():
    return {"logs": log_history}


@app.get("/", response_class=HTMLResponse)
def dashboard():
    """Serve the React dashboard (for development, React runs on its own port)."""
    return """
    <html>
      <body style="background:#0a0a0a;color:#fff;font-family:monospace;padding:40px">
        <h1 style="color:#e8251a">Code<span style="color:#fff">Sentinel</span></h1>
        <p>API is running. Connect your React frontend on port 5173.</p>
        <p>Or use the API directly:</p>
        <pre>POST /run?repo_url=https://github.com/owner/repo</pre>
        <pre>GET  /logs</pre>
        <pre>GET  /status</pre>
        <pre>WS   /ws</pre>
      </body>
    </html>
    """
