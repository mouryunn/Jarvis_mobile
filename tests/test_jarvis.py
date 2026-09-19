import os
import sys

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.config import settings
from actions.termux_api import termux_api
from actions.adb_control import adb_controller
from actions.web_tools import web_tools
from core.tools_schema import execute_tool, TOOL_DEFINITIONS
from core.brain import brain

def test_config():
    print("Testing config...")
    assert settings.assistant_name == "JARVIS"
    assert settings.port == 8000
    print("[PASS] Config loaded successfully.")

def test_termux_api_simulation():
    print("Testing Termux:API simulation...")
    res = termux_api.toggle_torch(True)
    assert res["success"] is True
    assert res["torch_state"] == "ON"

    res = termux_api.toggle_torch(False)
    assert res["success"] is True
    assert res["torch_state"] == "OFF"

    batt = termux_api.get_battery_status()
    assert batt["success"] is True
    assert "percentage" in batt

    vib = termux_api.vibrate(300)
    assert vib["success"] is True

    clip = termux_api.set_clipboard("Test JARVIS")
    assert clip["success"] is True

    photo = termux_api.take_camera_photo(0)
    assert photo["success"] is True
    assert os.path.exists(photo["file_path"])
    print("[PASS] Termux:API functions passed.")

def test_adb_simulation():
    print("Testing ADB simulation...")
    res = adb_controller.launch_app("youtube")
    assert res["success"] is True
    assert res["package"] == "com.google.android.youtube"

    tap_res = adb_controller.tap(500, 1000)
    assert tap_res["success"] is True

    shot = adb_controller.capture_screenshot()
    assert shot["success"] is True
    assert os.path.exists(shot["file_path"])
    print("[PASS] ADB functions passed.")

def test_web_tools():
    print("Testing Web & System tools...")
    time_res = web_tools.get_current_time_and_date()
    assert time_res["success"] is True
    assert "datetime" in time_res

    search_res = web_tools.search_web("Python programming", max_results=2)
    assert search_res["success"] is True
    assert len(search_res["results"]) > 0
    print("[PASS] Web & System tools passed.")

def test_tool_dispatcher():
    print("Testing tool dispatcher...")
    res = execute_tool("toggle_torch", {"state": True})
    assert res["success"] is True

    res2 = execute_tool("get_battery_status", {})
    assert res2["success"] is True
    assert "percentage" in res2
    print("[PASS] Tool dispatcher passed.")

def test_brain_offline():
    print("Testing Brain offline / simulation handling...")
    res = brain.ask("Turn on the flashlight")
    assert res["success"] is True
    assert "Flashlight" in res["response"] or len(res["actions"]) > 0

    res2 = brain.ask("What is my battery level?")
    assert res2["success"] is True
    assert "battery" in res2["response"].lower() or len(res2["actions"]) > 0
    print("[PASS] Brain response passed.")

def test_server_routes():
    print("Testing Starlette server endpoints...")
    from starlette.testclient import TestClient
    from server import app

    client = TestClient(app)
    resp = client.get("/")
    assert resp.status_code == 200
    assert "JARVIS" in resp.text

    status_resp = client.get("/api/status")
    assert status_resp.status_code == 200
    assert status_resp.json()["status"] == "online"

    action_resp = client.post("/api/action", json={"tool": "get_battery_status", "args": {}})
    assert action_resp.status_code == 200
    assert action_resp.json()["result"]["success"] is True
    print("[PASS] Server endpoints passed.")

if __name__ == "__main__":
    test_config()
    test_termux_api_simulation()
    test_adb_simulation()
    test_web_tools()
    test_tool_dispatcher()
    test_brain_offline()
    test_server_routes()
    print("\n[SUCCESS] ALL TESTS PASSED SUCCESSFULLY!")
