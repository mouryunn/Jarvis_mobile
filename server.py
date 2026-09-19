import os
import json
import logging
from pathlib import Path
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel

from core.config import settings
from core.brain import brain
from core.tools_schema import execute_tool
from actions.termux_api import termux_api

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("jarvis.server")

BASE_DIR = Path(__file__).resolve().parent
app = FastAPI(title="JARVIS Mobile", description="Mark-LIV Mobile Assistant for Android Termux")

# Mount static files
static_dir = BASE_DIR / "hud" / "static"
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

class ActionRequest(BaseModel):
    tool: str
    args: dict = {}

@app.get("/", response_class=HTMLResponse)
async def index():
    """Serve the holographic mobile Web HUD."""
    template_path = BASE_DIR / "hud" / "templates" / "index.html"
    return FileResponse(template_path)

@app.get("/api/status")
async def get_status():
    """Get system health, battery, and execution environment."""
    battery = termux_api.get_battery_status()
    return {
        "status": "online",
        "assistant": settings.assistant_name,
        "model": settings.gemini_model,
        "is_termux": settings.is_termux,
        "has_termux_api": settings.has_termux_api,
        "has_adb": settings.has_adb,
        "simulation_mode": settings.simulation_mode,
        "battery": battery
    }

@app.post("/api/action")
async def trigger_action(req: ActionRequest):
    """Directly trigger a hardware action via REST."""
    res = execute_tool(req.tool, req.args)
    return {"tool": req.tool, "result": res}

@app.websocket("/ws/jarvis")
async def websocket_endpoint(websocket: WebSocket):
    """Real-time bi-directional channel between Web HUD and Jarvis brain."""
    await websocket.accept()
    logger.info("New WebSocket client connected to JARVIS Mobile.")

    # Send initial status
    battery = termux_api.get_battery_status()
    await websocket.send_json({
        "type": "battery",
        "percentage": battery.get("percentage", 85),
        "status": battery.get("status", "CHARGING")
    })

    try:
        while True:
            raw_data = await websocket.receive_text()
            try:
                data = json.loads(raw_data)
            except json.JSONDecodeError:
                continue

            msg_type = data.get("type")
            if msg_type == "command":
                user_text = data.get("text", "").strip()
                if not user_text:
                    continue

                # Notify client that Jarvis is processing
                await websocket.send_json({"type": "thinking"})

                # Query Jarvis Brain
                result = brain.ask(user_text)

                # Send back the response with executed actions
                await websocket.send_json({
                    "type": "response",
                    "text": result.get("response", "Sir, I have completed the request."),
                    "actions": result.get("actions", []),
                    "success": result.get("success", True)
                })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected.")
    except Exception as e:
        logger.error(f"WebSocket session error: {e}")
