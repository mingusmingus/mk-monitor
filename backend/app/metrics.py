"""
Módulo de métricas en memoria.

Provee funcionalidades básicas para el seguimiento de métricas operativas del backend,
específicamente enfocadas en el rendimiento y comportamiento de los proveedores de IA.

Nota: Implementación en memoria no persistente. Diseñada para desarrollo.
Para producción, se recomienda migrar a `prometheus_client`.
"""
from __future__ import annotations

from collections import defaultdict
from threading import Lock
from typing import Dict, Tuple


# Estructuras en memoria (no persistentes)
_ai_requests_total: Dict[Tuple[str, bool], int] = defaultdict(int)
_ai_fallbacks_total: Dict[str, int] = defaultdict(int)

# Mecanismo de bloqueo para concurrencia
_lock = Lock()


def inc_ai_requests(provider: str, success: bool) -> None:
    """
    Incrementa el contador de solicitudes realizadas a un proveedor de IA.

    Args:
        provider (str): Identificador del proveedor (ej. "deepseek").
        success (bool): Indica si la solicitud fue exitosa (True) o fallida (False).
    """
    key = (provider.lower(), bool(success))
    with _lock:
        _ai_requests_total[key] += 1


def inc_ai_fallbacks(provider: str) -> None:
    """
    Incrementa el contador de recurrencia a mecanismos de respaldo (fallback).

    Se utiliza cuando un proveedor principal falla y el sistema opta por una alternativa
    (ej. heurísticas).

    Args:
        provider (str): Identificador del proveedor que falló.
    """
    k = provider.lower()
    with _lock:
        _ai_fallbacks_total[k] += 1


def _snapshot() -> dict:
    """
    Genera una instantánea del estado actual de las métricas.
    Útil para depuración y monitoreo básico.

    Returns:
        dict: Diccionario conteniendo el estado actual de los contadores.
    """
    with _lock:
        return {
            "ai_requests_total": {f"{p}:{'success' if s else 'error'}": c for (p, s), c in _ai_requests_total.items()},
            "ai_fallbacks_total": dict(_ai_fallbacks_total),
        }
