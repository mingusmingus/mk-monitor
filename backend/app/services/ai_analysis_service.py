"""
Servicio de Análisis de IA Interno.

Actúa como una fachada (Facade) para la estrategia del Proveedor de IA.
Delega el análisis forense al proveedor activo configurado (ej. DeepSeek, Gemini).
"""
import logging
import json
import asyncio
from typing import Dict, Any, List, Optional
from backend.app.core.ai.factory import get_ai_provider

logger = logging.getLogger(__name__)

async def analyze_device_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza el contexto forense completo utilizando el Proveedor de IA configurado.

    Args:
        context (Dict[str, Any]): Datos estructurados del dispositivo (salud, logs, interfaces, etc.).

    Returns:
        Dict[str, Any]: Resultado del análisis, incluyendo diagnóstico y recomendaciones.
    """
    provider = get_ai_provider()
    logger.info(f"[INFO] Iniciando análisis forense con proveedor: {provider.__class__.__name__}")

    # Prepare context string and prompt template
    context_str = json.dumps(context, indent=2)

    # We could move this prompt to a constant or configuration
    prompt_template = """
You are a MTCINE (MikroTik Certified Inter-networking Engineer) and a Lead Network Security Architect.
Your goal is to analyze deep forensic data from a MikroTik router and provide a structured diagnosis.

Input: JSON containing:
- hardware_health: Voltage, Temperature, CPU, Memory.
- interface_errors: Stats for interfaces with traffic or errors.
- security_posture: Open ports/services.
- recent_logs: Sanitized system logs.
- topology: Neighbors and routes.

Output: Strict JSON format with the following keys:
{
  "status": "CRITICAL" | "WARNING" | "HEALTHY",
  "summary": "Short title of the problem (e.g., Cable Failure on Ether2)",
  "technical_analysis": "Detailed explanation of why...",
  "security_audit": "Analysis of open ports (e.g., Close Telnet)",
  "recommendations": ["Step 1", "Step 2"],
  "confidence_score": 0.95
}

Rules:
1. Be precise and technical but clear.
2. If you see 'fcs-error', suspect Layer 1 (cable/connector).
3. If you see Telnet/FTP enabled, flag as SECURITY RISK.
4. If CPU is high, check for loops or heavy firewall rules.
5. If voltage is low (<10V for 12V systems), flag as power issue.
6. Ignore minor log noise. Focus on warnings, errors, and critical state changes.
"""

    try:
        # Note: analyze is now async
        result = await provider.analyze(context_str, prompt_template)
        logger.info("[INFO] Análisis de IA completado exitosamente.")
        return result
    except Exception as e:
        logger.error(f"[ERROR] Falló el análisis de IA: {e}")
        # Fallback to a safe response structure
        return {
            "status": "WARNING",
            "summary": "AI Analysis Failed",
            "technical_analysis": f"Internal error during AI analysis: {str(e)}",
            "security_audit": "N/A",
            "recommendations": ["Check backend logs"],
            "confidence_score": 0.0
        }

# Deprecated / Wrapper Legacy para retrocompatibilidad
async def analyze_logs(log_list: List[Any], device_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    LEGACY: Adapta llamadas antiguas (solo logs) a la nueva estructura de proveedor.

    Warning:
        Este método está obsoleto. Se recomienda migrar a `analyze_device_context`.

    Args:
        log_list (List[Any]): Lista de logs.
        device_context (Optional[Dict[str, Any]]): Contexto opcional del dispositivo.

    Returns:
        List[Dict[str, Any]]: Lista simplificada de alertas simuladas basada en el análisis.
    """
    logger.warning("[WARNING] Usando método legado 'analyze_logs'. Actualizar invocador a 'analyze_device_context'.")

    # Construir un contexto mínimo a partir de los logs
    context = {
        "context": device_context or {},
        "logs": log_list,
        "health": {},
        "interfaces": [],
        "telemetry": {},
        "heuristics": ["Solicitud de análisis de logs legado"]
    }

    # Invocar al proveedor
    result = await analyze_device_context(context)

    # Mapeo de mejor esfuerzo del nuevo formato 'technical_analysis' al antiguo formato de Lista de Alertas
    analysis_text = result.get("technical_analysis") or result.get("summary", "Sin análisis")
    recs = result.get("recommendations", [])
    rec_text = "; ".join(recs)

    # Retornar como una única alerta genérica
    return [{
        "estado": "Aviso",
        "titulo": result.get("summary", "Reporte de Análisis IA"),
        "descripcion": analysis_text[:512],
        "accion_recomendada": rec_text[:255]
    }]
