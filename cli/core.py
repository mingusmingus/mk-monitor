# Core logic and imports handling
import sys
import os
import asyncio
import platform
import json
from pathlib import Path
from typing import Dict, Any, List

# Try importing routeros_api
try:
    import routeros_api
    ROUTEROS_AVAILABLE = True
except ImportError:
    ROUTEROS_AVAILABLE = False

def init_system_paths(backend_path: str = None):
    """
    Helper to ensure backend paths are in sys.path.
    This can be used if we need to re-initialize or verify paths.
    """
    if backend_path and backend_path not in sys.path:
        sys.path.append(backend_path)

def load_or_create_env() -> str:
    """
    Locates the root .env file.
    Returns the path to the .env file.
    """
    # cli/core.py -> cli/ -> root/
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent
    return str(root_dir / '.env')

def save_key_to_env(key_name: str, key_value: str):
    """
    Saves the API Key to the .env file (EXCLUSIVELY in ROOT)
    and updates the current environment. Includes newline safety check.
    """
    # 1. Aggressive Strip
    key_value = key_value.strip()

    # 2. Determine Path (Root .env)
    target_env = load_or_create_env()

    # 3. Update Runtime Session
    os.environ[key_name] = key_value

    # Update Config class if available (for current execution)
    try:
        from backend.app.config import Config
        setattr(Config, key_name, key_value)
    except ImportError:
        pass

    # 4. Smart Write to File
    # Ensure directory exists
    target_path = Path(target_env)
    if not target_path.parent.exists():
        target_path.parent.mkdir(parents=True, exist_ok=True)

    lines = []
    if target_path.exists():
        try:
            with open(target_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        except UnicodeDecodeError:
             with open(target_path, 'r') as f: # Fallback
                lines = f.readlines()

    new_lines = []
    key_found = False

    for line in lines:
        # Check if line starts with KEY= (ignoring whitespace)
        if line.strip().startswith(f"{key_name}="):
            new_lines.append(f"{key_name}={key_value}\n")
            key_found = True
        else:
            new_lines.append(line)

    if not key_found:
        # Logic to prevent appending to a line without \n
        if new_lines:
            last_line = new_lines[-1]
            if not last_line.endswith('\n'):
                new_lines[-1] = last_line + '\n'

        new_lines.append(f"{key_name}={key_value}\n")

    try:
        with open(target_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
    except Exception as e:
        print(f"Error saving .env: {e}")

async def async_ping(ip: str) -> bool:
    """
    Asynchronously pings a host to check if it's reachable.
    Detects OS to use correct ping count flag (-n for Windows, -c for Linux/Mac).
    """
    current_os = platform.system().lower()
    count_flag = '-n' if current_os == 'windows' else '-c'

    try:
        process = await asyncio.create_subprocess_exec(
            'ping',
            count_flag,
            '1',
            ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )
        return_code = await process.wait()
        return return_code == 0
    except Exception:
        return False

class SimpleMiner:
    def __init__(self, ip, user, password, port=8728):
        self.ip = ip
        self.user = user
        self.password = password
        self.port = int(port)
        self.connection = None
        self.api = None

    def connect(self):
        if not ROUTEROS_AVAILABLE:
            raise ImportError("routeros_api library is not installed.")

        # Fixed: Removed socket_timeout which caused TypeError
        self.connection = routeros_api.RouterOsApiPool(
            self.ip,
            username=self.user,
            password=self.password,
            port=self.port,
            plaintext_login=True,
            use_ssl=False
        )
        self.api = self.connection.get_api()

    def disconnect(self):
        if self.connection:
            self.connection.disconnect()

    def mine(self) -> Dict[str, Any]:
        data = {}
        try:
            self.connect()

            # /system/resource/print
            try:
                resources = self.api.get_resource('/system/resource').get()
                if resources:
                    data['resource'] = resources[0]
            except Exception as e:
                 data['resource'] = {'error': str(e)}

            # /ip/address/print
            try:
                addresses = self.api.get_resource('/ip/address').get()
                data['addresses'] = addresses
            except Exception as e:
                data['addresses'] = [{'error': str(e)}]

            # /log/print
            try:
                logs = self.api.get_resource('/log').get()
                filtered_logs = [l for l in logs if 'debug' not in l.get('topics', '')]
                data['logs'] = filtered_logs[-20:]
            except Exception as e:
                data['logs'] = [{'message': f'Error fetching logs: {str(e)}'}]

        except Exception as e:
            # Capture connection errors instead of crashing
            return {'error': f"Connection failed: {str(e)}"}
        finally:
            self.disconnect()

        return data

def mine_data_sync(ip, user, password, port=8728) -> Dict[str, Any]:
    miner = SimpleMiner(ip, user, password, port=port)
    return miner.mine()

async def async_mine_data(ip, user, password, port=8728) -> Dict[str, Any]:
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(None, mine_data_sync, ip, user, password, port)


class GandalfBrain:
    def __init__(self):
        pass

    def check_key(self, provider="deepseek") -> bool:
        """Checks if the API key for the provider is available."""
        # Check environment first
        key_var = "DEEPSEEK_API_KEY" if provider == "deepseek" else "GEMINI_API_KEY"
        if os.environ.get(key_var):
            return True

        try:
            from backend.app.config import Config
            if provider == "deepseek":
                return bool(Config.DEEPSEEK_API_KEY)
            elif provider == "gemini":
                 return bool(getattr(Config, 'GEMINI_API_KEY', None))
        except ImportError:
            pass

        return False

    def setup_key(self, provider: str, key: str):
        """Injects the API key into environment and Config."""
        key_var = "DEEPSEEK_API_KEY" if provider == "deepseek" else "GEMINI_API_KEY"
        os.environ[key_var] = key

        try:
            from backend.app.config import Config
            setattr(Config, key_var, key)
        except ImportError:
            pass

    async def ask(self, context: dict, prompt: str, provider="deepseek") -> Dict[str, Any]:
        """
        Queries the AI provider.
        """
        from backend.app.core.ai.factory import AIFactory
        from backend.app.config import Config

        # Use configuration provider if set to specific engine, or override with argument
        # Ideally, respect what's passed, or what's in env
        # The instruction implies user can change provider

        # We ensure env var is set so Factory picks it up if it reads os.environ directly
        # or we rely on config reloading.
        # But AIFactory logic might rely on Config.AI_PROVIDER

        # Let's ensure the passed provider is used
        os.environ["AI_PROVIDER"] = provider

        # Also update Config to be safe if Factory reads Config
        Config.AI_PROVIDER = provider

        ai_provider = AIFactory.get_ai_provider()

        context_str = json.dumps(context, indent=2, default=str)

        full_system_prompt = (
            f"{prompt}\n\n"
            "INSTRUCTIONS:\n"
            "You are a Mikrotik Certified Control Engineer (MTCINE).\n"
            "Analyze the provided forensic data context.\n"
            "Provide your response in a JSON object with at least these keys: 'status', 'summary', 'technical_analysis'.\n"
            "If this is a free query, put the answer in 'technical_analysis'."
        )

        response = await ai_provider.analyze(context_str, full_system_prompt)
        return response
