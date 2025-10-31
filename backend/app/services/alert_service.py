"""
Servicio de alertas:

- Gestiona ciclo de vida de Alert (crear, actualizar estado, cerrar).
- Calcula salud del equipo (semáforo) según alertas activas.
- Mantiene histórico AlertStatusHistory para SLA.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..models.alert import Alert
from ..models.alert_status_history import AlertStatusHistory
from ..db import db

def list_alerts(tenant_id: int, filtros: Dict[str, Any]) -> List[Alert]:
    """
    Filtros soportados: estado, device_id, fecha_inicio, fecha_fin, status_operativo
    """
    q = Alert.query.filter_by(tenant_id=tenant_id)

    estado = filtros.get("estado")
    if estado:
        q = q.filter(Alert.estado == estado)

    device_id = filtros.get("device_id", type=int) if hasattr(filtros, "get") else filtros.get("device_id")
    if device_id:
        q = q.filter(Alert.device_id == int(device_id))

    status_operativo = filtros.get("status_operativo")
    if status_operativo:
        q = q.filter(Alert.status_operativo == status_operativo)

    # TODO: filtros por fecha_inicio/fecha_fin en created_at/updated_at (zona horaria)
    # fecha_inicio = filtros.get("fecha_inicio")
    # fecha_fin = filtros.get("fecha_fin")

    return q.order_by(Alert.created_at.desc()).all()

def update_alert_status(alert_id: int, user_id: int, tenant_id: int, nuevo_status: str, comentario: Optional[str]) -> Alert:
    """
    Verifica pertenencia por tenant, actualiza estado/comentario y guarda histórico.
    """
    alert = Alert.query.filter_by(id=alert_id, tenant_id=tenant_id).first()
    if not alert:
        raise ValueError("Alerta no encontrada")

    prev = alert.status_operativo
    alert.status_operativo = nuevo_status
    alert.comentario_ultimo = comentario
    alert.updated_at = datetime.utcnow()

    # Auditoría: quién y cuándo (UTC). Importante si pasa a "Resuelta" para SLA.
    hist = AlertStatusHistory(
        alert_id=alert.id,
        previous_status_operativo=prev,
        new_status_operativo=nuevo_status,
        changed_by_user_id=user_id,
        changed_at=datetime.utcnow()
    )
    db.session.add(hist)
    db.session.commit()
    return alert

def compute_device_health(tenant_id: int, device_id: int) -> str:
    """
    Reglas:
      - rojo si hay alerta activa (status_operativo != "Resuelta") con estado in ["Alerta Severa","Alerta Crítica"]
      - amarillo si hay alerta activa con estado == "Alerta Menor"
      - verde en cualquier otro caso
    """
    activos = (Alert.query
               .filter_by(tenant_id=tenant_id, device_id=device_id)
               .filter(Alert.status_operativo != "Resuelta")
               .all())

    if any(a.estado in ("Alerta Severa", "Alerta Crítica") for a in activos):
        return "rojo"
    if any(a.estado == "Alerta Menor" for a in activos):
        return "amarillo"
    return "verde"