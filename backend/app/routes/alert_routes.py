"""
Rutas de alertas:

- Listado, actualización de estado operativo y consulta por dispositivo.
"""
from flask import Blueprint, request, jsonify, g
from ..auth.decorators import require_auth
from ..services import alert_service

alert_bp = Blueprint("alerts", __name__)

@alert_bp.get("/alerts")
@require_auth()
def list_alerts():
    """
    Listado de alertas con filtros opcionales:
      - estado
      - device_id
      - fecha_inicio / fecha_fin (TODO)
      - status_operativo
    Solo alertas del tenant (g.tenant_id).
    """
    alerts = alert_service.list_alerts(g.tenant_id, request.args)
    result = [{
        "id": a.id,
        "device_id": a.device_id,
        "estado": a.estado,
        "titulo": a.titulo,
        "descripcion": a.descripcion,
        "accion_recomendada": a.accion_recomendada,
        "status_operativo": a.status_operativo,
        "comentario_ultimo": a.comentario_ultimo,
        "created_at": a.created_at.isoformat() if a.created_at else None,
        "updated_at": a.updated_at.isoformat() if a.updated_at else None,
    } for a in alerts]
    return jsonify(result), 200