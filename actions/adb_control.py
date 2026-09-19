import os
import subprocess
import tempfile
from typing import Dict, Any, Optional
from core.config import settings

# Common package mappings for intuitive voice commands
APP_PACKAGES = {
    "whatsapp": "com.whatsapp",
    "youtube": "com.google.android.youtube",
    "chrome": "com.android.chrome",
    "browser": "com.android.chrome",
    "spotify": "com.spotify.music",
    "settings": "com.android.settings",
    "camera": "com.android.camera2",
    "maps": "com.google.android.apps.maps",
    "telegram": "org.telegram.messenger",
    "instagram": "com.instagram.android",
    "calculator": "com.google.android.calculator",
    "clock": "com.google.android.deskclock",
    "gmail": "com.google.android.gm",
    "messages": "com.google.android.apps.messaging",
    "phone": "com.google.android.dialer",
    "gallery": "com.google.android.apps.photos"
}

# Android Key Events
KEY_EVENTS = {
    "home": "3",
    "back": "4",
    "call": "5",
    "endcall": "6",
    "volume_up": "24",
    "volume_down": "25",
    "power": "26",
    "camera": "27",
    "menu": "82",
    "enter": "66",
    "tab": "61",
    "space": "62",
    "delete": "67",
    "wake": "224"
}

class ADBController:
    """Controls Android applications, touch interactions, and screen captures via ADB."""

    def __init__(self):
        self.target = settings.adb_target

    def _is_available(self) -> bool:
        return settings.has_adb and not settings.simulation_mode

    def _base_cmd(self) -> list[str]:
        cmd = ["adb"]
        if self.target:
            cmd.extend(["-s", self.target])
        return cmd

    def _run_shell(self, shell_args: list[str], timeout: int = 15) -> tuple[int, str, str]:
        if not self._is_available():
            return 0, "[Simulation Output]", ""
        try:
            full_cmd = self._base_cmd() + ["shell"] + shell_args
            res = subprocess.run(
                full_cmd,
                capture_output=True,
                text=True,
                timeout=timeout,
                shell=False
            )
            return res.returncode, res.stdout.strip(), res.stderr.strip()
        except FileNotFoundError:
            return 127, "", "ADB not found on PATH."
        except Exception as e:
            return 1, "", str(e)

    def connect(self, host_port: str) -> Dict[str, Any]:
        """Connect to Android device via Wireless ADB (e.g. 127.0.0.1:5555 or 192.168.1.X:5555)."""
        if not settings.has_adb:
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Connected to {host_port}."}

        try:
            res = subprocess.run(["adb", "connect", host_port], capture_output=True, text=True, timeout=10)
            self.target = host_port
            return {"success": "connected" in res.stdout.lower(), "output": res.stdout.strip()}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def launch_app(self, app_name: str) -> Dict[str, Any]:
        """Launch an Android application by its name (e.g. 'whatsapp', 'youtube', 'settings') or package name."""
        clean_name = app_name.lower().strip()
        package = APP_PACKAGES.get(clean_name, app_name)

        if not self._is_available():
            return {
                "success": True,
                "mode": "simulated",
                "app": app_name,
                "package": package,
                "message": f"[Simulation] Launched '{app_name}' ({package})."
            }

        # Use Android Monkey tool or intent to launch package main activity
        cmd = ["monkey", "-p", package, "-c", "android.intent.category.LAUNCHER", "1"]
        code, stdout, stderr = self._run_shell(cmd)
        if code == 0 and "No activities found" not in stdout:
            return {"success": True, "app": app_name, "package": package, "message": f"Successfully launched {app_name}."}
        
        # Fallback to am start
        code, stdout, stderr = self._run_shell(["am", "start", "-n", f"{package}/.MainActivity"])
        return {
            "success": code == 0,
            "app": app_name,
            "package": package,
            "message": f"Sent launch intent for {app_name}." if code == 0 else stderr
        }

    def tap(self, x: int, y: int) -> Dict[str, Any]:
        """Tap at the given (x, y) screen coordinates on the phone."""
        if not self._is_available():
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Tapped screen at ({x}, {y})."}

        code, _, stderr = self._run_shell(["input", "tap", str(x), str(y)])
        if code == 0:
            return {"success": True, "message": f"Tapped at coordinate ({x}, {y})."}
        return {"success": False, "error": stderr or "Failed to tap screen."}

    def swipe(self, x1: int, y1: int, x2: int, y2: int, duration_ms: int = 300) -> Dict[str, Any]:
        """Swipe / scroll on screen from (x1, y1) to (x2, y2)."""
        if not self._is_available():
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Swiped from ({x1}, {y1}) to ({x2}, {y2})."}

        code, _, stderr = self._run_shell(["input", "swipe", str(x1), str(y1), str(x2), str(y2), str(duration_ms)])
        if code == 0:
            return {"success": True, "message": f"Swiped from ({x1}, {y1}) to ({x2}, {y2})."}
        return {"success": False, "error": stderr or "Failed to swipe screen."}

    def type_text(self, text: str) -> Dict[str, Any]:
        """Type text into the currently focused Android input field."""
        if not self._is_available():
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Typed: '{text}'"}

        # ADB input text requires spaces to be escaped as %s
        escaped = text.replace(" ", "%s").replace("'", "\\'").replace('"', '\\"')
        code, _, stderr = self._run_shell(["input", "text", escaped])
        if code == 0:
            return {"success": True, "message": f"Typed text into active field."}
        return {"success": False, "error": stderr or "Failed to type text."}

    def press_key(self, key_name: str) -> Dict[str, Any]:
        """Press an Android hardware key (home, back, power, volume_up, volume_down, enter)."""
        clean_key = key_name.lower().strip()
        keycode = KEY_EVENTS.get(clean_key, clean_key)

        if not self._is_available():
            return {"success": True, "mode": "simulated", "message": f"[Simulation] Pressed key: {key_name}"}

        code, _, stderr = self._run_shell(["input", "keyevent", keycode])
        if code == 0:
            return {"success": True, "message": f"Pressed hardware key '{key_name}'."}
        return {"success": False, "error": stderr or f"Failed to press key {key_name}."}

    def capture_screenshot(self, output_path: Optional[str] = None) -> Dict[str, Any]:
        """Take a screenshot of the phone screen for visual analysis."""
        if output_path is None:
            output_path = os.path.join(tempfile.gettempdir(), "jarvis_screen.png")

        if not self._is_available():
            try:
                from PIL import Image, ImageDraw
                img = Image.new("RGB", (1080, 1920), color=(10, 15, 30))
                d = ImageDraw.Draw(img)
                d.text((100, 960), "[Jarvis Screen Capture Simulation]", fill=(0, 255, 204))
                img.save(output_path)
                return {"success": True, "mode": "simulated", "file_path": output_path, "message": "[Simulation] Screenshot captured."}
            except Exception as e:
                return {"success": True, "mode": "simulated", "file_path": output_path, "message": str(e)}

        device_tmp = "/sdcard/jarvis_screencap.png"
        code, _, stderr = self._run_shell(["screencap", "-p", device_tmp])
        if code != 0:
            return {"success": False, "error": stderr or "Failed to capture screenshot on device."}

        # Pull the screenshot to local Termux filesystem
        pull_cmd = self._base_cmd() + ["pull", device_tmp, output_path]
        try:
            res = subprocess.run(pull_cmd, capture_output=True, text=True, timeout=10)
            if res.returncode == 0 and os.path.exists(output_path):
                return {"success": True, "file_path": output_path, "message": "Screenshot captured successfully."}
            return {"success": False, "error": res.stderr.strip() or "Failed to transfer screenshot."}
        except Exception as e:
            return {"success": False, "error": str(e)}

adb_controller = ADBController()
