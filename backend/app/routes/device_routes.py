"""
Rutas para gestión de Dispositivos.

Provee endpoints para listar y crear dispositivos Mikrotik,
asegurando el cumplimiento de límites según el plan contratado.
"""
from flask import Blueprint, request, jsonify, g
from ..auth.decorators import require_auth
from ..models.device import Device
from ..db import db
from ..services import alert_service, device_service
from ..services.device_service import DeviceLimitReached
from ..__init__ import limiter

device_bp = Blueprint("devices", __name__)

@device_bp.get("/devices")
@require_auth()
def list_devices():
    """
    Lista los dispositivos pertenecientes al tenant actual.

    Incluye el estado de salud calculado en base a alertas activas.
    Nota: Las credenciales sensibles se excluyen de la respuesta.

    Returns:
        Response: Lista de objetos JSON representando los dispositivos.
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
@limiter.limit("5/minute; 50/hour", override_defaults=False)
def create_device():
    """
    Registra un nuevo dispositivo en el sistema.

    Requiere rol de 'admin'. Valida que el tenant no haya excedido el límite
    de dispositivos permitidos por su plan.

    Body:
        name (str): Nombre del dispositivo.
        ip_address (str): Dirección IP.
        port (int): Puerto de gestión.
        username (str): Usuario (se almacenará cifrado).
        password (str): Contraseña (se almacenará cifrada).

    Returns:
        Response: 201 Created con el ID del dispositivo.
                  402 Payment Required si se excede el límite del plan.
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
