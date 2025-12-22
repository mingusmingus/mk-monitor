from typing import List, Generator, Union
import asyncio
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.text import Text
from rich.live import Live
from rich.columns import Columns
from rich.layout import Layout

# Import GandalfTarget for type hinting
try:
    from cli.session import GandalfTarget
except ImportError:
    pass

console = Console()

class GandalfUI:
    def __init__(self):
        self.console = console

    def show_banner(self):
        self.console.clear()
        # Gandalf ASCII Art
        ascii_art_str = r"""
                           .
                 /^\     .
            /\   "V"
           /__\   I      O  o
          //..\\  I     .
          \].`[/  I
          /l\/j\  (]    .  O
         /. ~~ ,\/I          .
         \\L__j^\/I       o
          \/--v}  I     o   .
          |    |  I   _________
          |    |  I c(`       ')o
          |    l  I   \.     ,/
        _/j  L l\_!  _//^---^\\_
        """

        content = Text(ascii_art_str, style="cyan")
        content.append("\n")
        content.append("GANDALF CLI TOOL", style="bold cyan")
        content.append("\n")
        content.append("Network Diagnostics & Security Wizard", style="dim")

        panel = Panel(
            Align.center(content),
            border_style="cyan",
            title="v1.0.0",
        )
        self.console.print(panel)

    def print_dashboard(self, target: Union['GandalfTarget', None], provider: str, has_key: bool):
        """
        Prints the dashboard showing system status.
        """
        # Target Status
        if target:
            status_color = "green" if target.is_alive else "red"
            status_text = "ONLINE" if target.is_alive else "OFFLINE"
            target_info = f"[bold white]{target.ip}[/bold white]\n[{status_color}]{status_text}[/{status_color}]"
            target_title = f"[cyan]Target ({target.user})[/cyan]"
        else:
            target_info = "[dim]No target selected[/dim]"
            target_title = "[dim]Target[/dim]"

        target_panel = Panel(Align.center(target_info), title=target_title, border_style="cyan")

        # AI Provider Status
        provider_info = f"[bold white]{provider.upper()}[/bold white]"
        provider_panel = Panel(Align.center(provider_info), title="[magenta]AI Provider[/magenta]", border_style="magenta")

        # Key Status
        key_color = "green" if has_key else "red"
        key_text = "CONFIGURED" if has_key else "MISSING"
        key_info = f"[{key_color}]{key_text}[/{key_color}]"
        key_panel = Panel(Align.center(key_info), title="[yellow]API Key[/yellow]", border_style="yellow")

        # Grid Layout
        self.console.print(Columns([target_panel, provider_panel, key_panel], expand=True))

    def main_menu(self):
        """Displays the main menu options."""
        table = Table(show_header=False, box=None)
        table.add_column("Option", style="bold yellow", justify="right")
        table.add_column("Description", style="white")

        table.add_row("1", "Gestionar Objetivos (Router)")
        table.add_row("2", "Diagnóstico de Red")
        table.add_row("3", "Invocar Inteligencia Artificial")
        table.add_row("4", "Salir")

        self.console.print("\n[bold]Seleccione una opción:[/bold]")
        self.console.print(table)

    def print_targets_table(self, targets: List['GandalfTarget']):
        """
        Prints a table of managed targets.

        Args:
            targets: List of GandalfTarget objects.
        """
        table = Table(title="Objetivos Gestionados")

        table.add_column("ID", justify="right", style="cyan", no_wrap=True)
        table.add_column("IP", style="magenta")
        table.add_column("Usuario", style="green")
        table.add_column("Estado", justify="center")

        for idx, target in enumerate(targets, 1):
            # Check is_alive status
            status_emoji = "🟢" if target.is_alive else "🔴"

            table.add_row(
                str(idx),
                target.ip,
                target.user,
                status_emoji
            )

        self.console.print(table)

    def show_mined_data(self, data: dict):
        """
        Displays mined forensic data using Rich components.
        """
        if 'error' in data:
            self.console.print(f"[bold red]Error in data mining:[/bold red] {data['error']}")
            return

        # Top Panel: System Info
        res = data.get('resource', {})
        if isinstance(res, dict) and 'error' in res:
             sys_info = f"[red]Error fetching resource: {res['error']}[/red]"
        elif isinstance(res, dict):
            sys_info = f"[bold]Model:[/bold] {res.get('board-name', 'N/A')}\n" \
                       f"[bold]Version:[/bold] {res.get('version', 'N/A')}\n" \
                       f"[bold]CPU:[/bold] {res.get('cpu', 'N/A')}\n" \
                       f"[bold]Uptime:[/bold] {res.get('uptime', 'N/A')}\n" \
                       f"[bold]CPU Load:[/bold] {res.get('cpu-load', '0')}%"
        else:
            sys_info = "No resource data available."

        panel = Panel(sys_info, title="[cyan]System Resource[/cyan]", border_style="cyan")
        self.console.print(panel)

        # Table: IP Addresses
        table = Table(title="IP Addresses", show_header=True)
        table.add_column("Interface", style="cyan")
        table.add_column("Address", style="green")
        table.add_column("Network", style="dim")

        addresses = data.get('addresses', [])
        if isinstance(addresses, list):
            for addr in addresses:
                if isinstance(addr, dict) and 'error' in addr:
                     table.add_row("Error", addr['error'], "")
                elif isinstance(addr, dict):
                    table.add_row(addr.get('interface', 'N/A'), addr.get('address', 'N/A'), addr.get('network', 'N/A'))

        self.console.print(table)

        # Table: Logs
        log_table = Table(title="Recent Logs (Last 20)", show_header=True, box=None)
        log_table.add_column("Time", style="dim")
        log_table.add_column("Topics", style="magenta")
        log_table.add_column("Message", style="white")

        logs = data.get('logs', [])
        if isinstance(logs, list):
            for log in logs:
                if isinstance(log, dict):
                    log_table.add_row(log.get('time', ''), log.get('topics', ''), log.get('message', ''))

        self.console.print(log_table)

    async def stream_ai_response(self, text_input: Union[str, Generator]):
        """
        Simulates a typewriter effect for the AI response.
        If text_input is a string, it streams it character by character (or chunk by chunk).
        """
        self.console.print("\n[bold cyan]🤖 GANDALF AI:[/bold cyan]")

        message = ""
        # Create a Live display
        with Live(Text(message, style="cyan"), console=self.console, refresh_per_second=15) as live:
            if isinstance(text_input, str):
                # Simulate streaming for string
                for char in text_input:
                    message += char
                    live.update(Text(message, style="cyan"))
                    await asyncio.sleep(0.005) # Typewriter speed
            else:
                # If it's a generator (not implemented yet in core, but good for future)
                for chunk in text_input:
                    message += chunk
                    live.update(Text(message, style="cyan"))
                    await asyncio.sleep(0.01)

        self.console.print("\n")
