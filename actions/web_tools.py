import datetime
import subprocess
import requests
from typing import Dict, Any

class WebAndSystemTools:
    """Provides web search, live time/date, and system execution tools.
    100% pure Python - zero Rust or complex binaries.
    """

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
        """Perform a web search using DuckDuckGo Instant Answers API via requests."""
        try:
            url = f"https://api.duckduckgo.com/?q={requests.utils.quote(query)}&format=json"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                results = []
                abstract = data.get("AbstractText", "")
                if abstract:
                    results.append({"title": data.get("Heading", "Summary"), "snippet": abstract, "url": data.get("AbstractURL", "")})

                topics = data.get("RelatedTopics", [])
                for t in topics[:max_results]:
                    if isinstance(t, dict) and "Text" in t:
                        results.append({"title": "Topic", "snippet": t["Text"], "url": t.get("FirstURL", "")})

                if results:
                    return {"success": True, "query": query, "results": results}

            return {"success": True, "query": query, "results": [{"snippet": f"No summary found for '{query}', but neural core knowledge is active."}]}
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
