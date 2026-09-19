import os
import shutil
from pathlib import Path
from dataclasses import dataclass

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

@dataclass
class Settings:
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "").strip().strip("'").strip('"')
    gemini_model: str = os.getenv("GEMINI_MODEL", "gemini-2.0-flash").strip().strip("'").strip('"')
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8000"))
    simulation_mode: bool = os.getenv("SIMULATION_MODE", "false").lower() in ("true", "1", "yes")
    adb_target: str = os.getenv("ADB_TARGET", "")


    # Assistant Persona
    assistant_name: str = "JARVIS"
    system_prompt: str = (
        "You are JARVIS (Just A Rather Very Intelligent System), an advanced mobile AI personal assistant "
        "running autonomously on an Android smartphone via Termux. "
        "You have direct control over this mobile device through Termux:API and Android Wireless ADB. "
        "You can execute actions on the phone such as toggling the flashlight (torch), checking battery status, "
        "reading/setting clipboard, sending notifications, vibrating, taking photos with front/rear cameras, "
        "and interacting with Android apps (tapping coordinates, swiping, typing, launching apps like WhatsApp, YouTube, etc.). "
        "When the user requests an action on the phone, ALWAYS use your available tools to perform the task directly. "
        "Respond in a confident, concise, and courteous manner reminiscent of Tony Stark's JARVIS. "
        "Keep spoken responses punchy, direct, and conversational."
    )

    @property
    def is_termux(self) -> bool:
        """Detect whether we are running inside native Android Termux."""
        return "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")

    @property
    def has_termux_api(self) -> bool:
        """Check if termux-api CLI commands are available."""
        return shutil.which("termux-battery-status") is not None

    @property
    def has_adb(self) -> bool:
        """Check if adb executable is available."""
        return shutil.which("adb") is not None

settings = Settings()
