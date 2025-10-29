"""
Rutas de logs:

- Consulta histórica con filtros de fecha y dispositivo.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, request, jsonify, g
from ..auth.decorators import require_auth
from ..models.log_entry import LogEntry

log_bp = Blueprint("logs", __name__)

@log_bp.get("/devices/<int:device_id>/logs")
@require_auth()
def device_logs(device_id: int):
    """
    Query params: limit (5/10/20), fecha_inicio, fecha_fin.
    Devuelve logs paginados del dispositivo dentro del tenant.
    """
    limit = request.args.get("limit", default=10, type=int)
    limit = min(max(limit, 1), 50)

    # TODO: usar fecha_inicio/fecha_fin para filtrar rango
    # fecha_inicio = request.args.get("fecha_inicio")
    # fecha_fin = request.args.get("fecha_fin")

    q = LogEntry.query.filter_by(tenant_id=g.tenant_id, device_id=device_id)
    logs = q.order_by(LogEntry.timestamp_equipo.desc()).limit(limit).all()

    result = [{
        "id": l.id,
        "raw_log": l.raw_log,
        "log_level": l.log_level,
        "timestamp_equipo": l.timestamp_equipo.isoformat() if l.timestamp_equipo else None,
        "created_at": l.created_at.isoformat() if l.created_at else None,
    } for l in logs]
    return jsonify(result), 200