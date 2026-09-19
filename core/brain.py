import os
import json
import logging
from typing import Dict, Any, List, Optional
from core.config import settings
from core.tools_schema import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger("jarvis.brain")

class JarvisBrain:
    """The AI cognitive core of Jarvis-Mobile, powered by Google Gemini with tool execution."""

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model
        self.client = None
        self.chat = None
        self.conversation_history: List[Dict[str, Any]] = []
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.warning("GEMINI_API_KEY is not set. Brain will run in offline simulation mode.")
            return

        try:
            import google.generativeai as genai
            genai.configure(api_key=self.api_key)

            # Define tools for Google Generative AI
            # GenerativeModel supports passing Python functions or tool dicts
            from core.tools_schema import TOOL_MAP

            # Wrap each function into a callable with docstring and annotations for automatic schema extraction
            self.tools = list(TOOL_MAP.values())

            self.model = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=settings.system_prompt,
                tools=self.tools
            )
            self.chat = self.model.start_chat(enable_automatic_function_calling=True)
            logger.info(f"Jarvis brain initialized with model: {self.model_name}")
        except Exception as e:
            logger.error(f"Failed to initialize Gemini client: {e}")
            self.chat = None

    def ask(self, user_prompt: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query, handle function calls, and return the final spoken response and executed actions."""
        # Check if API key is present
        if not self.api_key or not self.chat:
            return self._offline_response(user_prompt)

        executed_actions = []

        try:
            # If an image is provided (camera snapshot or screencap), send multimodal content
            if image_path and os.path.exists(image_path):
                from PIL import Image
                img = Image.open(image_path)
                response = self.chat.send_message([user_prompt, img])
            else:
                response = self.chat.send_message(user_prompt)

            # Check for function call parts in the history or candidate response to log executed actions
            if hasattr(response, "candidates") and response.candidates:
                for candidate in response.candidates:
                    if hasattr(candidate, "content") and candidate.content:
                        for part in candidate.content.parts:
                            if hasattr(part, "function_call") and part.function_call:
                                fn_name = part.function_call.name
                                fn_args = dict(part.function_call.args)
                                executed_actions.append({"tool": fn_name, "args": fn_args})

            reply_text = response.text.strip() if response.text else "Done, sir."

            return {
                "success": True,
                "response": reply_text,
                "actions": executed_actions
            }

        except Exception as e:
            logger.error(f"Gemini processing error: {e}", exc_info=True)
            # Try a direct keyword fallback if network or tool calling fails
            return self._fallback_action_handler(user_prompt, str(e))

    def _fallback_action_handler(self, prompt: str, error_msg: str) -> Dict[str, Any]:
        """Simple rule-based fallback when Gemini API encounters rate limits or errors."""
        p = prompt.lower()
        actions = []
        response_text = ""

        if "torch" in p or "flashlight" in p:
            turn_on = "on" in p or "enable" in p or "start" in p
            res = execute_tool("toggle_torch", {"state": turn_on})
            actions.append({"tool": "toggle_torch", "result": res})
            response_text = f"Flashlight turned {'ON' if turn_on else 'OFF'}, sir."
        elif "battery" in p:
            res = execute_tool("get_battery_status", {})
            actions.append({"tool": "get_battery_status", "result": res})
            pct = res.get("percentage", 85)
            response_text = f"Battery level is currently at {pct}%, sir."
        elif "time" in p or "date" in p:
            res = execute_tool("get_current_time_and_date", {})
            actions.append({"tool": "get_current_time_and_date", "result": res})
            response_text = res.get("message", "Time updated, sir.")
        elif "vibrate" in p:
            res = execute_tool("vibrate_device", {"duration_ms": 500})
            actions.append({"tool": "vibrate_device", "result": res})
            response_text = "Vibrating device now, sir."
        elif "open" in p or "launch" in p:
            words = p.split()
            app_target = words[-1]
            res = execute_tool("launch_app", {"app_name": app_target})
            actions.append({"tool": "launch_app", "result": res})
            response_text = f"Opening {app_target} for you, sir."
        else:
            response_text = f"I encountered an issue connecting to my core intelligence ({error_msg}). Please verify your GEMINI_API_KEY."

        return {
            "success": True,
            "response": response_text,
            "actions": actions,
            "fallback": True
        }

    def _offline_response(self, prompt: str) -> Dict[str, Any]:
        """Offline simulation mode when GEMINI_API_KEY is not yet configured."""
        p = prompt.lower()
        actions = []
        
        if "torch" in p or "flashlight" in p:
            turn_on = "off" not in p
            res = execute_tool("toggle_torch", {"state": turn_on})
            actions.append({"tool": "toggle_torch", "result": res})
            reply = f"Flashlight has been turned {'ON' if turn_on else 'OFF'}, sir."
        elif "battery" in p:
            res = execute_tool("get_battery_status", {})
            actions.append({"tool": "get_battery_status", "result": res})
            reply = f"Battery status is {res.get('percentage', 88)}%, currently {res.get('status', 'CHARGING')}."
        elif "time" in p or "date" in p:
            res = execute_tool("get_current_time_and_date", {})
            actions.append({"tool": "get_current_time_and_date", "result": res})
            reply = res.get("message", "")
        elif "open" in p or "launch" in p:
            app = p.replace("open", "").replace("launch", "").strip()
            res = execute_tool("launch_app", {"app_name": app})
            actions.append({"tool": "launch_app", "result": res})
            reply = f"Launching {app} on your Android device."
        elif "vibrate" in p:
            res = execute_tool("vibrate_device", {"duration_ms": 500})
            actions.append({"tool": "vibrate_device", "result": res})
            reply = "Vibrating device."
        elif "screenshot" in p or "screen" in p:
            res = execute_tool("capture_screenshot", {})
            actions.append({"tool": "capture_screenshot", "result": res})
            reply = "Screenshot captured and saved to temporary storage."
        elif "camera" in p or "photo" in p:
            res = execute_tool("take_camera_photo", {"camera_id": 0})
            actions.append({"tool": "take_camera_photo", "result": res})
            reply = "Photo captured using device camera."
        else:
            reply = (
                "JARVIS Mobile online. Please set your GEMINI_API_KEY in the .env file to enable full "
                "conversational reasoning. Hardware controls (torch, battery, app launching) are fully operational."
            )

        return {
            "success": True,
            "response": reply,
            "actions": actions,
            "offline_mode": True
        }

brain = JarvisBrain()
