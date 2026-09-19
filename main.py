import argparse
import sys
import uvicorn
from core.config import settings

def main():
    parser = argparse.ArgumentParser(description="JARVIS Mobile - Mark-LIV for Android Termux")
    parser.add_argument("--cli", action="store_true", help="Launch interactive Terminal UI (CLI mode)")
    parser.add_argument("--host", type=str, default=settings.host, help=f"Server host (default: {settings.host})")
    parser.add_argument("--port", type=int, default=settings.port, help=f"Server port (default: {settings.port})")
    args = parser.parse_args()

    if args.cli:
        from cli import run_cli
        run_cli()
    else:
        print("=" * 65)
        print("   JARVIS MOBILE // MARK-LIV (Android Termux Edition)")
        print(f"   Starting Mobile Web HUD on http://localhost:{args.port}")
        print("   Access this URL in your mobile browser (e.g. Chrome / Firefox).")
        print("   Use --cli to run directly in the Termux terminal.")
        print("=" * 65)
        uvicorn.run("server:app", host=args.host, port=args.port, reload=False)

if __name__ == "__main__":
    main()
