import json
import os
import subprocess
import shutil
import tempfile
from typing import Dict, Any, Optional
from core.config import settings

class TermuxAPIController:
    """Controls Android hardware and OS features using Termux:API commands.
    Falls back gracefully to simulation mode when not running on a Termux device.
    """

    def __init__(self):
        self._simulated_state = {
            "torch": False,
            "clipboard": "Simulated clipboard content",
            "battery": {
                "percentage": 88,
                "plugged": "PLUGGED_AC",
                "status": "CHARGING",
                "health": "GOOD",
                "temperature": 29.5
            }
        }

    def _is_native(self) -> bool:
        return settings.is_termux and settings.has_termux_api and not settings.simulation_mode

    def _run_cmd(self, cmd: list[str], timeout: int = 10) -> tuple[int, str, str]:
        """Execute a command safely."""
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except FileNotFoundError:
            return 127, "", f"Command '{cmd[0]}' not found."
        except subprocess.TimeoutExpired:
            return 124, "", "Command timed out."
        except Exception as e:
            return 1, "", str(e)

    def toggle_torch(self, state: bool) -> Dict[str, Any]:
        """Turn the Android flashlight/torch on or off."""
        if not self._is_native():
            self._simulated_state["torch"] = state
            return {
                "success": True,
                "mode": "simulated",
                "torch_state": "ON" if state else "OFF",
                "message": f"[Simulation] Flashlight turned {'ON' if state else 'OFF'}."
            }

        cmd = ["termux-torch", "on" if state else "off"]
        code, stdout, stderr = self._run_cmd(cmd)
        if code == 0:
            return {"success": True, "torch_state": "ON" if state else "OFF", "message": f"Flashlight is now {'ON' if state else 'OFF'}."}
        return {"success": False, "error": stderr or "Failed to toggle flashlight."}

    def get_battery_status(self) -> Dict[str, Any]:
        """Retrieve battery percentage, charging status, health, and temperature."""
        if not self._is_native():
            return {
                "success": True,
                "mode": "simulated",
                **self._simulated_state["battery"],
                "message": f"[Simulation] Battery at {self._simulated_state['battery']['percentage']}% (Charging)."
            }

        code, stdout, stderr = self._run_cmd(["termux-battery-status"])
        if code == 0 and stdout:
            try:
                data = json.loads(stdout)
                return {
                    "success": True,
                    "percentage": data.get("percentage", 0),
                    "plugged": data.get("plugged", "UNPLUGGED"),
                    "status": data.get("status", "DISCHARGING"),
                    "health": data.get("health", "UNKNOWN"),
                    "temperature": data.get("temperature", 0),
                    "message": f"Battery is at {data.get('percentage')}% ({data.get('status')})."
                }
            except json.JSONDecodeError:
                pass
        return {"success": False, "error": stderr or "Unable to read battery status."}

    def vibrate(self, duration_ms: int = 500) -> Dict[str, Any]:
        """Vibrate the phone for a specified duration in milliseconds."""
        if not self._is_native():
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Vibrated device for {duration_ms}ms."}

        code, _, stderr = self._run_cmd(["termux-vibrate", "-d", str(duration_ms)])
        if code == 0:
            return {"success": True, "message": f"Vibrated device for {duration_ms}ms."}
        return {"success": False, "error": stderr or "Failed to vibrate device."}

    def show_notification(self, title: str, content: str, priority: str = "high") -> Dict[str, Any]:
        """Show a native Android status bar notification."""
        if not self._is_native():
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Notification sent: [{title}] {content}"}

        cmd = [
            "termux-notification",
            "--title", title,
            "--content", content,
            "--priority", priority,
            "--vibrate", "200,200",
            "--id", "jarvis_notification"
        ]
        code, _, stderr = self._run_cmd(cmd)
        if code == 0:
            return {"success": True, "message": f"Notification posted: '{title}'"}
        return {"success": False, "error": stderr or "Failed to display notification."}

    def get_clipboard(self) -> Dict[str, Any]:
        """Read text from the Android system clipboard."""
        if not self._is_native():
            return {"success": True, "mode": "simulated", "clipboard": self._simulated_state["clipboard"]}

        code, stdout, stderr = self._run_cmd(["termux-clipboard-get"])
        if code == 0:
            return {"success": True, "clipboard": stdout}
        return {"success": False, "error": stderr or "Failed to access clipboard."}

    def set_clipboard(self, text: str) -> Dict[str, Any]:
        """Copy text to the Android system clipboard."""
        if not self._is_native():
            self._simulated_state["clipboard"] = text
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Copied text to clipboard."}

        code, _, stderr = self._run_cmd(["termux-clipboard-set", text])
        if code == 0:
            return {"success": True, "message": "Text copied to clipboard successfully."}
        return {"success": False, "error": stderr or "Failed to set clipboard."}

    def speak_tts(self, text: str, pitch: float = 1.0, rate: float = 1.0) -> Dict[str, Any]:
        """Use the Android Text-to-Speech engine to speak aloud."""
        if not self._is_native():
            return {"success": True, "mode": "simulated", "message": f"[Simulation Speech] '{text}'"}

        cmd = ["termux-tts-speak", "-p", str(pitch), "-r", str(rate), text]
        code, _, stderr = self._run_cmd(cmd)
        if code == 0:
            return {"success": True, "message": "Speech completed."}
        return {"success": False, "error": stderr or "TTS failed."}

    def take_camera_photo(self, camera_id: int = 0, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Take a photo using Android front (1) or rear (0) camera."""
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), f"jarvis_cam_{camera_id}.jpg")

        if not self._is_native():
            # Create a simple placeholder image in simulation mode
            try:
                from PIL import Image, ImageDraw
                img = Image.new("RGB", (640, 480), color=(15, 23, 42))
                d = ImageDraw.Draw(img)
                d.text((50, 240), f"[Jarvis Simulation Image - Camera {camera_id}]", fill=(0, 255, 204))
                img.save(output_path)
                return {
                    "success": True,
                    "mode": "simulated",
                    "file_path": output_path,
                    "camera": "Front" if camera_id == 1 else "Rear",
                    "message": f"[Simulation] Captured photo from Camera {camera_id} saved to {output_path}."
                }
            except Exception as e:
                return {"success": True, "mode": "simulated", "file_path": output_path, "message": str(e)}

        cmd = ["termux-camera-photo", "-c", str(camera_id), output_path]
        code, _, stderr = self._run_cmd(cmd, timeout=15)
        if code == 0 and os.path.exists(output_path):
            return {
                "success": True,
                "file_path": output_path,
                "camera": "Front" if camera_id == 1 else "Rear",
                "message": f"Captured photo using Camera {camera_id}."
            }
        return {"success": False, "error": stderr or "Failed to capture photo."}

    def open_url(self, url: str) -> Dict[str, Any]:
        """Open a web URL or deep link using default Android intent."""
        if not self._is_native():
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Opened URL: {url}"}

        code, _, stderr = self._run_cmd(["termux-open-url", url])
        if code == 0:
            return {"success": True, "message": f"Opened {url} in Android."}
        return {"success": False, "error": stderr or "Failed to open URL."}

termux_api = TermuxAPIController()
