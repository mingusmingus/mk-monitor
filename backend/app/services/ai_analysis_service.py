"""
Servicio de Análisis de IA Interno.

Actúa como una fachada (Facade) para la estrategia del Proveedor de IA.
Delega el análisis forense al proveedor activo configurado (ej. DeepSeek).
"""
import logging
from typing import Dict, Any, List, Optional
from .ai_providers.deepseek import DeepSeekProvider
# from .ai_providers.gemini import GeminiProvider # Futuro
from ..config import Config

logger = logging.getLogger(__name__)

def analyze_device_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza el contexto forense completo utilizando el Proveedor de IA configurado.

    Args:
        context (Dict[str, Any]): Datos estructurados del dispositivo (salud, logs, interfaces, etc.).

    Returns:
        Dict[str, Any]: Resultado del análisis, incluyendo diagnóstico y recomendaciones.
    """
    # Futura implementación: selección dinámica de proveedor basada en Config
    provider = DeepSeekProvider()

    logger.info("[INFO] Iniciando análisis forense con IA...")
    result = provider.analyze(context)
    logger.info("[INFO] Análisis de IA completado.")

    return result

# Deprecated / Wrapper Legacy para retrocompatibilidad
def analyze_logs(log_list: List[Any], device_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
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
    result = analyze_device_context(context)

    # Mapeo de mejor esfuerzo del nuevo formato 'analysis' al antiguo formato de Lista de Alertas
    analysis_text = result.get("analysis", "Sin análisis")
    recs = result.get("recommendations", [])
    rec_text = "; ".join(recs)

    # Retornar como una única alerta genérica
    return [{
        "estado": "Aviso",
        "titulo": "Reporte de Análisis IA",
        "descripcion": analysis_text[:512],
        "accion_recomendada": rec_text[:255]
    }]
