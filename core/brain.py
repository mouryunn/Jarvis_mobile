import os
import json
import logging
import base64
from typing import Dict, Any, List, Optional
import requests

from core.config import settings
from core.tools_schema import TOOL_DEFINITIONS, execute_tool

logger = logging.getLogger("jarvis.brain")

class JarvisBrain:
    """The AI cognitive core of Jarvis-Mobile, powered by Google Gemini REST API with tool execution.
    100% Pure Python - Zero Rust or complex C dependencies required!
    """

    def __init__(self):
        self.api_key = settings.gemini_api_key
        self.model_name = settings.gemini_model
        self.conversation_history: List[Dict[str, Any]] = []

    def ask(self, user_prompt: str, image_path: Optional[str] = None) -> Dict[str, Any]:
        """Process a user query, handle tool calling, and return spoken response."""
        if not self.api_key:
            return self._offline_response(user_prompt)

        user_parts = []
        if image_path and os.path.exists(image_path):
            try:
                with open(image_path, "rb") as img_f:
                    b64_data = base64.b64encode(img_f.read()).decode("utf-8")
                user_parts.append({
                    "inline_data": {
                        "mime_type": "image/jpeg",
                        "data": b64_data
                    }
                })
            except Exception as e:
                logger.error(f"Failed to read image: {e}")

        user_parts.append({"text": user_prompt})

        # Append user message to history
        self.conversation_history.append({"role": "user", "parts": user_parts})

        # Limit conversation history to last 12 turns to conserve memory
        if len(self.conversation_history) > 12:
            self.conversation_history = self.conversation_history[-12:]

        candidate_models = [
            self.model_name,
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro"
        ]
        # Deduplicate preserving order
        models_to_try = []
        for m in candidate_models:
            if m and m not in models_to_try:
                models_to_try.append(m)

        executed_actions = []
        resp = None

        for model in models_to_try:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={self.api_key}"
            headers = {"Content-Type": "application/json"}
            payload = {
                "system_instruction": {
                    "parts": [{"text": settings.system_prompt}]
                },
                "contents": self.conversation_history,
                "tools": [{"function_declarations": TOOL_DEFINITIONS}]
            }

            try:
                r = requests.post(url, headers=headers, json=payload, timeout=25)
                if r.status_code == 404:
                    logger.warning(f"Model '{model}' returned 404. Trying next supported model...")
                    continue
                resp = r
                self.model_name = model  # Remember working model
                break
            except Exception as e:
                logger.error(f"Request failed for model {model}: {e}")

        if not resp:
            return self._fallback_action_handler(user_prompt, "All Gemini models returned 404")

        try:
            if resp.status_code != 200:
                logger.error(f"Gemini API returned status {resp.status_code}: {resp.text}")
                return self._fallback_action_handler(user_prompt, f"Status {resp.status_code}")

            data = resp.json()
            candidates = data.get("candidates", [])
            if not candidates:
                return {"success": False, "response": "No response received from neural core, sir."}

            candidate = candidates[0]
            content = candidate.get("content", {})
            parts = content.get("parts", [])

            reply_text = ""
            function_calls = []

            for part in parts:
                if "text" in part:
                    reply_text += part["text"]
                if "functionCall" in part:
                    function_calls.append(part["functionCall"])

            # If Gemini called one or more tools, execute them and send results back
            if function_calls:
                self.conversation_history.append({"role": "model", "parts": parts})
                fn_response_parts = []

                for fc in function_calls:
                    fn_name = fc.get("name")
                    fn_args = fc.get("args", {})
                    logger.info(f"Executing tool: {fn_name} with args: {fn_args}")

                    tool_res = execute_tool(fn_name, fn_args)
                    executed_actions.append({"tool": fn_name, "args": fn_args, "result": tool_res})

                    fn_response_parts.append({
                        "functionResponse": {
                            "name": fn_name,
                            "response": {"output": tool_res}
                        }
                    })

                self.conversation_history.append({
                    "role": "function",
                    "parts": fn_response_parts
                })

                # Follow up request to generate final spoken answer
                followup_payload = {
                    "system_instruction": {"parts": [{"text": settings.system_prompt}]},
                    "contents": self.conversation_history,
                    "tools": [{"function_declarations": TOOL_DEFINITIONS}]
                }

                followup_resp = requests.post(url, headers=headers, json=followup_payload, timeout=25)
                if followup_resp.status_code == 200:
                    f_data = followup_resp.json()
                    f_candidates = f_data.get("candidates", [])
                    if f_candidates:
                        f_parts = f_candidates[0].get("content", {}).get("parts", [])
                        reply_text = "".join(p.get("text", "") for p in f_parts)
                        self.conversation_history.append({"role": "model", "parts": f_parts})

            if not reply_text:
                reply_text = "Action completed, sir."

            return {
                "success": True,
                "response": reply_text.strip(),
                "actions": executed_actions
            }

        except Exception as e:
            logger.error(f"Gemini REST error: {e}", exc_info=True)
            return self._fallback_action_handler(user_prompt, str(e))

    def _fallback_action_handler(self, prompt: str, error_msg: str) -> Dict[str, Any]:
        """Simple rule-based fallback when Gemini API encounters network or key issues."""
        p = prompt.lower()
        actions = []

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
            response_text = f"I encountered an issue connecting to Gemini ({error_msg}). Hardware actions are still operational."

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
            reply = "Screenshot captured."
        elif "camera" in p or "photo" in p:
            res = execute_tool("take_camera_photo", {"camera_id": 0})
            actions.append({"tool": "take_camera_photo", "result": res})
            reply = "Photo captured."
        else:
            reply = "JARVIS Mobile online. Please set your GEMINI_API_KEY in the .env file."

        return {
            "success": True,
            "response": reply,
            "actions": actions,
            "offline_mode": True
        }

brain = JarvisBrain()
