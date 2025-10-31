"""
Rutas de suscripción:

- Estado de plan del tenant, upsell y gestión de límites.
"""
from flask import Blueprint, jsonify, g
from ..auth.decorators import require_auth
from ..services.subscription_service import get_current_subscription

# Ajuste: sin url_prefix aquí; se monta bajo /api en create_app
sub_bp = Blueprint("subscriptions", __name__)

@sub_bp.get("/subscription/status")
@require_auth()
def subscription_status():
    info = get_current_subscription(g.tenant_id)
    resp = {
        "plan": info["plan_name"],
        "max_devices": info["max_devices"],
        "used": info["devices_registrados"],
        "status_pago": info["status_pago"],
    }
    if info["status_pago"] == "suspendido":
        resp["suspended"] = True
    return jsonify(resp), 200