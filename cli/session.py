from dataclasses import dataclass
from typing import List, Optional, Dict

@dataclass
class GandalfTarget:
    ip: str
    user: str
    password: str
    port: int = 8728
    is_alive: bool = False

class GandalfSession:
    """
    Manages the session state for the Gandalf CLI.
    """
    def __init__(self):
        self.context = {}
        self.targets: List[GandalfTarget] = []
        self.last_mined_data: Optional[Dict] = None

    def update_context(self, key, value):
        self.context[key] = value

    def get_context(self, key, default=None):
        return self.context.get(key, default)

    def add_target(self, ip, user, password, port=8728, is_alive=False):
        target = GandalfTarget(
            ip=ip,
            user=user,
            password=password,
            port=port,
            is_alive=is_alive
        )
        self.targets.append(target)

    def set_last_mined_data(self, data: Dict):
        self.last_mined_data = data

    @property
    def active_target(self) -> Optional[GandalfTarget]:
        if not self.targets:
            return None
        return self.targets[-1]
