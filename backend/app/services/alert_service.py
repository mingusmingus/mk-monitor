"""
Servicio de Gestión de Alertas.

Este servicio encapsula la lógica de negocio relacionada con las alertas:
- Creación y consulta con filtros.
- Gestión del ciclo de vida (cambios de estado operativo).
- Cálculo de indicadores de salud de dispositivos basados en alertas activas.
- Registro histórico para cumplimiento de SLA.
"""
from datetime import datetime
from typing import Dict, Any, List, Optional
from ..models.alert import Alert
from ..models.alert_status_history import AlertStatusHistory
from ..db import db

def list_alerts(tenant_id: int, filtros: Dict[str, Any]) -> List[Alert]:
    """
    Lista alertas aplicando filtros de negocio.

    Args:
        tenant_id (int): ID del tenant.
        filtros (Dict[str, Any]): Diccionario de filtros (estado, device_id, status_operativo).

    Returns:
        List[Alert]: Lista de objetos Alert que coinciden con los criterios.
    """
    q = Alert.query.filter_by(tenant_id=tenant_id)

    estado = filtros.get("estado")
    if estado:
        q = q.filter(Alert.estado == estado)

    device_id = filtros.get("device_id")
    # Manejo robusto si filtros viene de request.args o dict plano
    if device_id and hasattr(device_id, "isdigit") and str(device_id).isdigit():
         q = q.filter(Alert.device_id == int(device_id))
    elif isinstance(device_id, int):
         q = q.filter(Alert.device_id == device_id)

    status_operativo = filtros.get("status_operativo")
    if status_operativo:
        q = q.filter(Alert.status_operativo == status_operativo)

    return q.order_by(Alert.created_at.desc()).all()

def update_alert_status(alert_id: int, user_id: int, tenant_id: int, nuevo_status: str, comentario: Optional[str]) -> Alert:
    """
    Actualiza el estado operativo de una alerta y registra el cambio en el histórico.

    Args:
        alert_id (int): ID de la alerta.
        user_id (int): ID del usuario que realiza el cambio.
        tenant_id (int): ID del tenant para validación de propiedad.
        nuevo_status (str): Nuevo estado ('Pendiente', 'En curso', 'Resuelta').
        comentario (Optional[str]): Comentario opcional sobre la acción.

    Returns:
        Alert: La instancia de la alerta actualizada.

    Raises:
        ValueError: Si la alerta no existe o no pertenece al tenant.
    """
    alert = Alert.query.filter_by(id=alert_id, tenant_id=tenant_id).first()
    if not alert:
        raise ValueError("[ERROR] Alerta no encontrada")

    prev = alert.status_operativo
    alert.status_operativo = nuevo_status
    alert.comentario_ultimo = comentario
    alert.updated_at = datetime.utcnow()

    # Registro de auditoría
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
    Calcula el estado de salud de un dispositivo basado en sus alertas activas.

    Reglas:
      - 'rojo': Si existen alertas activas de severidad 'Alerta Severa' o 'Alerta Crítica'.
      - 'amarillo': Si existen alertas activas de severidad 'Alerta Menor'.
      - 'verde': Si no existen alertas activas relevantes.

    Args:
        tenant_id (int): ID del tenant.
        device_id (int): ID del dispositivo.

    Returns:
        str: Estado de salud ('rojo', 'amarillo', 'verde').
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
