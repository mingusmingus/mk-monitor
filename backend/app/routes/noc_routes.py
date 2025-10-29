"""
Rutas NOC:

- Acciones del operador (marcar En curso/Resuelta, comentar).
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, request, jsonify, g
from ..auth.decorators import require_auth
from ..models.alert import Alert
from ..models.alert_status_history import AlertStatusHistory
from ..db import db

noc_bp = Blueprint("noc", __name__)

@noc_bp.patch("/alerts/<int:alert_id>/status")
@require_auth()  # Operadores NOC o Admin
def update_alert_status(alert_id: int):
    """
    Body: { status_operativo, comentario }
    Reglas:
      - Solo usuarios del mismo tenant (enforced por query).
      - Operador NOC puede marcar "En curso" o "Resuelta".
      - Guardar histórico en AlertStatusHistory.
    """
    data = request.get_json(silent=True) or {}
    new_status = data.get("status_operativo")
    comentario = data.get("comentario")

    alert = Alert.query.filter_by(id=alert_id, tenant_id=g.tenant_id).first()
    if not alert:
        return jsonify({"error": "Alerta no encontrada"}), 404

    # TODO: validar permisos/rol si se requiere política específica
    prev = alert.status_operativo
    alert.status_operativo = new_status
    alert.comentario_ultimo = comentario

    hist = AlertStatusHistory(
        alert_id=alert.id,
        previous_status_operativo=prev,
        new_status_operativo=new_status,
        changed_by_user_id=g.user_id
    )
    db.session.add(hist)
    db.session.commit()

    return jsonify({"id": alert.id, "status_operativo": alert.status_operativo}), 200
