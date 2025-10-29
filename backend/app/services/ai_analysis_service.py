"""
Servicio interno de IA (placeholder).

- Recibe logs crudos de MikroTik.
- Devuelve una sugerencia de alerta con: estado, titulo, descripcion, accion_recomendada.
- TODO: Aquí se integrará el motor IA (p.ej. DeepSeek, etc.)
"""

from typing import Dict, Any, List

def analyze_logs_to_alert(log_lines: List[str]) -> Dict[str, Any]:
    """
    Placeholder: analiza logs y devuelve una alerta sugerida.
    """
    # TODO: Implementar análisis real con IA/heurísticas
    return {
        "estado": "Aviso",
        "titulo": "Actividad inusual detectada",
        "descripcion": "Se detectaron eventos fuera del patrón habitual.",
        "accion_recomendada": "Revisar configuración y tráfico del router."
    }