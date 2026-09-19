import datetime
import subprocess
from typing import Dict, Any

class WebAndSystemTools:
    """Provides web search, live time/date, and system execution tools."""

    @staticmethod
    def get_current_time_and_date() -> Dict[str, Any]:
        """Get current local date, time, and day of week."""
        now = datetime.datetime.now()
        return {
            "success": True,
            "datetime": now.strftime("%Y-%m-%d %H:%M:%S"),
            "time": now.strftime("%I:%M %p"),
            "date": now.strftime("%A, %B %d, %Y"),
            "message": f"It is currently {now.strftime('%I:%M %p on %A, %B %d, %Y')}."
        }

    @staticmethod
    def search_web(query: str, max_results: int = 4) -> Dict[str, Any]:
        """Perform a live web search for fresh information using DuckDuckGo."""
        try:
            try:
                from ddgs import DDGS
            except ImportError:
                from duckduckgo_search import DDGS

            results = []
            with DDGS() as ddgs:
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "snippet": r.get("body", ""),
                        "url": r.get("href", "")
                    })

            if results:
                return {"success": True, "query": query, "results": results}
            return {"success": False, "query": query, "message": "No results found."}
        except Exception as e:
            return {"success": False, "query": query, "error": str(e)}

    @staticmethod
    def run_shell(command: str, timeout: int = 15) -> Dict[str, Any]:
        """Execute a custom shell command safely in Termux."""
        try:
            res = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout
            )
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout.strip(),
                "stderr": res.stderr.strip(),
                "returncode": res.returncode
            }
        except subprocess.TimeoutExpired:
            return {"success": False, "error": "Command timed out."}
        except Exception as e:
            return {"success": False, "error": str(e)}

web_tools = WebAndSystemTools()
