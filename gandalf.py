#!/usr/bin/env python3
import sys
import os
import asyncio
import getpass
from aioconsole import ainput

# Import Hack: Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# Now we can import from cli
from cli.ui import GandalfUI
from cli.session import GandalfSession
from cli.core import async_ping, async_mine_data, GandalfBrain

async def ainput_password(prompt: str) -> str:
    """Async wrapper for getpass to read password securely."""
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, getpass.getpass, prompt)

async def main():
    ui = GandalfUI()
    session = GandalfSession()
    brain = GandalfBrain()

    # Default provider
    current_provider = "deepseek"

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

                # Get Password (using getpass implicitly via ainput_password logic if we want consistency,
                # but instruction only demanded it for API Key. existing code used ainput.
                # I will leave existing code for router password as is unless asked,
                # but instruction said "ainput (input con máscara password)" specifically for API Key?
                # "Verifica si hay API Key. Si no, pídela con ainput (input con máscara password) e inyéctala."
                # So I only apply it to API Key.
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
                target = session.active_target
                if not target:
                    ui.console.print("[red]Error: No hay objetivo seleccionado. Use Opción 1 primero.[/red]")
                    await asyncio.sleep(1)
                    continue

                ui.console.print(f"\n[cyan]⛏️ Extrayendo evidencia forense del equipo {target.ip}...[/cyan]")

                try:
                    with ui.console.status(f"[bold green]Conectando a {target.ip}:{target.port}...[/bold green]", spinner="dots"):
                        # Now passing port correctly to async_mine_data
                        data = await async_mine_data(target.ip, target.user, target.password, port=target.port)
                        session.set_last_mined_data(data)

                    ui.console.print("[green]✓ Extracción completada con éxito.[/green]\n")
                    ui.show_mined_data(data)

                except Exception as e:
                    ui.console.print(f"\n[red]Error durante la extracción: {e}[/red]")

                await asyncio.sleep(1.5)

            elif choice == "3":
                # AI Sub-menu
                while True:
                    ui.console.print(f"\n[bold cyan]🧠 Inteligencia Artificial ({current_provider})[/bold cyan]")
                    ui.console.print("1. Auditoría Automática")
                    ui.console.print("2. Consulta Libre")
                    ui.console.print("3. Cambiar Proveedor")
                    ui.console.print("4. Volver al menú principal")

                    sub_choice = await ainput("\nIA > ")
                    sub_choice = sub_choice.strip()

                    if sub_choice == "4":
                        break

                    if sub_choice == "3":
                        ui.console.print("[yellow]Proveedores disponibles: deepseek, gemini[/yellow]")
                        new_prov = await ainput("Nombre del proveedor: ")
                        new_prov = new_prov.strip().lower()
                        if new_prov in ["deepseek", "gemini"]:
                            current_provider = new_prov
                            ui.console.print(f"[green]Proveedor cambiado a {current_provider}[/green]")
                        else:
                            ui.console.print("[red]Proveedor no válido[/red]")
                        continue

                    # Ensure we have a target and data
                    target = session.active_target
                    if not target:
                        ui.console.print("[red]Error: No hay objetivo seleccionado. Use Opción 1 del menú principal.[/red]")
                        await asyncio.sleep(1)
                        break # Go back to main menu

                    # Ensure API Key
                    if not brain.check_key(current_provider):
                        ui.console.print(f"[yellow]⚠️ No se detectó API Key para {current_provider}.[/yellow]")
                        # Use secure input
                        key = await ainput_password(f"Ingrese API Key para {current_provider}: ")
                        if key.strip():
                            brain.setup_key(current_provider, key.strip())
                        else:
                            ui.console.print("[red]Key requerida para continuar.[/red]")
                            continue

                    # Ensure Data
                    data = session.last_mined_data
                    if not data:
                        ui.console.print("[yellow]Datos no disponibles en caché. Iniciando minería automática...[/yellow]")
                        try:
                            with ui.console.status(f"[bold green]Conectando a {target.ip}...[/bold green]", spinner="dots"):
                                data = await async_mine_data(target.ip, target.user, target.password, port=target.port)
                                session.set_last_mined_data(data)
                        except Exception as e:
                            ui.console.print(f"[red]Falló la minería de datos: {e}[/red]")
                            continue

                    # Prepare Prompt
                    prompt = ""
                    if sub_choice == "1":
                        prompt = "Realiza una auditoría de seguridad completa basada en los logs, recursos y direcciones IP proporcionados. Identifica vulnerabilidades críticas."
                        ui.console.print("[cyan]Iniciando Auditoría Automática...[/cyan]")
                    elif sub_choice == "2":
                        prompt = await ainput("Escriba su consulta a la IA: ")
                        if not prompt.strip():
                            continue
                    else:
                        continue

                    # Send to AI
                    try:
                        with ui.console.status("[bold cyan]Consultando al Oráculo...[/bold cyan]", spinner="earth"):
                            response = await brain.ask(data, prompt, provider=current_provider)

                        # Handle Response
                        if response.get("status") == "WARNING" and "unavailable" in response.get("summary", "").lower():
                             ui.console.print(f"[red]Error de la IA: {response.get('technical_analysis')}[/red]")
                        else:
                            # We prefer 'technical_analysis' for the main body
                            answer = response.get("technical_analysis", "")
                            if not answer:
                                answer = str(response) # Fallback

                            await ui.stream_ai_response(answer)

                            # Also show summary if present and distinct
                            summary = response.get("summary")
                            if summary and summary not in answer:
                                ui.console.print(f"[bold]Resumen:[/bold] {summary}")

                    except Exception as e:
                         ui.console.print(f"[red]Error crítico comunicando con la IA: {e}[/red]")
                         import traceback
                         traceback.print_exc()

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
