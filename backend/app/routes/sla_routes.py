from flask import Blueprint, jsonify, g
from ..auth.decorators import require_auth
from ..services.sla_service import get_sla_metrics

sla_bp = Blueprint("sla", __name__)

@sla_bp.get("/sla/metrics")
@require_auth()
def sla_metrics():
    """
    Devuelve métricas KPI de SLA del tenant actual.
    {
      "tiempo_promedio_resolucion_severa_min": 42.5
    }
    """
    metrics = get_sla_metrics(g.tenant_id)
    return jsonify(metrics), 200