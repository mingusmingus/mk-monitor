"""
Internal AI Service.

Now acts as a facade for the AIProvider strategy.
Delegates analysis to the active provider (e.g., DeepSeek).
"""
import logging
from typing import Dict, Any, List, Optional
from .ai_providers.deepseek import DeepSeekProvider
# from .ai_providers.gemini import GeminiProvider # Future
from ..config import Config

logger = logging.getLogger(__name__)

def analyze_device_context(context: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyzes the full forensic context using the configured AI Provider.
    """
    # In the future, this could select provider based on Config
    provider = DeepSeekProvider()

    logger.info("Starting AI Forensic Analysis...")
    result = provider.analyze(context)
    logger.info("AI Analysis completed.")

    return result

# Deprecated / Legacy wrapper for backward compatibility if needed by other modules
# (Though we will update monitoring_service to use analyze_device_context)
def analyze_logs(log_list: List[Any], device_context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    """
    LEGACY: Adapts old log-only calls to the new provider structure if possible,
    or returns a simplified response.
    """
    logger.warning("Using legacy analyze_logs. Upgrade caller to analyze_device_context.")

    # Construct a minimal context from the logs
    context = {
        "context": device_context or {},
        "logs": log_list,
        "health": {},
        "interfaces": [],
        "telemetry": {},
        "heuristics": ["Legacy log analysis request"]
    }

    # Call the provider
    result = analyze_device_context(context)

    # Convert the new 'analysis' format back to the old List[Alert] format
    # This is a best-effort mapping.
    analysis_text = result.get("analysis", "No analysis")
    recs = result.get("recommendations", [])
    rec_text = "; ".join(recs)

    # Return as a single alert
    return [{
        "estado": "Aviso",
        "titulo": "AI Analysis Report",
        "descripcion": analysis_text[:512],
        "accion_recomendada": rec_text[:255]
    }]
