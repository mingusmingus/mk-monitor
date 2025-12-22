from typing import List
from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.text import Text

# Import GandalfTarget for type hinting
# Note: In a real circular import scenario we might need TYPE_CHECKING
# but here GandalfSession imports nothing from ui, so it should be fine.
# If cli.session is not available yet, we skip or use string forward ref.
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
        # Top Panel: System Info
        res = data.get('resource', {})
        sys_info = f"[bold]Model:[/bold] {res.get('board-name', 'N/A')}\n" \
                   f"[bold]Version:[/bold] {res.get('version', 'N/A')}\n" \
                   f"[bold]CPU:[/bold] {res.get('cpu', 'N/A')}\n" \
                   f"[bold]Uptime:[/bold] {res.get('uptime', 'N/A')}\n" \
                   f"[bold]CPU Load:[/bold] {res.get('cpu-load', '0')}%"

        panel = Panel(sys_info, title="[cyan]System Resource[/cyan]", border_style="cyan")
        self.console.print(panel)

        # Table: IP Addresses
        table = Table(title="IP Addresses", show_header=True)
        table.add_column("Interface", style="cyan")
        table.add_column("Address", style="green")
        table.add_column("Network", style="dim")

        for addr in data.get('addresses', []):
            table.add_row(addr.get('interface'), addr.get('address'), addr.get('network'))

        self.console.print(table)

        # Table: Logs
        log_table = Table(title="Recent Logs (Last 20)", show_header=True, box=None)
        log_table.add_column("Time", style="dim")
        log_table.add_column("Topics", style="magenta")
        log_table.add_column("Message", style="white")

        for log in data.get('logs', []):
            log_table.add_row(log.get('time'), log.get('topics'), log.get('message'))

        self.console.print(log_table)
