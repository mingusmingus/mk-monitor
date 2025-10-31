"""
Rutas de salud/monitor:

- Endpoint simple /api/health para verificar estado del servicio.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, jsonify, g
from ..auth.decorators import require_auth
from ..models.device import Device
from ..models.alert import Alert

health_bp = Blueprint("health", __name__)

@health_bp.get("/health/devices")
@require_auth()
def health_devices():
    """
    Devuelve lista de { device_id, name, health_status } para todos los equipos del tenant.
    Reglas:
      - rojo si el device tiene Alerta Severa o Crítica no resuelta
      - amarillo si tiene Alerta Menor activa
      - verde caso contrario
    Seguridad: No exponer campos internos ni credenciales.
    """
    devices = Device.query.filter_by(tenant_id=g.tenant_id).all()
    result = []
    for d in devices:
        # TODO: calcular según alertas activas no resueltas
        # alerts = Alert.query.filter_by(tenant_id=g.tenant_id, device_id=d.id).filter(Alert.status_operativo != "Resuelta").all()
        # if any(a.estado in ("Alerta Severa", "Alerta Crítica") for a in alerts): health = "rojo"
        # elif any(a.estado == "Alerta Menor" for a in alerts): health = "amarillo"
        # else: health = "verde"
        health = "verde"
        result.append({
            "device_id": d.id,
            "name": d.name,
            "health_status": health
        })
    return jsonify(result), 200
