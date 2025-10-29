"""
Rutas de dispositivos:

- CRUD de equipos MikroTik y validación de límites por plan.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, request, jsonify, g

from ..auth.decorators import require_auth
from ..models.device import Device

device_bp = Blueprint("devices", __name__)

@device_bp.get("/devices")
@require_auth()
def list_devices():
    """
    Devuelve SOLO los dispositivos del tenant actual g.tenant_id.
    Incluye health_status calculado (por ahora 'verde' hardcodeado).
    """
    devices = Device.query.filter_by(tenant_id=g.tenant_id).all()
    result = []
    for d in devices:
        result.append({
            "id": d.id,
            "name": d.name,
            "ip_address": d.ip_address,
            "port": d.port,
            "firmware_version": d.firmware_version,
            "location": d.location,
            "wan_type": d.wan_type,
            "created_at": d.created_at.isoformat() if d.created_at else None,
            "health_status": "verde",  # TODO: calcular según alertas activas
        })
    return jsonify(result), 200

@device_bp.post("/devices")
@require_auth(role="admin")
def create_device():
    """
    Crea un dispositivo. Solo admin.
    - Validar límite de plan del tenant (TODO).
    - Si supera límite: 402 + { upsell: true, message: "..."}
    - Si OK, almacenar device (credenciales deben venir cifradas o cifrarse aquí).
    Body: { name, ip_address, port, username_encrypted, password_encrypted, ... }
    """
    data = request.get_json(silent=True) or {}

    # TODO: verificar límites del plan para g.tenant_id
    # if supera_limite:
    #     return jsonify({"upsell": True, "message": "Has alcanzado el límite de tu plan."}), 402

    device = Device(
        tenant_id=g.tenant_id,
        name=data.get("name"),
        ip_address=data.get("ip_address"),
        port=int(data.get("port", 22)),
        username_encrypted=data.get("username_encrypted"),
        password_encrypted=data.get("password_encrypted"),
        firmware_version=data.get("firmware_version"),
        location=data.get("location"),
        wan_type=data.get("wan_type"),
    )
    from ..db import db
    db.session.add(device)
    db.session.commit()

    return jsonify({"id": device.id}), 201