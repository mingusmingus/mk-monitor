# Core logic and imports handling
import sys
import os
import asyncio
import platform
import json
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

async def async_ping(ip: str) -> bool:
    """
    Asynchronously pings a host to check if it's reachable.
    Detects OS to use correct ping count flag (-n for Windows, -c for Linux/Mac).
    """
    # Determine the current operating system
    current_os = platform.system().lower()

    # Select the appropriate ping parameter
    # Windows uses '-n', others use '-c' to set the number of echo requests
    count_flag = '-n' if current_os == 'windows' else '-c'

    # Construct the command
    # ping <flag> 1 <ip>
    # Note: Using 'ping' command which should be in PATH

    try:
        # Create subprocess
        # stdout and stderr are piped to /dev/null (or equivalent) to avoid cluttering UI
        process = await asyncio.create_subprocess_exec(
            'ping',
            count_flag,
            '1',
            ip,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL
        )

        # Wait for the process to finish
        return_code = await process.wait()

        # Return True if return_code is 0 (success), else False
        return return_code == 0

    except Exception:
        # In case of any error (e.g., command not found), assume host is unreachable or check failed
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

        self.connection = routeros_api.RouterOsApiPool(
            self.ip,
            username=self.user,
            password=self.password,
            port=self.port,
            plaintext_login=True,
            use_ssl=False,
            socket_timeout=5
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
            resources = self.api.get_resource('/system/resource').get()
            if resources:
                data['resource'] = resources[0]

            # /ip/address/print
            addresses = self.api.get_resource('/ip/address').get()
            data['addresses'] = addresses

            # /log/print
            # Getting last 20 logs. Not filtering topics heavily as per prompt request "filtering topics de debug si es posible"
            # routeros_api allows query but filtering effectively might be easier in python or simple slice.
            logs = self.api.get_resource('/log').get()
            # Filter debug if possible, else take last 20
            # Let's filter out debug topics roughly
            filtered_logs = [l for l in logs if 'debug' not in l.get('topics', '')]
            data['logs'] = filtered_logs[-20:]

        except Exception as e:
            # Re-raise to be handled by caller
            raise e
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
        # We rely on lazy import in methods or updated env vars
        pass

    def check_key(self, provider="deepseek") -> bool:
        """Checks if the API key for the provider is available."""
        try:
            from app.config import Config
            if provider == "deepseek":
                return bool(os.getenv("DEEPSEEK_API_KEY") or Config.DEEPSEEK_API_KEY)
            elif provider == "gemini":
                 return bool(os.getenv("GEMINI_API_KEY") or getattr(Config, 'GEMINI_API_KEY', None))
        except ImportError:
            # Fallback if Config not loaded yet
            pass

        key_var = "DEEPSEEK_API_KEY" if provider == "deepseek" else "GEMINI_API_KEY"
        return key_var in os.environ

    def setup_key(self, provider: str, key: str):
        """Injects the API key into environment and Config."""
        key_var = "DEEPSEEK_API_KEY" if provider == "deepseek" else "GEMINI_API_KEY"
        os.environ[key_var] = key

        # Update Config dynamically so new instances pick it up
        try:
            from app.config import Config
            setattr(Config, key_var, key)
        except ImportError:
            pass

    async def ask(self, context: dict, prompt: str, provider="deepseek") -> Dict[str, Any]:
        """
        Queries the AI provider.
        """
        # Ensure imports work (backend must be in sys.path)
        from app.core.ai.factory import AIFactory

        # Force provider selection via env var which Factory reads
        os.environ["AI_PROVIDER"] = provider

        ai_provider = AIFactory.get_ai_provider()

        # Convert context to string
        context_str = json.dumps(context, indent=2, default=str)

        # Construct system prompt to ensure JSON output and handle user question
        # DeepSeekProvider enforces JSON object response format.
        # We guide the model to put the text answer in 'technical_analysis'.
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
