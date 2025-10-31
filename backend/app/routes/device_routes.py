"""
Rutas de dispositivos:

- CRUD de equipos MikroTik y validación de límites por plan.
"""
from flask import Blueprint, request, jsonify, g
from ..auth.decorators import require_auth
from ..models.device import Device
from ..db import db
from ..services import alert_service, device_service
from ..services.device_service import DeviceLimitReached

device_bp = Blueprint("devices", __name__)

@device_bp.get("/devices")
@require_auth()
def list_devices():
    """
    Devuelve SOLO los dispositivos del tenant actual g.tenant_id.
    Incluye health_status calculado.
    Importante: NO exponer credenciales cifradas (username_encrypted/password_encrypted) en la salida JSON.
    """
    devices = device_service.list_devices_for_tenant(g.tenant_id)
    result = []
    for d in devices:
        health = alert_service.compute_device_health(g.tenant_id, d.id)
        result.append({
            "id": d.id,
            "name": d.name,
            "ip_address": d.ip_address,
            "port": d.port,
            "firmware_version": d.firmware_version,
            "location": d.location,
            "wan_type": d.wan_type,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "health_status": health,
        })
    return jsonify(result), 200

@device_bp.post("/devices")
@require_auth(role="admin")
def create_device():
    """
    Crea un dispositivo. Solo admin.
    - Valida límite de plan del tenant.
    - Si supera límite: 402 + { upsell: true, message, required_plan_hint }
    - Si OK, almacena device cifrando credenciales si vinieran en claro.
    Body: { name, ip_address, port, username(_encrypted)?, password(_encrypted)?, ... }
    """
    data = request.get_json(silent=True) or {}
    try:
        device = device_service.create_device(g.tenant_id, data)
        return jsonify({"id": device.id}), 201
    except DeviceLimitReached as e:
        return jsonify({
            "upsell": True,
            "message": e.message,
            "required_plan_hint": e.required_plan_hint
        }), 402