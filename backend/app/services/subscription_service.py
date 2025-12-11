"""
Servicio de Gestión de Suscripciones.

Provee funcionalidades para:
- Determinar el plan comercial vigente y sus límites.
- Validar si un tenant puede agregar nuevos recursos (dispositivos).
- Gestionar la creación de suscripciones iniciales.
"""
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models.subscription import Subscription
from ..models.device import Device
from ..models.tenant import Tenant
from sqlalchemy import func
from ..db import db

# Límites de dispositivos por Plan
PLAN_LIMITS: dict[str, Optional[int]] = {
    "BASICMAAT": 5,
    "INTERMAAT": 15,
    "PROMAAT": None,  # None representa ilimitado
}

def _resolve_current_plan(tenant: Tenant) -> str:
    """Resuelve el nombre del plan activo para un tenant."""
    return (tenant.plan or "BASICMAAT").upper()

def get_current_subscription(tenant_id: int) -> Dict[str, Any]:
    """
    Obtiene el estado actual de la suscripción del tenant.

    Args:
        tenant_id (int): ID del tenant.

    Returns:
        Dict[str, Any]: Información consolidada del plan, límites, uso y estado de pago.
    """
    tenant = Tenant.query.filter_by(id=tenant_id).first()
    if not tenant:
        return {
            "plan_name": "BASICMAAT",
            "max_devices": PLAN_LIMITS["BASICMAAT"],
            "status_pago": "suspendido",
            "devices_registrados": 0,
        }

    # Buscar suscripción activa (la más reciente que no haya expirado o sea indefinida)
    _now = datetime.utcnow()
    sub = (Subscription.query
           .filter(Subscription.tenant_id == tenant_id)
           .filter((Subscription.activo_hasta == None) | (Subscription.activo_hasta >= _now))  # noqa: E711
           .order_by(Subscription.activo_hasta.desc().nullslast())
           .first())

    plan_name = _resolve_current_plan(tenant if tenant else None)

    # Determinar max_devices: Priorizar suscripción explícita, sino fallback al default del plan
    # Nota: En DB, 0 puede usarse para representar ilimitado si el campo es integer no nulo,
    # pero aquí la lógica maneja None como ilimitado.
    if sub and sub.max_devices is not None:
         max_devices = sub.max_devices
    else:
         max_devices = PLAN_LIMITS.get(plan_name, 5)

    used = Device.query.filter_by(tenant_id=tenant_id).count()
    return {
        "plan_name": plan_name,
        "max_devices": max_devices,
        "status_pago": tenant.status_pago or "activo",
        "devices_registrados": used,
    }

def can_add_device(tenant_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Valida si un tenant tiene capacidad para agregar un nuevo dispositivo.

    Args:
        tenant_id (int): ID del tenant.

    Returns:
        Tuple[bool, Optional[Dict[str, Any]]]:
            - bool: True si puede agregar, False si no.
            - dict: Información para upsell si la validación falla (mensaje y sugerencia).
    """
    info = get_current_subscription(tenant_id)

    # Validación de estado de cuenta
    if info["status_pago"] == "suspendido":
        return False, {
            "upsell": True,
            "message": "Tu suscripción está suspendida. Reactiva tu plan para poder agregar dispositivos.",
            "required_plan_hint": "Ponte al día con el pago para reactivar."
        }

    max_devices = info["max_devices"]
    used = info["devices_registrados"]

    if max_devices is None:
        return True, None  # Plan Ilimitado

    if used >= max_devices:
        plan = info["plan_name"]
        # Lógica de Upsell
        if plan == "BASICMAAT":
            return False, {
                "upsell": True,
                "message": "Has alcanzado el límite de 5 dispositivos de BASICMAAT.",
                "required_plan_hint": "Actualiza a INTERMAAT (hasta 15 dispositivos)."
            }
        elif plan == "INTERMAAT":
            return False, {
                "upsell": True,
                "message": "Has alcanzado el límite de 15 dispositivos de INTERMAAT.",
                "required_plan_hint": "Actualiza a PROMAAT (dispositivos ilimitados)."
            }
        else:
            return False, {
                "upsell": True,
                "message": "Límite de dispositivos alcanzado.",
                "required_plan_hint": "Contacta soporte para ampliar tu plan."
            }

    return True, None

def create_initial_subscription(tenant_id: int, plan: str = "BASICMAAT") -> Subscription:
    """
    Genera la suscripción inicial para un nuevo tenant.

    Args:
        tenant_id (int): ID del tenant.
        plan (str): Nombre del plan (default 'BASICMAAT').

    Returns:
        Subscription: Objeto de suscripción creado (pendiente de commit).
    """
    p = (plan or "BASICMAAT").upper()
    max_devices_limit = PLAN_LIMITS.get(p, PLAN_LIMITS["BASICMAAT"])

    # Periodo de prueba/inicial de 30 días
    activo_hasta = datetime.utcnow() + timedelta(days=30)

    # Manejo de ilimitado (None) para columna Integer: usamos 0 o un número muy alto.
    # Asumimos que la lógica de negocio interpreta 0 como ilimitado o manejamos un valor alto.
    # Para consistencia con el modelo, si es None lo dejamos como 0 si la columna no acepta Nulls,
    # o Null si lo permite. Revisando modelo: max_devices int not null default 5.
    # Ajuste: usaremos un valor centinela o el límite real.
    # Si PROMAAT es ilimitado, ponemos un número alto (ej. 10000) o modificamos la lógica de lectura.
    # Por ahora, si es None (PROMAAT), ponemos 999999.

    val_max_devices = max_devices_limit if max_devices_limit is not None else 999999

    sub = Subscription(
        tenant_id=tenant_id,
        plan_name=p,
        max_devices=val_max_devices,
        activo_hasta=activo_hasta,
    )
    db.session.add(sub)
    return sub
