from typing import Dict, Any, Callable
from actions import termux_api, adb_controller, web_tools

# Tool definitions compatible with both google-genai and google-generativeai SDKs
TOOL_DEFINITIONS = [
    {
        "name": "toggle_torch",
        "description": "Turn the phone's flashlight / torch ON or OFF.",
        "parameters": {
            "type": "object",
            "properties": {
                "state": {
                    "type": "boolean",
                    "description": "True to turn flashlight ON, False to turn OFF."
                }
            },
            "required": ["state"]
        }
    },
    {
        "name": "get_battery_status",
        "description": "Check current battery level percentage, charging status, temperature and health.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "vibrate_device",
        "description": "Vibrate the phone for tactile feedback.",
        "parameters": {
            "type": "object",
            "properties": {
                "duration_ms": {
                    "type": "integer",
                    "description": "Duration in milliseconds (default: 500)."
                }
            }
        }
    },
    {
        "name": "show_notification",
        "description": "Post a status bar notification on the Android device.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Title of the notification."
                },
                "content": {
                    "type": "string",
                    "description": "Body text of the notification."
                }
            },
            "required": ["title", "content"]
        }
    },
    {
        "name": "get_clipboard",
        "description": "Read copied text from the Android system clipboard.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "set_clipboard",
        "description": "Copy text to the Android system clipboard.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "The text to copy to clipboard."
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "take_camera_photo",
        "description": "Take a photo using the phone's camera. 0 for rear/back camera, 1 for front/selfie camera.",
        "parameters": {
            "type": "object",
            "properties": {
                "camera_id": {
                    "type": "integer",
                    "description": "0 for rear camera, 1 for front selfie camera."
                }
            }
        }
    },
    {
        "name": "open_url",
        "description": "Open a website or deep link on the Android device.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to open, e.g. https://google.com"
                }
            },
            "required": ["url"]
        }
    },
    {
        "name": "launch_app",
        "description": "Open or switch to an Android application by common name (e.g. 'whatsapp', 'youtube', 'chrome', 'spotify', 'settings', 'camera') or package name.",
        "parameters": {
            "type": "object",
            "properties": {
                "app_name": {
                    "type": "string",
                    "description": "Name of the app to launch."
                }
            },
            "required": ["app_name"]
        }
    },
    {
        "name": "tap_screen",
        "description": "Tap at specific (x, y) coordinates on the Android touch screen.",
        "parameters": {
            "type": "object",
            "properties": {
                "x": {"type": "integer", "description": "Horizontal X coordinate."},
                "y": {"type": "integer", "description": "Vertical Y coordinate."}
            },
            "required": ["x", "y"]
        }
    },
    {
        "name": "swipe_screen",
        "description": "Swipe or scroll on screen from start coordinates (x1, y1) to end coordinates (x2, y2).",
        "parameters": {
            "type": "object",
            "properties": {
                "x1": {"type": "integer", "description": "Start X coordinate."},
                "y1": {"type": "integer", "description": "Start Y coordinate."},
                "x2": {"type": "integer", "description": "End X coordinate."},
                "y2": {"type": "integer", "description": "End Y coordinate."},
                "duration_ms": {"type": "integer", "description": "Swipe duration in ms (default 300)."}
            },
            "required": ["x1", "y1", "x2", "y2"]
        }
    },
    {
        "name": "type_text",
        "description": "Type text into the currently focused Android input field.",
        "parameters": {
            "type": "object",
            "properties": {
                "text": {
                    "type": "string",
                    "description": "Text to type."
                }
            },
            "required": ["text"]
        }
    },
    {
        "name": "press_key",
        "description": "Press an Android hardware key (home, back, power, volume_up, volume_down, enter).",
        "parameters": {
            "type": "object",
            "properties": {
                "key_name": {
                    "type": "string",
                    "description": "Key name: 'home', 'back', 'power', 'volume_up', 'volume_down', 'enter'."
                }
            },
            "required": ["key_name"]
        }
    },
    {
        "name": "capture_screenshot",
        "description": "Take a screenshot of the phone screen for visual inspection.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "get_current_time_and_date",
        "description": "Get current time, date, and day of week.",
        "parameters": {
            "type": "object",
            "properties": {}
        }
    },
    {
        "name": "search_web",
        "description": "Search the web for up-to-date information, news, or answers.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query."
                }
            },
            "required": ["query"]
        }
    }
]

# Dispatcher mapping tool names to python execution functions
TOOL_MAP: Dict[str, Callable] = {
    "toggle_torch": lambda args: termux_api.toggle_torch(args.get("state", False)),
    "get_battery_status": lambda args: termux_api.get_battery_status(),
    "vibrate_device": lambda args: termux_api.vibrate(args.get("duration_ms", 500)),
    "show_notification": lambda args: termux_api.show_notification(args.get("title", ""), args.get("content", "")),
    "get_clipboard": lambda args: termux_api.get_clipboard(),
    "set_clipboard": lambda args: termux_api.set_clipboard(args.get("text", "")),
    "take_camera_photo": lambda args: termux_api.take_camera_photo(args.get("camera_id", 0)),
    "open_url": lambda args: termux_api.open_url(args.get("url", "")),
    "launch_app": lambda args: adb_controller.launch_app(args.get("app_name", "")),
    "tap_screen": lambda args: adb_controller.tap(args.get("x", 0), args.get("y", 0)),
    "swipe_screen": lambda args: adb_controller.swipe(
        args.get("x1", 0), args.get("y1", 0), args.get("x2", 0), args.get("y2", 0), args.get("duration_ms", 300)
    ),
    "type_text": lambda args: adb_controller.type_text(args.get("text", "")),
    "press_key": lambda args: adb_controller.press_key(args.get("key_name", "home")),
    "capture_screenshot": lambda args: adb_controller.capture_screenshot(),
    "get_current_time_and_date": lambda args: web_tools.get_current_time_and_date(),
    "search_web": lambda args: web_tools.search_web(args.get("query", ""))
}

def execute_tool(name: str, args: Dict[str, Any]) -> Dict[str, Any]:
    """Execute a tool function by name."""
    if name not in TOOL_MAP:
        return {"error": f"Tool '{name}' is not recognized."}
    try:
        return TOOL_MAP[name](args)
    except Exception as e:
        return {"error": f"Tool execution failed: {str(e)}"}
