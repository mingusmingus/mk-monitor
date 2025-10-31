"""
Servicio interno de IA (placeholder).

- Recibe logs crudos de MikroTik.
- Devuelve sugerencias de alertas normalizadas.
- TODO: Integración con motor LLM (p.ej. DeepSeek) para análisis avanzado.
"""
from typing import Dict, Any, List

def analyze_logs(log_list: List[str]) -> List[Dict[str, Any]]:
    """
    Input: lista de logs crudos.
    Output: lista de alertas normalizadas:
    {
      "estado": "Alerta Crítica" | "Alerta Severa" | "Alerta Menor" | "Aviso",
      "titulo": "...",
      "descripcion": "...",
      "accion_recomendada": "..."
    }
    Lógica de ejemplo:
      - "login failed" -> posible ataque de fuerza bruta (Severa).
      - "pppoe reconnect" repetido muchas veces -> inestabilidad WAN (Severa).
    """
    alerts: List[Dict[str, Any]] = []

    txt = "\n".join(log_list).lower()

    if "login failed" in txt:
        alerts.append({
            "estado": "Alerta Severa",
            "titulo": "Posible ataque de fuerza bruta",
            "descripcion": "Se detectaron intentos fallidos de login en el router.",
            "accion_recomendada": "Cambiar contraseñas y habilitar protección de acceso."
        })

    ppp_reconnects = sum(1 for line in log_list if "pppoe reconnect" in line.lower())
    if ppp_reconnects >= 5:
        alerts.append({
            "estado": "Alerta Severa",
            "titulo": "Inestabilidad en enlace WAN (PPPoE)",
            "descripcion": f"Se detectaron {ppp_reconnects} reconexiones PPPoE en un período corto.",
            "accion_recomendada": "Revisar cableado/ISP y monitorear latencia/perdidas."
        })

    # Otros patrones podrían ser "Aviso" o "Alerta Menor"
    return alerts