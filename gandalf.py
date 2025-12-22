#!/usr/bin/env python3
import sys
import os
import asyncio
from aioconsole import ainput

# Import Hack: Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# Now we can import from cli
from cli.ui import GandalfUI
from cli.session import GandalfSession
from cli.core import async_ping

async def main():
    ui = GandalfUI()
    session = GandalfSession()

    ui.show_banner()

    while True:
        ui.main_menu()
        try:
            # Non-blocking input
            choice = await ainput("\n> ")
            choice = choice.strip()

            if choice == "1":
                ui.console.print("\n[bold cyan]Nuevo Objetivo[/bold cyan]")

                # Get IP
                ip = await ainput("IP Address: ")
                ip = ip.strip()
                if not ip:
                    ui.console.print("[red]IP no puede estar vacía.[/red]")
                    continue

                # Get User
                user = await ainput("User: ")
                user = user.strip()
                if not user:
                    ui.console.print("[red]Usuario no puede estar vacío.[/red]")
                    continue

                # Get Password
                password = await ainput("Password: ")
                # Password can be empty sometimes, so we allow it but strip it
                password = password.strip()

                # Verify Network Reachability
                with ui.console.status("[bold green]🔍 Verificando alcance de red...[/bold green]", spinner="dots"):
                    is_reachable = await async_ping(ip)

                if is_reachable:
                    ui.console.print(f"[green]✓ Host {ip} es alcanzable.[/green]")
                else:
                    ui.console.print(f"[red]✗ Host {ip} no responde al ping.[/red]")

                # Add to session
                session.add_target(ip, user, password, is_alive=is_reachable)

                # Show Targets Table
                ui.console.print("\n") # Spacing
                ui.print_targets_table(session.targets)

                await asyncio.sleep(1)

            elif choice == "2":
                ui.console.print("\n[yellow][TODO] Implementar en Fase 2: Diagnóstico de Red[/yellow]")
                await asyncio.sleep(1.5)
            elif choice == "3":
                ui.console.print("\n[yellow][TODO] Implementar en Fase 2: Invocar IA[/yellow]")
                await asyncio.sleep(1.5)
            elif choice == "4":
                ui.console.print("\n[bold cyan]¡Corred, insensatos![/bold cyan]")
                break
            else:
                ui.console.print("\n[red]Opción inválida. Intente de nuevo.[/red]")
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            break
        except Exception as e:
            ui.console.print(f"\n[red]Error inesperado: {e}[/red]")
            import traceback
            traceback.print_exc()
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        # Run the async main loop
        asyncio.run(main())
    except KeyboardInterrupt:
        # Use simple print here as UI might not be initialized or to be safe during exit
        print("\n\n\033[1;36mEl Mago se desvanece... (Interrupción de usuario)\033[0m")
        sys.exit(0)
