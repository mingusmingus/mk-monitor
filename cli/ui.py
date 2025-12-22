from rich.console import Console
from rich.panel import Panel
from rich.align import Align
from rich.table import Table
from rich.text import Text

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

        # Create a Text object to handle the ASCII art safely (no markup parsing)
        # We append the title and subtitle to this Text object or create a Group.
        # Here we construct a single centered renderable.

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
