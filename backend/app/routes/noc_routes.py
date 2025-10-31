"""
Rutas NOC:

- Acciones del operador (marcar En curso/Resuelta, comentar).
"""
from flask import Blueprint, request, jsonify, g
from ..auth.decorators import require_auth
from ..services import alert_service

noc_bp = Blueprint("noc", __name__)

@noc_bp.patch("/alerts/<int:alert_id>/status")
@require_auth()  # Operadores NOC o Admin
def update_alert_status(alert_id: int):
    """
    Body: { status_operativo, comentario }
    - Solo usuarios del mismo tenant (enforced en service).
    - Registra histórico para SLA.
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get("status_operativo")
    comentario = data.get("comentario")
    if new_status not in {"Pendiente", "En curso", "Resuelta"}:
        return jsonify({"error": "status_operativo inválido"}), 400

    try:
        alert = alert_service.update_alert_status(
            alert_id=alert_id,
            user_id=g.user_id,
            tenant_id=g.tenant_id,
            nuevo_status=new_status,
            comentario=comentario
        )
    except ValueError:
        return jsonify({"error": "Alerta no encontrada"}), 404

    return jsonify({"id": alert.id, "status_operativo": alert.status_operativo}), 200
