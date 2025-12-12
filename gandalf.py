#!/usr/bin/env python3
import asyncio
import os
import sys
import time
import getpass
import logging
from datetime import datetime

# --- PRE-INIT CONFIGURATION ---
# Ensure backend is in python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(BASE_DIR, 'backend')
sys.path.append(BACKEND_DIR)

# Suppress standard logging to keep the mystique
logging.getLogger("app").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)

# Handle Dependencies
try:
    from colorama import init, Fore, Style
    init(autoreset=True)
except ImportError:
    print("Error: colorama not found. Please install it.")
    sys.exit(1)

try:
    from cryptography.fernet import Fernet
except ImportError:
    print(f"{Fore.RED}[!] ERROR CRÍTICO: CRYPTOGRAPHY NO DETECTADO.{Style.RESET_ALL}")
    sys.exit(1)

# Inject Encryption Key if missing (for Phantom Node in RAM)
if not os.environ.get("ENCRYPTION_KEY"):
    # Generate a temporary key for this session
    os.environ["ENCRYPTION_KEY"] = Fernet.generate_key().decode()

# --- BACKEND IMPORTS ---
try:
    from app.core.ai.factory import AIFactory
    from app.services.device_mining import DeviceMiner
    from app.services.device_service import encrypt_secret
    from app.models.device import Device
    from app.config import Config
except ImportError as e:
    print(f"{Fore.RED}[!] ERROR FATAL DE IMPORTACIÓN: {e}{Style.RESET_ALL}")
    print(f"{Fore.RED}[!] Verifique que está en la raíz del repositorio y 'backend/' es accesible.{Style.RESET_ALL}")
    sys.exit(1)


# --- CONSTANTS & ART ---
ASCII_ART = r"""
,---.
                   /    |
                  /     |   G A N D A L F
                 /      |   [v1.0.4 - ORACULO]
                /       |
           ___,'        |   // SYSTEM: ONLINE
         <  -'          :   // MODE:   ASYNC_SHELL
          `-.__..--'``-,_\_
             |o/ <o>` :,.)_`>
             :/ `     ||/)
             (_.).__,-` |\
             /( `.``   `| :
             \'`-.)  `  ; ;
             | `       /-<
             |     `  /   `.
     ,-_-..____     /|  `  \
    /,'-.__\\  ``-./ :`      \
"""

# --- UTILS ---

async def typewriter_effect(text: str, color: str = Fore.CYAN, delay: float = 0.005):
    """Simulates a retro typewriter effect."""
    sys.stdout.write(color)
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        await asyncio.sleep(delay)
    sys.stdout.write(Style.RESET_ALL + "\n")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_banner():
    clear_screen()
    print(f"{Style.DIM}{ASCII_ART}{Style.RESET_ALL}")

# --- CORE LOGIC ---

class GandalfCLI:
    def __init__(self):
        self.phantom_device = None
        self.mined_data = {}
        self.logs = []

    def log(self, message: str, level="INFO"):
        timestamp = datetime.now().strftime("%H:%M:%S")
        entry = f"[{timestamp}] {level} :: {message}"
        self.logs.append(entry)
        # We don't print logs immediately unless requested, to keep UI clean

    async def materialize_node(self):
        """[0x01] Creates a Device object in RAM."""
        print(f"\n{Fore.GREEN}>>> INICIANDO PROTOCOLO DE MATERIALIZACIÓN...{Style.RESET_ALL}")

        try:
            ip = input(f"{Fore.GREEN}>>> IP OBJETIVO: {Style.RESET_ALL}")
            user = input(f"{Fore.GREEN}>>> USUARIO: {Style.RESET_ALL}")
            password = getpass.getpass(f"{Fore.GREEN}>>> PASSWORD (HIDDEN): {Style.RESET_ALL}")
            port_input = input(f"{Fore.GREEN}>>> PUERTO API (Default 8728): {Style.RESET_ALL}")
            port = int(port_input) if port_input.strip() else 8728

            # Encrypt credentials using the session key
            user_enc = encrypt_secret(user)
            pass_enc = encrypt_secret(password)

            # Create Phantom Device (No DB persistence, just RAM)
            self.phantom_device = Device(
                id=9999, # Phantom ID
                tenant_id=1,
                name="PHANTOM_NODE_v1",
                ip_address=ip,
                port=port,
                username_encrypted=user_enc,
                password_encrypted=pass_enc,
                created_at=datetime.now()
            )

            await typewriter_effect(f"[+] NODO FANTASMA MATERIALIZADO EN RAM.", Fore.GREEN)
            await typewriter_effect(f"[+] HASH IDENTIDAD: {hash(self.phantom_device)}", Style.DIM)
            self.log(f"Nodo fantasma creado: {ip}")

        except Exception as e:
            print(f"{Fore.RED}[!] ERROR DE MATERIALIZACIÓN: {str(e)}{Style.RESET_ALL}")
            self.log(f"Error materialización: {e}", "ERROR")

    async def signal_probe(self):
        """[0x02] Connects to Mikrotik and mines data."""
        if not self.phantom_device:
            print(f"{Fore.RED}[!] ERROR: NO HAY NODO FANTASMA. EJECUTE [0x01] PRIMERO.{Style.RESET_ALL}")
            return

        print(f"\n{Fore.GREEN}>>> ESTABLECIENDO ENLACE NEURAL CON {self.phantom_device.ip_address}...{Style.RESET_ALL}")

        try:
            miner = DeviceMiner(self.phantom_device)
            # Running sync mining in async loop (blocking, but acceptable for CLI)
            # Ideally we'd wrap in executor but let's keep it simple for now as mining is sync
            print(f"{Style.DIM}... Inyectando payload de sondeo ...{Style.RESET_ALL}")

            data = miner.mine()

            if data.get("error"):
                raise Exception(data["error"])

            self.mined_data = data

            # Display Summary
            context = data.get("context", {})
            health = data.get("health", {})

            await typewriter_effect(f"[+] ENLACE ESTABLECIDO.", Fore.GREEN)
            print(f"{Fore.CYAN}--- TELEMETRÍA OBTENIDA ---{Style.RESET_ALL}")
            print(f"IDENTITY: {context.get('identity')}")
            print(f"BOARD:    {context.get('board_name')} ({context.get('version')})")
            print(f"UPTIME:   {context.get('uptime')}")
            print(f"CPU:      {context.get('cpu_load')}%")
            if health:
                print(f"VOLTAJE:  {health.get('voltage')}V")
                print(f"TEMP:     {health.get('temperature')}C")

            findings = data.get("heuristics", [])
            if findings:
                print(f"{Fore.RED}[!] ANOMALÍAS DETECTADAS:{Style.RESET_ALL}")
                for f in findings:
                    print(f"  - {f}")
            else:
                print(f"{Fore.GREEN}[+] SISTEMA ESTABLE.{Style.RESET_ALL}")

            self.log(f"Sondeo exitoso a {self.phantom_device.ip_address}")

        except Exception as e:
            print(f"{Fore.RED}[!] ENLACE FALLIDO: {str(e)}{Style.RESET_ALL}")
            self.log(f"Fallo de sondeo: {e}", "ERROR")

    async def summon_demon(self):
        """[0x03] Chat with AI."""
        if not self.phantom_device:
            print(f"{Fore.RED}[!] ADVERTENCIA: SIN NODO FANTASMA, EL DEMONIO NO TENDRÁ CONTEXTO TÉCNICO.{Style.RESET_ALL}")

        # Check current provider
        provider_name = os.environ.get("AI_PROVIDER", "deepseek").upper()
        print(f"\n{Fore.CYAN}>>> INVOCANDO DEMONIO NEURONAL [{provider_name}]...{Style.RESET_ALL}")

        # Menu de Hechizos
        print(f"{Style.DIM}[1] MODO LIBRE (Consulta directa)")
        print(f"[2] HECHIZO: AUDITORÍA (Análisis de Seguridad)")
        print(f"[3] HECHIZO: TRADUCTOR (Explicación Config){Style.RESET_ALL}")

        choice = input(f"{Fore.GREEN}>>> SELECCIONE RITUAL: {Style.RESET_ALL}")

        prompt = ""
        system_context = "Eres un ingeniero experto en redes Mikrotik (MTCINE) con un tono técnico, serio y conciso."

        if self.mined_data:
            import json
            # Simplify data for AI to save tokens
            minimized_data = {
                "context": self.mined_data.get("context"),
                "security": self.mined_data.get("security"),
                "heuristics": self.mined_data.get("heuristics"),
                "logs_sample": self.mined_data.get("logs")[:5] if self.mined_data.get("logs") else []
            }
            system_context += f"\nCONTEXTO DEL DISPOSITIVO:\n{json.dumps(minimized_data)}"

        if choice == "2":
            prompt = "Analiza la seguridad de este router basándote en los datos proporcionados. Lista vulnerabilidades críticas y recomendaciones."
        elif choice == "3":
            prompt = "Explica la configuración y el estado actual del equipo en español simple para un ejecutivo no técnico."
        else:
            prompt = input(f"{Fore.GREEN}>>> ESCRIBA SU CONSULTA: {Style.RESET_ALL}")

        if not prompt:
            return

        # Execute AI Call
        try:
            print(f"{Style.DIM}... Canalizando energía del vacío ...{Style.RESET_ALL}")
            provider = AIFactory.get_ai_provider()

            # Check for API Key before calling
            if provider_name == "GEMINI" and not os.environ.get("GEMINI_API_KEY"):
                raise ValueError("GEMINI_API_KEY no encontrada.")
            if provider_name == "DEEPSEEK" and not os.environ.get("DEEPSEEK_API_KEY"):
                # Check config as fallback
                if not getattr(Config, 'DEEPSEEK_API_KEY', None):
                     raise ValueError("DEEPSEEK_API_KEY no encontrada.")

            # We use the raw generate_response or similar if available,
            # but BaseAIProvider usually has `analyze_device` or similar.
            # Let's check BaseAIProvider interface?
            # Usually provider.generate_response(prompt, context)

            # Assuming provider has a method to just chat.
            # If the provider interface is strictly `analyze_forensics(data)`, we might need to adapt.
            # Checking `backend/app/core/ai/base.py` would have been good.
            # Assuming `generate_response(prompt: str)` exists or similar.

            # Call the provider's analyze method
            # analyze(context: str, prompt_template: str) where context is user input and template is system prompt
            if hasattr(provider, 'analyze'):
                response = await provider.analyze(context=prompt, prompt_template=system_context)
            else:
                # Fallback if interface changes
                raise AttributeError(f"El proveedor {provider_name} no tiene el método 'analyze'.")

            # Extract text from response (it might be a dict or object)
            if isinstance(response, dict):
                # If it's the mock response or structured analysis
                text_out = response.get("technical_analysis") or response.get("summary") or response.get("raw_output") or str(response)

                # Format specific keys if available
                if isinstance(response.get("recommendations"), list):
                    text_out += "\n\nRECOMENDACIONES:\n" + "\n".join([f"- {r}" for r in response["recommendations"]])
            else:
                text_out = str(response)

            await typewriter_effect(f"\n>> {text_out}", Fore.CYAN)
            self.log(f"Consulta IA ({provider_name}): {prompt[:20]}...")

        except Exception as e:
            # Check for API Key error specifically to prompt hot-swap?
            # The prompt says: "En la opción [0x04], si el usuario elige una IA... Input: ... Ingrese Credencial".
            # This is option 0x03. Option 0x04 is switching.
            # But if it fails here due to key...
            print(f"{Fore.RED}[!] EL DEMONIO RECHAZÓ LA LLAMADA: {str(e)}{Style.RESET_ALL}")
            self.log(f"Error IA: {e}", "ERROR")

    async def transmute_core(self):
        """[0x04] Switch AI Provider."""
        print(f"\n{Fore.GREEN}>>> SELECCIÓN DE NÚCLEO:{Style.RESET_ALL}")
        print(f"[1] DEEPSEEK")
        print(f"[2] GEMINI")

        sel = input(f"{Fore.GREEN}>>> OPCIÓN: {Style.RESET_ALL}")
        provider_key = "DEEPSEEK" if sel == "1" else "GEMINI" if sel == "2" else None

        if not provider_key:
            print(f"{Fore.RED}[!] SELECCIÓN INVÁLIDA.{Style.RESET_ALL}")
            return

        # Hot-Swap Logic
        env_var = f"{provider_key}_API_KEY"
        current_key = os.getenv(env_var) or getattr(Config, env_var, None)

        if not current_key:
            print(f"{Fore.RED}[!] ERROR CRÍTICO: LLAVE NO DETECTADA EN VARIABLES DE ENTORNO.{Style.RESET_ALL}")
            new_key = input(f"{Fore.GREEN}>>> INGRESE CREDENCIAL TEMPORAL PARA INYECCIÓN EN RAM: {Style.RESET_ALL}")
            if new_key.strip():
                os.environ[env_var] = new_key.strip()
                # Also update Config class if possible (though env var usually enough if re-read)
                # Config might have cached it as None.
                setattr(Config, env_var, new_key.strip())
                print(f"{Style.DIM}// Llave inyectada en sector de memoria 0x{id(new_key):X}{Style.RESET_ALL}")
            else:
                print(f"{Fore.RED}[!] ABORTANDO TRANSMUTACIÓN.{Style.RESET_ALL}")
                return

        os.environ["AI_PROVIDER"] = provider_key.lower()
        print(f"{Fore.CYAN}>>> NÚCLEO TRANSMUTADO A: {provider_key}{Style.RESET_ALL}")
        self.log(f"Cambio de proveedor IA a {provider_key}")

    async def consult_grimoire(self):
        """[0x05] View Logs."""
        print(f"\n{Fore.CYAN}--- GRIMORIO DEL SISTEMA ---{Style.RESET_ALL}")
        if not self.logs:
            print(f"{Style.DIM}* Páginas vacías *{Style.RESET_ALL}")
        for entry in self.logs:
            color = Fore.RED if "ERROR" in entry else Style.DIM
            print(f"{color}{entry}{Style.RESET_ALL}")
        input(f"\n{Fore.GREEN}>>> PRESIONE ENTER PARA CERRAR GRIMORIO...{Style.RESET_ALL}")

    async def run(self):
        print_banner()
        while True:
            # Menu
            print(f"\n{Fore.GREEN}[0x01] MATERIALIZAR NODO FANTASMA{Style.RESET_ALL}   {Style.DIM}(Crear Router en RAM: IP/User/Pass){Style.RESET_ALL}")
            print(f"{Fore.GREEN}[0x02] SONDEO DE SEÑAL{Style.RESET_ALL}              {Style.DIM}(Ping + Info Mikrotik){Style.RESET_ALL}")
            print(f"{Fore.GREEN}[0x03] INVOCAR DEMONIO NEURONAL{Style.RESET_ALL}     {Style.DIM}(Chat IA con Contexto){Style.RESET_ALL}")
            print(f"{Fore.GREEN}[0x04] TRANSMUTAR NÚCLEO{Style.RESET_ALL}            {Style.DIM}(Cambiar IA: DeepSeek <-> Gemini){Style.RESET_ALL}")
            print(f"{Fore.GREEN}[0x05] CONSULTAR GRIMORIO{Style.RESET_ALL}           {Style.DIM}(Ver Logs){Style.RESET_ALL}")
            print(f"{Fore.GREEN}[0x99] CERRAR CONEXIÓN{Style.RESET_ALL}              {Style.DIM}(Salir){Style.RESET_ALL}")

            choice = input(f"\n{Fore.GREEN}>>> COMANDO: {Style.RESET_ALL}")

            if choice == "0x01" or choice == "1":
                await self.materialize_node()
            elif choice == "0x02" or choice == "2":
                await self.signal_probe()
            elif choice == "0x03" or choice == "3":
                await self.summon_demon()
            elif choice == "0x04" or choice == "4":
                await self.transmute_core()
            elif choice == "0x05" or choice == "5":
                await self.consult_grimoire()
            elif choice == "0x99" or choice == "99":
                await typewriter_effect(">>> DESCONECTANDO SISTEMA...", Fore.RED)
                break
            else:
                print(f"{Fore.RED}[!] COMANDO DESCONOCIDO.{Style.RESET_ALL}")

if __name__ == "__main__":
    cli = GandalfCLI()
    try:
        asyncio.run(cli.run())
    except KeyboardInterrupt:
        print(f"\n{Fore.RED}>>> INTERRUPCIÓN FORZADA.{Style.RESET_ALL}")
