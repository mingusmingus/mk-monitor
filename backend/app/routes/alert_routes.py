"""
Rutas de alertas:

- Listado, actualización de estado operativo y consulta por dispositivo.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, request, jsonify, g
from ..auth.decorators import require_auth
from ..models.alert import Alert

alert_bp = Blueprint("alerts", __name__)

@alert_bp.get("/alerts")
@require_auth()
def list_alerts():
    """
    Listado de alertas con filtros opcionales:
      - estado
      - device_id
      - fecha_inicio / fecha_fin
      - status_operativo
    Debe devolver solo alertas del tenant (g.tenant_id).
    """
    q = Alert.query.filter_by(tenant_id=g.tenant_id)

    estado = request.args.get("estado")
    if estado:
        q = q.filter(Alert.estado == estado)

    device_id = request.args.get("device_id", type=int)
    if device_id:
        q = q.filter(Alert.device_id == device_id)

    status_operativo = request.args.get("status_operativo")
    if status_operativo:
        q = q.filter(Alert.status_operativo == status_operativo)

    # TODO: filtros por fecha_inicio/fecha_fin en created_at/updated_at
    # fecha_inicio = request.args.get("fecha_inicio")
    # fecha_fin = request.args.get("fecha_fin")

    alerts = q.order_by(Alert.created_at.desc()).all()
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