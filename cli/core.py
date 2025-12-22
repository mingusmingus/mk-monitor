# Core logic and imports handling
import sys
import os
import asyncio
import platform

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
