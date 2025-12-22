#!/usr/bin/env python3
import sys
import os
import asyncio
from aioconsole import ainput

# Check initial requirements
try:
    import aiohttp
except ImportError:
    print("\n\033[1;31m[ERROR CRÍTICO]\033[0m La librería 'aiohttp' no está instalada.")
    print("Por favor, instale las dependencias con: pip install -r backend/requirements.txt\n")
    sys.exit(1)

try:
    import routeros_api
except ImportError:
    print("\n\033[1;31m[ERROR CRÍTICO]\033[0m La librería 'routeros_api' no está instalada.")
    print("Por favor, instale las dependencias con: pip install routeros_api\n")
    sys.exit(1)


# Import Hack: Add backend to sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.append(BACKEND_DIR)

# Now we can import from cli
from cli.ui import GandalfUI
from cli.session import GandalfSession
from cli.core import async_ping, async_mine_data, GandalfBrain, save_key_to_env, load_or_create_env, async_verify_connection
from backend.app.config import Config

async def main():
    ui = GandalfUI()
    session = GandalfSession()
    brain = GandalfBrain()

    # Load provider from Config/Env
    current_provider = Config.AI_ANALYSIS_PROVIDER if Config.AI_ANALYSIS_PROVIDER != 'auto' else 'deepseek'

    # If Config says "auto" but we want to know what it resolved to, we might check keys
    # But for now, let's default to what's in env or deepseek
    if not current_provider:
        current_provider = "deepseek"

    ui.show_banner()
    await asyncio.sleep(1)

    while True:
        # Dashboard Refresh
        has_key = brain.check_key(current_provider)
        ui.console.clear()
        ui.show_banner()
        ui.print_dashboard(session.active_target, current_provider, has_key)

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
                    await asyncio.sleep(1)
                    continue

                # Get User
                user = await ainput("User: ")
                user = user.strip()
                if not user:
                    ui.console.print("[red]Usuario no puede estar vacío.[/red]")
                    await asyncio.sleep(1)
                    continue

                password = await ainput("Password: ")
                password = password.strip()

                # Get Port (optional)
                port_input = await ainput("Port (8728): ")
                port = int(port_input.strip()) if port_input.strip() else 8728

                # Verify Network Reachability AND Auth
                is_reachable = False
                auth_success = False

                with ui.console.status("[bold green]🔍 Verificando conexión y credenciales...[/bold green]", spinner="dots"):
                     # Step 1: Ping
                    is_reachable = await async_ping(ip)

                    if not is_reachable:
                        ui.console.print(f"[red]✗ Host {ip} no responde al ping.[/red]")
                    else:
                        ui.console.print(f"[green]✓ Host {ip} responde al ping.[/green]")
                        # Step 2: Auth Check
                        auth_success = await async_verify_connection(ip, user, password, port)
                        if not auth_success:
                             ui.console.print("[red]Ping OK, pero Falló Autenticación (User/Pass incorrectos)[/red]")
                        else:
                             ui.console.print("[green]✓ Autenticación correcta.[/green]")

                if is_reachable and auth_success:
                     # Add to session only if fully verified
                    session.add_target(ip, user, password, port=port, is_alive=True)
                    # Show Targets Table
                    ui.console.print("\n") # Spacing
                    ui.print_targets_table(session.targets)
                else:
                    ui.console.print("[yellow]Objetivo no agregado debido a fallos de conexión o autenticación.[/yellow]")

                await asyncio.sleep(2)

            elif choice == "2":
                target = session.active_target
                if not target:
                    ui.console.print("[red]Error: No hay objetivo seleccionado. Use Opción 1 primero.[/red]")
                    await asyncio.sleep(2)
                    continue

                ui.console.print(f"\n[cyan]⛏️ Extrayendo evidencia forense del equipo {target.ip}...[/cyan]")

                try:
                    with ui.console.status(f"[bold green]Conectando a {target.ip}:{target.port}...[/bold green]", spinner="dots"):
                        # Now passing port correctly to async_mine_data
                        data = await async_mine_data(target.ip, target.user, target.password, port=target.port)
                        session.set_last_mined_data(data)

                    ui.console.print("[green]✓ Extracción completada con éxito.[/green]\n")
                    ui.show_mined_data(data)

                    # Wait for user acknowledgment
                    await ainput("\n[Presione Enter para continuar]")

                except Exception as e:
                    ui.console.print(f"\n[red]Error durante la extracción: {e}[/red]")
                    await asyncio.sleep(3)

            elif choice == "3":
                # Ensure we have a target and data
                target = session.active_target
                if not target:
                    ui.console.print("[red]Error: No hay objetivo seleccionado. Use Opción 1 del menú principal.[/red]")
                    await asyncio.sleep(2)
                    continue

                # Check Key
                if not has_key:
                     ui.console.print(f"[yellow]⚠️ No se detectó API Key para {current_provider}.[/yellow]")
                     ui.console.print("Por favor, use la opción 5 para configurar su API Key.")
                     await asyncio.sleep(2)
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
                        await asyncio.sleep(2)
                        continue

                # AI Sub-menu
                ui.console.print(f"\n[bold cyan]🧠 Inteligencia Artificial ({current_provider})[/bold cyan]")
                ui.console.print("1. Auditoría Automática")
                ui.console.print("2. Consulta Libre")
                ui.console.print("3. Volver")

                sub_choice = await ainput("\nIA > ")
                sub_choice = sub_choice.strip()

                if sub_choice == "3":
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

                    await ainput("\n[Presione Enter para continuar]")

                except Exception as e:
                        ui.console.print(f"[red]Error crítico comunicando con la IA: {e}[/red]")
                        await ainput("\n[Presione Enter para continuar]")

            elif choice == "4":
                # Change Platform AI Engine
                ui.console.print(f"\n[bold yellow]Cambiar Motor de IA de la Plataforma[/bold yellow]")
                ui.console.print(f"Proveedor Actual: [bold]{current_provider}[/bold]")
                ui.console.print("Opciones disponibles: deepseek, gemini")

                new_prov = await ainput("Nuevo proveedor: ")
                new_prov = new_prov.strip().lower()

                if new_prov in ["deepseek", "gemini"]:
                    # Save to .env (AI_ANALYSIS_PROVIDER)
                    save_key_to_env("AI_ANALYSIS_PROVIDER", new_prov)
                    current_provider = new_prov

                    # Also update AI_PROVIDER just in case
                    save_key_to_env("AI_PROVIDER", new_prov)

                    ui.console.print(f"[green]✓ Proveedor actualizado a: {current_provider} (Guardado en .env)[/green]")
                else:
                    ui.console.print("[red]Proveedor inválido.[/red]")

                await asyncio.sleep(2)

            elif choice == "5":
                # Manage API Keys
                ui.console.print("\n[bold yellow]Gestión de API Keys[/bold yellow]")
                ui.console.print("1. DeepSeek API Key")
                ui.console.print("2. Google Gemini API Key")
                ui.console.print("3. Volver")

                k_choice = await ainput("\nOpción > ")
                key_var = ""

                if k_choice == "1":
                    key_var = "DEEPSEEK_API_KEY"
                elif k_choice == "2":
                    key_var = "GEMINI_API_KEY"
                elif k_choice == "3":
                    continue
                else:
                    continue

                ui.console.print(f"Ingrese la nueva Key para {key_var}")
                new_key = await ainput("Key (Click derecho para pegar): ")
                new_key = new_key.strip()

                if new_key:
                    save_key_to_env(key_var, new_key)
                    ui.console.print(f"[green]✓ {key_var} actualizada y guardada en .env[/green]")
                else:
                    ui.console.print("[yellow]Operación cancelada (Key vacía)[/yellow]")

                await asyncio.sleep(1.5)

            elif choice == "6":
                ui.console.print("\n[bold cyan]¡Corred, insensatos![/bold cyan]")
                break
            else:
                ui.console.print("\n[red]Opción inválida. Intente de nuevo.[/red]")
                await asyncio.sleep(1)

        except asyncio.CancelledError:
            break
        except Exception as e:
            ui.console.print(f"\n[red]Error inesperado: {e}[/red]")
            # import traceback
            # traceback.print_exc()
            await asyncio.sleep(2)

if __name__ == "__main__":
    try:
        # Run the async main loop
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n\033[1;36mEl Mago se desvanece... (Interrupción de usuario)\033[0m")
        sys.exit(0)
