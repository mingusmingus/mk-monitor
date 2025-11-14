"""
Servicio interno de IA con soporte para DeepSeek y heurísticas.

- Recibe logs crudos de MikroTik.
- Devuelve sugerencias de alertas normalizadas.
- Soporta múltiples proveedores: heuristic (local), deepseek (LLM), auto (intenta deepseek, fallback a heuristic).
"""
import json
import re
import logging
from typing import Dict, Any, List, Optional
import requests
from ..config import Config

# Mapeo de variantes de estado a taxonomía canónica
ESTADO_MAPPING = {
    "aviso": "Aviso",
    "alerta menor": "Alerta Menor",
    "menor": "Alerta Menor",
    "alerta severa": "Alerta Severa",
    "severa": "Alerta Severa",
    "alerta crítica": "Alerta Crítica",
    "crítica": "Alerta Crítica",
    "critica": "Alerta Crítica",
}

VALID_ESTADOS = {"Aviso", "Alerta Menor", "Alerta Severa", "Alerta Crítica"}


def normalize_estado(estado: str) -> str:
    """
    Normaliza variantes del estado a uno de los 4 valores canónicos.
    """
    if not estado:
        return "Aviso"
    estado_lower = estado.lower().strip()
    normalized = ESTADO_MAPPING.get(estado_lower)
    if normalized:
        return normalized
    # Si ya está en formato canónico
    if estado in VALID_ESTADOS:
        return estado
    # Fallback: buscar coincidencia parcial
    if "crítica" in estado_lower or "critica" in estado_lower:
        return "Alerta Crítica"
    if "severa" in estado_lower:
        return "Alerta Severa"
    if "menor" in estado_lower:
        return "Alerta Menor"
    return "Aviso"


def analyze_logs(log_list: List[str], device_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Orquestador principal de análisis de logs.
    
    Comportamiento según AI_ANALYSIS_PROVIDER:
    - "heuristic": usa solo heurísticas locales.
    - "deepseek": intenta DeepSeek; si falla, raise (el caller decide fallback).
    - "auto": intenta DeepSeek si hay key; si falla o no hay key, fallback a heurísticas.
    
    Args:
        log_list: Lista de strings de logs crudos.
        device_context: Opcional, dict con {"name": str, "ip": str} para contexto adicional.
    
    Returns:
        Lista de dicts normalizados:
        {
          "estado": "Aviso"|"Alerta Menor"|"Alerta Severa"|"Alerta Crítica",
          "titulo": str,
          "descripcion": str,
          "accion_recomendada": str
        }
    """
    provider = str(Config.AI_ANALYSIS_PROVIDER).lower()
    
    if provider == "heuristic":
        return _analyze_heuristic(log_list)
    
    elif provider == "deepseek":
        # Modo estricto: si falla DeepSeek, propagar error
        return analyze_with_deepseek(log_list, device_context)
    
    elif provider == "auto":
        # Modo tolerante: intenta DeepSeek, fallback a heurísticas
        if Config.DEEPSEEK_API_KEY:
            try:
                return analyze_with_deepseek(log_list, device_context)
            except Exception as ex:
                logging.warning("ai_analysis: DeepSeek falló, fallback a heurísticas: %s", ex)
                return _analyze_heuristic(log_list)
        else:
            logging.info("ai_analysis: DeepSeek no configurado (modo auto), usando heurísticas")
            return _analyze_heuristic(log_list)
    
    else:
        logging.warning("ai_analysis: provider desconocido '%s', fallback a heurísticas", provider)
        return _analyze_heuristic(log_list)


def _analyze_heuristic(log_list: List[str]) -> List[Dict[str, Any]]:
    """
    Análisis basado en heurísticas locales (lógica original).
    
    Detecta patrones conocidos:
    - "login failed" -> posible ataque de fuerza bruta
    - "pppoe reconnect" repetido -> inestabilidad WAN
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
            "accion_recomendada": "Revisar cableado/ISP y monitorear latencia/pérdidas."
        })

    return alerts


def analyze_with_deepseek(log_list: List[str], device_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    Análisis con DeepSeek LLM.
    
    Construye un prompt solicitando análisis de logs MikroTik y generación de alertas
    en formato JSON puro (sin markdown fences).
    
    Args:
        log_list: Lista de logs crudos.
        device_context: Opcional, dict con {"name": str, "ip": str}.
    
    Returns:
        Lista de alertas normalizadas.
    
    Raises:
        Exception: Si falla la llamada a DeepSeek (timeout, error HTTP, JSON inválido, etc).
    
    TODO:
    - Implementar backoff/retry si 429 (rate limit)
    - Chunking de logs si excede max_tokens
    - Deduplicación y correlación de alertas
    - Caché de respuestas para logs idénticos
    """
    if not Config.DEEPSEEK_API_KEY:
        raise ValueError("analyze_with_deepseek: DEEPSEEK_API_KEY no configurada")
    
    # Contexto del dispositivo (opcional)
    context_str = ""
    if device_context:
        name = device_context.get("name", "Desconocido")
        ip = device_context.get("ip", "N/A")
        context_str = f"\nDispositivo: {name} (IP: {ip})"
    
    # Limitar número de logs para no exceder tokens
    # TODO: implementar chunking inteligente si log_list es muy largo
    max_logs = 100
    logs_sample = log_list[:max_logs]
    logs_text = "\n".join(logs_sample)
    
    prompt = f"""Eres un experto en análisis de logs de routers MikroTik. Analiza los siguientes logs y genera alertas operativas según la taxonomía:

Taxonomía de Estados (obligatoria):
- "Aviso": Información relevante sin impacto operativo inmediato
- "Alerta Menor": Problema leve que requiere atención en plazo medio
- "Alerta Severa": Problema grave que afecta operación y requiere atención urgente
- "Alerta Crítica": Fallo crítico que compromete servicio, requiere atención inmediata

{context_str}

Logs a analizar:
{logs_text}

Genera una lista de alertas en formato JSON puro (sin markdown, sin triple backticks). Cada alerta debe tener exactamente estos campos:
- "estado": uno de los 4 valores exactos de la taxonomía
- "titulo": descripción breve del problema (máximo 100 caracteres)
- "descripcion": explicación detallada del problema detectado (máximo 400 caracteres)
- "accion_recomendada": pasos específicos para resolver el problema (máximo 200 caracteres)

Responde ÚNICAMENTE con el array JSON, sin texto adicional ni fences. Ejemplo de formato esperado:
[{{"estado": "Alerta Severa", "titulo": "...", "descripcion": "...", "accion_recomendada": "..."}}]

Si no detectas problemas, devuelve un array vacío: []"""

    # Preparar request a DeepSeek
    headers = {
        "Authorization": f"Bearer {Config.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": Config.DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": "Eres un experto en análisis de logs de routers MikroTik y generación de alertas operativas."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.3,  # Baja temperatura para respuestas más deterministas
        "max_tokens": Config.AI_MAX_TOKENS
    }
    
    try:
        response = requests.post(
            Config.DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
            timeout=Config.AI_TIMEOUT_SEC
        )
        
        # Manejo de errores HTTP
        if response.status_code == 429:
            # TODO: implementar backoff/retry
            raise Exception(f"DeepSeek rate limit (429). TODO: implementar backoff.")
        
        if not response.ok:
            error_detail = response.text[:200]
            raise Exception(f"DeepSeek HTTP {response.status_code}: {error_detail}")
        
        data = response.json()
        
        # Extraer contenido de la respuesta
        if "choices" not in data or not data["choices"]:
            raise Exception("DeepSeek response missing 'choices'")
        
        content = data["choices"][0].get("message", {}).get("content", "")
        if not content:
            raise Exception("DeepSeek response empty content")
        
        # Limpieza robusta: eliminar fences de markdown si los hay
        content = content.strip()
        # Remover ```json ... ``` o ``` ... ```
        content = re.sub(r'^```(?:json)?\s*\n', '', content, flags=re.MULTILINE)
        content = re.sub(r'\n```\s*$', '', content, flags=re.MULTILINE)
        content = content.strip()
        
        # Parsear JSON
        try:
            alerts_raw = json.loads(content)
        except json.JSONDecodeError as je:
            logging.error("ai_analysis: JSON decode error. Content: %s", content[:500])
            raise Exception(f"DeepSeek returned invalid JSON: {je}")
        
        # Validar y normalizar estructura
        if not isinstance(alerts_raw, list):
            raise Exception(f"DeepSeek response no es una lista: {type(alerts_raw)}")
        
        alerts: List[Dict[str, Any]] = []
        for item in alerts_raw:
            if not isinstance(item, dict):
                logging.warning("ai_analysis: item no es dict, skip: %s", item)
                continue
            
            # Validar campos requeridos
            estado = item.get("estado", "")
            titulo = item.get("titulo", "")
            descripcion = item.get("descripcion", "")
            accion = item.get("accion_recomendada", "")
            
            if not all([estado, titulo, descripcion, accion]):
                logging.warning("ai_analysis: alerta incompleta, skip: %s", item)
                continue
            
            # Normalizar estado a taxonomía canónica
            estado_normalized = normalize_estado(estado)
            
            alerts.append({
                "estado": estado_normalized,
                "titulo": str(titulo)[:100],  # Truncar si excede
                "descripcion": str(descripcion)[:400],
                "accion_recomendada": str(accion)[:200]
            })
        
        logging.info("ai_analysis: DeepSeek generó %d alertas", len(alerts))
        return alerts
        
    except requests.exceptions.Timeout:
        raise Exception(f"DeepSeek timeout después de {Config.AI_TIMEOUT_SEC}s")
    except requests.exceptions.RequestException as e:
        raise Exception(f"DeepSeek request error: {e}")
    except Exception as e:
        # Re-raise con contexto
        raise Exception(f"analyze_with_deepseek falló: {e}")