"""
Rutas de salud/monitor:

- Endpoint simple /api/health para verificar estado del servicio.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint, jsonify, g
from ..auth.decorators import require_auth
from ..models.device import Device
from ..models.alert import Alert
from ..services import alert_service  # añadido

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
    try:
        devices = Device.query.filter_by(tenant_id=g.tenant_id).all()
        result = []
        for d in devices:
            health = alert_service.compute_device_health(g.tenant_id, d.id)
            result.append({
                "device_id": d.id,
                "name": d.name,
                "health_status": health
            })
        return jsonify(result), 200
    except Exception:
        # Manejo de errores consistente sin exponer detalles internos
        return jsonify({"error": "Error al obtener estado de salud"}), 500
