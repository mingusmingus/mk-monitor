"""
Placeholders de métricas en memoria para el backend.

Objetivo:
- Contar solicitudes a proveedores de IA y los fallbacks automáticos.

NOTA: Esto es deliberadamente simple y no persistente. Adecuado para
desarrollo/local.

TODO: Migrar a Prometheus usando `prometheus_client` con métricas como:
- Counter: ai_requests_total{provider, outcome}
- Counter: ai_fallbacks_total{provider}
"""
from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple


# Estructuras in-memory (no persistentes)
_ai_requests_total: Dict[Tuple[str, bool], int] = defaultdict(int)
_ai_fallbacks_total: Dict[str, int] = defaultdict(int)

# Bloqueo básico para evitar condiciones de carrera en servidores multi-hilo
_lock = Lock()


def inc_ai_requests(provider: str, success: bool) -> None:
    """Incrementa el contador de solicitudes a un proveedor de IA.

    Args:
        provider: Nombre del proveedor (e.g., "deepseek", "openai").
        success: True si la solicitud fue exitosa; False si falló (timeout, HTTP error, etc.).
    """
    key = (provider.lower(), bool(success))
    with _lock:
        _ai_requests_total[key] += 1


def inc_ai_fallbacks(provider: str) -> None:
    """Incrementa el contador de fallbacks automáticos para un proveedor dado.

    Se usa cuando, por ejemplo, falla DeepSeek en modo "auto" y se cae a heurísticas.
    """
    k = provider.lower()
    with _lock:
        _ai_fallbacks_total[k] += 1


# Funciones auxiliares opcionales (para depuración o endpoints de salud)
def _snapshot() -> dict:
    """Devuelve un snapshot de los contadores actuales (solo para debug)."""
    with _lock:
        return {
            "ai_requests_total": {f"{p}:{'success' if s else 'error'}": c for (p, s), c in _ai_requests_total.items()},
            "ai_fallbacks_total": dict(_ai_fallbacks_total),
        }
