import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt
from rich import box

from core.config import settings
from core.brain import brain
from actions.termux_api import termux_api

console = Console()

BANNER = """
 [bold cyan]██╗  ██╗   █████╗ ██████╗ ██╗   ██╗██╗███████╗   ███╗   ███╗██╗     ██╗██╗   ██╗[/bold cyan]
 [bold cyan]██║  ██║  ██╔══██╗██╔══██╗██║   ██║██║██╔════╝   ████╗ ████║██║     ██║██║   ██║[/bold cyan]
 [bold cyan]███████║  ███████║██████╔╝██║   ██║██║███████╗   ██╔████╔██║██║     ██║██║   ██║[/bold cyan]
 [bold cyan]██╔══██║  ██╔══██║██╔══██╗╚██╗ ██╔╝██║╚════██║   ██║╚██╔╝██║██║     ██║╚██╗ ██╔╝[/bold cyan]
 [bold cyan]██║  ██║  ██║  ██║██║  ██║ ╚████╔╝ ██║███████║██╗██║ ╚═╝ ██║███████╗██║ ╚████╔╝ [/bold cyan]
 [dim cyan]╚═╝  ╚═╝  ╚═╝  ╚═╝╚═╝  ╚═╝  ╚═══╝  ╚═╝╚══════╝╚═╝╚═╝     ╚═╝╚══════╝╚═╝  ╚═══╝  [/dim cyan]
 [bold yellow]         -- MARK LIV MOBILE (Android Termux Autonomous Assistant) -- [/bold yellow]
"""

def print_header():
    console.print(BANNER)
    
    # System status table
    table = Table(box=box.ROUNDED, show_header=False, expand=True)
    table.add_column("Key", style="bold cyan", width=16)
    table.add_column("Val", style="bold white")

    battery = termux_api.get_battery_status()
    batt_str = f"{battery.get('percentage', '--')}% ({battery.get('status', 'N/A')})"
    
    table.add_row("Platform", "Android Termux" if settings.is_termux else "Host / Simulation Mode")
    table.add_row("AI Model", settings.gemini_model)
    table.add_row("Battery", batt_str)
    table.add_row("Termux:API", "[green]Available[/green]" if settings.has_termux_api else "[yellow]Simulated[/yellow]")
    table.add_row("ADB Status", "[green]Ready[/green]" if settings.has_adb else "[yellow]Simulated[/yellow]")

    console.print(Panel(table, title="[bold cyan]SYSTEM DIAGNOSTICS[/bold cyan]", border_style="cyan"))
    console.print("[dim]Type your command or query. Type 'exit' or 'quit' to close.[/dim]\n")

def run_cli():
    print_header()

    while True:
        try:
            user_input = Prompt.ask("[bold cyan]Jarvis[/bold cyan] [bold white]❯[/bold white]").strip()
            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit", "q"):
                console.print("[bold cyan]JARVIS:[/bold cyan] Shutting down systems. Have a good day, sir.")
                break

            with console.status("[bold yellow]Processing with neural core...", spinner="dots"):
                result = brain.ask(user_input)

            # Display response
            reply = result.get("response", "Request processed, sir.")
            console.print(Panel(reply, title="[bold cyan]JARVIS[/bold cyan]", border_style="cyan"))

            # Display any actions executed
            actions = result.get("actions", [])
            if actions:
                for act in actions:
                    tool_name = act.get("tool", "Action")
                    console.print(f"[bold green]⚡ Executed:[/bold green] [yellow]{tool_name}[/yellow]")

            # Speak via Termux TTS if on Android
            if settings.is_termux and settings.has_termux_api:
                termux_api.speak_tts(reply)

        except (KeyboardInterrupt, EOFError):
            console.print("\n[bold cyan]JARVIS:[/bold cyan] Goodbye, sir.")
            break
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] {e}")

if __name__ == "__main__":
    run_cli()
