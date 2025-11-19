"""
Servicio interno de IA con soporte para DeepSeek y heurísticas.

- Recibe logs crudos de MikroTik.
- Devuelve sugerencias de alertas normalizadas.
- Soporta múltiples proveedores: heuristic (local), deepseek (LLM), auto (intenta deepseek, fallback a heuristic).
"""
import json
import logging
from typing import Any, Dict, List, Optional

import requests

from ..config import Config
from ..metrics import inc_ai_requests, inc_ai_fallbacks


logger = logging.getLogger(__name__)


_SEVERITY_CANONICAL = {
    "info": "Aviso",
    "informational": "Aviso",
    "notice": "Aviso",
    "low": "Alerta Menor",
    "minor": "Alerta Menor",
    "medium": "Alerta Severa",
    "moderate": "Alerta Severa",
    "high": "Alerta Crítica",
    "critical": "Alerta Crítica",
    "critico": "Alerta Crítica",
}

_DEFAULT_ACTION = "Revisar y mitigar el evento identificado por el análisis de IA."
_MAX_LOG_LINES = 120


def analyze_logs(log_list: List[str], device_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """Orquesta el análisis de logs según el proveedor configurado."""
    provider = str(Config.AI_ANALYSIS_PROVIDER or "auto").lower()

    if provider == "heuristic":
        return _analyze_heuristic(log_list)

    if provider == "deepseek":
        if not Config.DEEPSEEK_API_KEY:
            logger.error("ai_analysis: DeepSeek seleccionado pero falta DEEPSEEK_API_KEY")
            return []
        deepseek_input = _prepare_logs_chunk(log_list, device_context)
        try:
            # TODO: instrumentar métrica ai_requests_total cuando se agregue observabilidad.
            alerts_raw = _call_deepseek(deepseek_input)
            # Métricas: solicitud DeepSeek exitosa
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
            return _analyze_heuristic(log_list)

        deepseek_input = _prepare_logs_chunk(log_list, device_context)
        try:
            # TODO: instrumentar métrica ai_requests_total cuando se agregue observabilidad.
            alerts_raw = _call_deepseek(deepseek_input)
            # Métricas: solicitud DeepSeek exitosa en modo auto
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

        # TODO: instrumentar métrica ai_fallbacks_total cuando se agregue observabilidad.
        # Métricas: solicitud DeepSeek fallida en modo auto y aplicación de fallback
        inc_ai_requests("deepseek", False)
        inc_ai_fallbacks("deepseek")
        return _analyze_heuristic(log_list)

    logger.warning("ai_analysis: provider desconocido '%s', fallback a heurísticas", provider)
    return _analyze_heuristic(log_list)


def _analyze_heuristic(log_list: List[str]) -> List[Dict[str, Any]]:
    """Análisis basado en reglas simples sobre los logs."""
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
            "accion_recomendada": "Revisar cableado/ISP y monitorear latencia/pérdidas."
        })

    return alerts


def _prepare_logs_chunk(log_list: List[str], device_context: Optional[Dict[str, Any]]) -> List[str]:
    """Recorta y enriquece los logs antes de enviarlos a DeepSeek."""
    chunk: List[str] = []
    if device_context:
        name = device_context.get("name") or "Desconocido"
        ip_address = device_context.get("ip") or "N/A"
        chunk.append(f"Device: {name} (IP: {ip_address})")
    chunk.extend(log_list[:_MAX_LOG_LINES])
    return chunk


def _call_deepseek(logs_chunk: List[str]) -> List[Dict[str, Any]]:
    """Realiza la llamada HTTP al endpoint de DeepSeek y devuelve la lista cruda de alertas."""
    if not Config.DEEPSEEK_API_KEY:
        raise RuntimeError("DeepSeek requiere DEEPSEEK_API_KEY configurada")

    url = Config.DEEPSEEK_API_URL or "https://api.deepseek.com/v1/chat/completions"
    model = Config.DEEPSEEK_MODEL or "deepseek-chat"
    timeout = Config.AI_TIMEOUT_SEC or 20
    max_tokens = Config.AI_MAX_TOKENS or 800

    logs_text = "\n".join(logs_chunk)
    prompt = (
        "Analiza los siguientes logs de equipos MikroTik y detecta posibles incidentes. "
        "Devuelve SOLO un JSON válido con una lista de objetos en el formato "
        "[{\"severity_raw\": str, \"message\": str}]. "
        "La severidad debe ser una de: info, low, medium, high, critical. "
        "Resume cada evento en menos de 300 caracteres y evita repetir información trivial.\n\n"
        f"Logs:\n{logs_text}"
    )

    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Eres un analista NOC. Clasifica eventos de routers MikroTik usando severidades "
                    "info, low, medium, high o critical."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens,
    }

    headers = {
        "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    response = requests.post(url, headers=headers, json=payload, timeout=timeout)

    if response.status_code == 429:
        error = requests.exceptions.HTTPError("DeepSeek rate limited", response=response)
        raise error
    if 400 <= response.status_code < 600:
        error = requests.exceptions.HTTPError(
            f"DeepSeek HTTP {response.status_code}", response=response
        )
        raise error

    try:
        data = response.json()
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek respondió con JSON inválido en nivel superior") from exc

    try:
        content = data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError, TypeError) as exc:
        raise ValueError("DeepSeek no incluyó contenido en la respuesta") from exc

    # Intentar manejar code fences comunes sin ocultar posibles problemas.
    if content.startswith("```") and content.endswith("```"):
        inner = content.strip("`").strip()
        if inner.lower().startswith("json"):
            inner = inner[4:].strip()
        content = inner

    try:
        alerts_raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("DeepSeek devolvió JSON de alertas mal formado") from exc

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

        severity_raw = str(item.get("severity_raw", "")).strip().lower()
        message = str(item.get("message", "")).strip()
        if not message:
            logger.debug("ai_analysis: alerta descartada por mensaje vacío")
            continue

        estado = _SEVERITY_CANONICAL.get(severity_raw, "Aviso")
        mensaje = message[:300]
        titulo = mensaje.split(".", 1)[0][:100] or f"Alerta IA #{idx}"

        normalized.append({
            "estado": estado,
            "titulo": titulo,
            "descripcion": mensaje,
            "accion_recomendada": _DEFAULT_ACTION,
        })

    return normalized
