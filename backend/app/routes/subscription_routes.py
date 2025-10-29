"""
Rutas de suscripción:

- Estado de plan del tenant, upsell y gestión de límites.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, jsonify, g
from ..auth.decorators import require_auth
from ..models.subscription import Subscription
from ..models.device import Device
from sqlalchemy import func
from datetime import datetime

sub_bp = Blueprint("subscriptions", __name__, url_prefix="/api/subscriptions")

@sub_bp.get("/subscription/status")
@require_auth()
def subscription_status():
    """
    Devuelve info de la suscripción actual del tenant:
      - plan actual
      - max_devices
      - usados
      - status_pago
    Nota: el plan efectivo puede leerse de la fila más reciente con activo_hasta >= now().
    """
    now = datetime.utcnow()
    sub = (Subscription.query
           .filter(Subscription.tenant_id == g.tenant_id)
           .order_by(Subscription.activo_hasta.desc().nullslast())
           .first())

    used = Device.query.filter_by(tenant_id=g.tenant_id).count()
    return jsonify({
        "plan": sub.plan_name if sub else "BASICMAAT",
        "max_devices": sub.max_devices if sub else 5,
        "used": used,
        # status_pago real debería venir de Tenant; aquí omitido por simplicidad
        "status_pago": "activo"  # TODO: leer de Tenant.status_pago
    }), 200