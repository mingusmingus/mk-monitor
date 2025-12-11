"""
Rutas para gestión de Suscripciones.

Provee endpoints para consultar el estado actual del plan contratado por el Tenant,
incluyendo límites y uso de recursos.
"""
from flask import Blueprint, jsonify, g
from ..auth.decorators import require_auth
from ..services.subscription_service import get_current_subscription

sub_bp = Blueprint("subscriptions", __name__)

@sub_bp.get("/subscription/status")
@require_auth()
def subscription_status():
    """
    Obtiene el estado de la suscripción del Tenant actual.

    Returns:
        Response: Objeto JSON con detalles del plan, límites y uso actual.
                  Indica si la cuenta está suspendida.
    """
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
