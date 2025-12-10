"""
Servicio interno de IA con soporte para DeepSeek y heurísticas.

- Recibe logs crudos de MikroTik (idealmente estructurados).
- Devuelve sugerencias de alertas normalizadas.
- Soporta múltiples proveedores: heuristic (local), deepseek (LLM), auto (intenta deepseek, fallback a heuristic).
"""
import json
import logging
from typing import Any, Dict, List, Optional, Union

import requests

from ..config import Config
from ..metrics import inc_ai_requests, inc_ai_fallbacks


logger = logging.getLogger(__name__)


_SEVERITY_CANONICAL = {
    # Mapeo del usuario
    "warning": "Aviso",
    "minor": "Alerta Menor",
    "major": "Alerta Severa",
    "critical": "Alerta Crítica",
    # Mapeo legacy / fallback
    "info": "Aviso",
    "informational": "Aviso",
    "notice": "Aviso",
    "low": "Alerta Menor",
    "medium": "Alerta Severa",
    "moderate": "Alerta Severa",
    "high": "Alerta Crítica",
    "critico": "Alerta Crítica",
}

_DEFAULT_ACTION = "Revisar y mitigar el evento identificado por el análisis de IA."
_MAX_LOG_LINES = 120


def analyze_logs(log_list: List[Any], device_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Orquesta el análisis de logs según el proveedor configurado.

    Args:
        log_list: Lista de logs. Puede ser lista de strings (legacy) o lista de dicts (estructurado).
                  Si es dict, se espera: {timestamp, message, level, ...}
        device_context: Datos del dispositivo (name, ip, id, etc.)
    """
    provider = str(Config.AI_ANALYSIS_PROVIDER or "auto").lower()

    # Normalizar entrada a lista de dicts para uso interno si es posible
    structured_logs = _normalize_input_logs(log_list, device_context)

    if provider == "heuristic":
        return _analyze_heuristic(structured_logs)

    if provider == "deepseek":
        if not Config.DEEPSEEK_API_KEY:
            logger.error("ai_analysis: DeepSeek seleccionado pero falta DEEPSEEK_API_KEY")
            return []

        try:
            # Métricas: solicitud DeepSeek exitosa
            alerts_raw = _call_deepseek(structured_logs, device_context)
            inc_ai_requests("deepseek", True)
            return _normalize_alerts(alerts_raw)
        except requests.exceptions.Timeout:
            logger.warning("ai_analysis: DeepSeek timeout tras %ss", Config.AI_TIMEOUT_SEC)
        except requests.exceptions.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else None
            if status == 429:
                logger.warning("ai_analysis: DeepSeek respondió 429 (rate limit)")
            elif status and status >= 500:
                logger.error("ai_analysis: DeepSeek error servidor %s", status)
            else:
                logger.error("ai_analysis: DeepSeek HTTP %s", status or http_err)
        except ValueError as json_err:
            logger.error("ai_analysis: DeepSeek JSON inválido: %s", json_err)
        except requests.exceptions.RequestException as req_err:
            logger.error("ai_analysis: DeepSeek request error: %s", req_err)
        except Exception as exc:  # noqa: BLE001
            logger.error("ai_analysis: DeepSeek error inesperado: %s", exc)

        # Métricas: solicitud DeepSeek fallida
        inc_ai_requests("deepseek", False)
        return []

    if provider == "auto":
        if not Config.DEEPSEEK_API_KEY:
            logger.info("ai_analysis: modo auto sin DEEPSEEK_API_KEY, usando heurísticas")
            return _analyze_heuristic(structured_logs)

        try:
            alerts_raw = _call_deepseek(structured_logs, device_context)
            inc_ai_requests("deepseek", True)
            return _normalize_alerts(alerts_raw)
        except requests.exceptions.Timeout:
            logger.warning("ai_analysis: DeepSeek timeout tras %ss (fallback heurístico)", Config.AI_TIMEOUT_SEC)
        except requests.exceptions.HTTPError as http_err:
            status = http_err.response.status_code if http_err.response else None
            if status == 429:
                logger.warning("ai_analysis: DeepSeek rate limit (429), aplicando heurísticas")
            elif status and status >= 500:
                logger.error("ai_analysis: DeepSeek error servidor %s, aplicando heurísticas", status)
            else:
                logger.error("ai_analysis: DeepSeek HTTP %s, aplicando heurísticas", status or http_err)
        except ValueError as json_err:
            logger.error("ai_analysis: DeepSeek JSON inválido, aplicando heurísticas: %s", json_err)
        except requests.exceptions.RequestException as req_err:
            logger.error("ai_analysis: DeepSeek request error, aplicando heurísticas: %s", req_err)
        except Exception as exc:  # noqa: BLE001
            logger.error("ai_analysis: DeepSeek error inesperado, aplicando heurísticas: %s", exc)

        # Fallback
        inc_ai_requests("deepseek", False)
        inc_ai_fallbacks("deepseek")
        return _analyze_heuristic(structured_logs)

    logger.warning("ai_analysis: provider desconocido '%s', fallback a heurísticas", provider)
    return _analyze_heuristic(structured_logs)


def _normalize_input_logs(log_list: List[Any], device_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte la entrada (strings o dicts) a un formato unificado de lista de dicts."""
    normalized = []
    default_dev_name = "Unknown"
    if device_context:
        default_dev_name = device_context.get("name") or "Unknown"

    for item in log_list:
        if isinstance(item, str):
            normalized.append({
                "timestamp": None,
                "equipment_name": default_dev_name,
                "log_message": item,
                "log_level": None
            })
        elif isinstance(item, dict):
            # Asumimos que viene con keys parecidas a lo que queremos o mapeamos
            # Lo ideal es que venga ya limpio, pero aseguramos keys mínimas
            msg = item.get("log_message") or item.get("raw_log") or item.get("message") or ""
            normalized.append({
                "timestamp": item.get("timestamp_equipo") or item.get("timestamp"),
                "equipment_name": item.get("equipment_name") or default_dev_name,
                "log_message": str(msg),
                "log_level": item.get("log_level") or item.get("level")
            })
    return normalized


def _analyze_heuristic(log_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Análisis basado en reglas simples sobre los logs."""
    alerts: List[Dict[str, Any]] = []

    # Concatenamos todo para búsqueda simple, aunque podríamos iterar
    full_text = "\n".join([x["log_message"].lower() for x in log_list])

    if "login failed" in full_text:
        alerts.append({
            "estado": "Alerta Severa",
            "titulo": "Posible ataque de fuerza bruta",
            "descripcion": "Se detectaron intentos fallidos de login en el router.",
            "accion_recomendada": "Cambiar contraseñas y habilitar protección de acceso."
        })

    ppp_reconnects = full_text.count("pppoe reconnect")
    if ppp_reconnects >= 5:
        alerts.append({
            "estado": "Alerta Severa",
            "titulo": "Inestabilidad en enlace WAN (PPPoE)",
            "descripcion": f"Se detectaron {ppp_reconnects} reconexiones PPPoE en un período corto.",
            "accion_recomendada": "Revisar cableado/ISP y monitorear latencia/pérdidas."
        })

    return alerts


def _build_system_prompt() -> str:
    return (
        "Act as a Senior Network & Telecommunications Engineer specialized in analysis, classification, "
        "and notification of failures, events, and incidents in Mikrotik Routing & Switching equipment."
    )


def _build_user_prompt(logs_json: str) -> str:
    return f"""
Analyze the following list of Mikrotik logs and identify any events, failures, incidents, or anomalies.

Input Logs (JSON):
{logs_json}

Instructions:
1. Analyze each log entry for issues such as interface state changes, memory/CPU thresholds, connection failures, auth failures, BGP/OSPF issues, updates, packet loss, DDoS indicators, or unusual patterns.
2. Return ONLY a valid JSON list. No explanations, no markdown formatting.
3. If no issues are detected, return an empty JSON array: []
4. Output Format (JSON List of objects):
   - "equipment_name": string
   - "title": string (max 100 chars)
   - "severity": "warning" | "minor" | "major" | "critical"
   - "alert_class": "alert-secondary" | "alert-info" | "alert-warning" | "alert-danger"
   - "detected_date": string (ISO 8601 YYYY-MM-DDTHH:MM:SSZ)
   - "description": string (detailed description, max 180 chars)
   - "affected_services": array of strings
   - "recommended_action": string (max 100 chars)
   - "log_excerpt": string (the log line that triggered this)

Severity Definitions:
- "warning": Event occurred but does not affect equipment/services.
- "minor": Low-impact failure, critical services not affected.
- "major": Medium-impact failure, may affect some services.
- "critical": High-impact failure, compromises equipment or multiple services.

Constraints:
- Return ONLY JSON.
- No code blocks (```json ... ```).
- Ensure valid JSON.
"""


def _call_deepseek(logs_list: List[Dict[str, Any]], device_context: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Realiza la llamada HTTP al endpoint de DeepSeek y devuelve la lista cruda de alertas."""
    if not Config.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek requiere DEEPSEEK_API_KEY configurada")

    url = Config.DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"
    model = Config.DEEPSEEK_MODEL or "deepseek-chat"
    timeout = Config.AI_TIMEOUT_SEC or 30
    max_tokens = Config.AI_MAX_TOKENS or 4096

    # Preparar el input en formato JSON
    # Limitamos a _MAX_LOG_LINES para no saturar el contexto
    logs_to_send = logs_list[:_MAX_LOG_LINES]

    # Formatear timestamps a string si son datetimes
    serializable_logs = []
    for log in logs_to_send:
        item = log.copy()
        ts = item.get("timestamp")
        if ts and not isinstance(ts, str):
            item["timestamp"] = str(ts)
        serializable_logs.append(item)

    logs_json_str = json.dumps(serializable_logs, indent=2)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": _build_system_prompt(),
            },
            {"role": "user", "content": _build_user_prompt(logs_json_str)},
        ],
        "temperature": 0.3,  # Deterministic output
        "max_tokens": max_tokens,
        "stream": False # Could implement streaming later for large batches
    }

    headers = {
        "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code == 429:
        raise requests.exceptions.HTTPError("DeepSeek rate limited", response=response)
    if 400 <= response.status_code < 600:
        raise requests.exceptions.HTTPError(
            f"DeepSeek HTTP {response.status_code}", response=response
        )

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek respondió con JSON inválido en nivel superior") from exc

    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("DeepSeek no incluyó contenido en la respuesta") from exc

    # Limpieza de markdown fences si el modelo los añade a pesar de las instrucciones
    if content.startswith("```"):
        # Puede ser ```json ... ``` o simplemente ``` ... ```
        lines = content.splitlines()
        if lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip().startswith("```"):
            lines = lines[:-1]
        content = "\n".join(lines).strip()

    try:
        alerts_raw = json.loads(content)
    except json.JSONDecodeError as exc:
        # Intento de recuperación simple si hay texto extra
        start = content.find("[")
        end = content.rfind("]")
        if start != -1 and end != -1:
            try:
                alerts_raw = json.loads(content[start:end+1])
            except json.JSONDecodeError:
                raise ValueError(f"DeepSeek devolvió JSON mal formado: {exc}") from exc
        else:
            raise ValueError(f"DeepSeek devolvió JSON mal formado: {exc}") from exc

    if not isinstance(alerts_raw, list):
        raise ValueError("DeepSeek devolvió un payload que no es lista")

    return alerts_raw


def _normalize_alerts(alerts_raw: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Convierte la salida cruda del LLM a la estructura interna estándar."""
    normalized: List[Dict[str, Any]] = []
    for idx, item in enumerate(alerts_raw, start=1):
        if not isinstance(item, dict):
            logger.debug("ai_analysis: alerta descartada por no ser dict: %s", item)
            continue

        severity_raw = str(item.get("severity", "")).strip().lower()
        title = str(item.get("title", "")).strip()
        description = str(item.get("description", "")).strip()
        rec_action = str(item.get("recommended_action", "")).strip()

        # Enriquecemos la descripcion con info extra si cabe
        affected = item.get("affected_services")
        excerpt = item.get("log_excerpt")

        full_desc = description
        if affected:
            full_desc += f" | Servicios: {affected}"
        if excerpt:
            # Cortar si es muy largo
            if len(excerpt) > 50:
                excerpt = excerpt[:47] + "..."
            full_desc += f" | Log: {excerpt}"

        if not title:
            logger.debug("ai_analysis: alerta descartada por titulo vacío")
            continue

        estado = _SEVERITY_CANONICAL.get(severity_raw, "Aviso")

        # Truncate to DB limits
        # Alert.titulo: 120
        # Alert.descripcion: 512
        # Alert.accion_recomendada: 255

        normalized.append({
            "estado": estado,
            "titulo": title[:120],
            "descripcion": full_desc[:512],
            "accion_recomendada": rec_action[:255] or _DEFAULT_ACTION,
            # Extra fields useful for debugging or future expansion
            "raw_analysis": item
        })

    return normalized
