"""
Servicio de suscripciones:

- Aplica límites por plan (BASICMAAT: 5, INTERMAAT: 15, PROMAAT: ilimitado).
- Estado de pago del tenant.
"""
from typing import Tuple, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models.subscription import Subscription
from ..models.device import Device
from ..models.tenant import Tenant
from sqlalchemy import func
from ..db import db

PLAN_LIMITS: dict[str, Optional[int]] = {
    "BASICMAAT": 5,
    "INTERMAAT": 15,
    "PROMAAT": None,  # Ilimitado
}

def _resolve_current_plan(tenant: Tenant) -> str:
    # Plan efectivo: si hubiera múltiples, tomaría el activo más reciente; por ahora usamos Tenant.plan
    return (tenant.plan or "BASICMAAT").upper()

def get_current_subscription(tenant_id: int) -> Dict[str, Any]:
    """
    Retorna información ejecutiva de la suscripción actual del tenant.
    {
      "plan_name": ...,
      "max_devices": ... (None => ilimitado),
      "status_pago": "activo" | "suspendido",
      "devices_registrados": <count>,
    }
    """
    tenant = Tenant.query.filter_by(id=tenant_id).first()
    if not tenant:
        # En escenarios reales, lanzaríamos error; aquí devolvemos defaults seguros.
        return {
            "plan_name": "BASICMAAT",
            "max_devices": PLAN_LIMITS["BASICMAAT"],
            "status_pago": "suspendido",
            "devices_registrados": 0,
        }

    # Opcional: considerar la suscripción más reciente por activo_hasta
    _now = datetime.utcnow()
    sub = (Subscription.query
           .filter(Subscription.tenant_id == tenant_id)
           .filter((Subscription.activo_hasta == None) | (Subscription.activo_hasta >= _now))  # noqa: E711
           .order_by(Subscription.activo_hasta.desc().nullslast())
           .first())

    plan_name = _resolve_current_plan(tenant if tenant else None)
    # Si el registro de suscripción setea un max_devices custom, respetarlo; si no, usar regla por plan
    max_devices = sub.max_devices if sub and sub.max_devices is not None else PLAN_LIMITS.get(plan_name, 5)

    used = Device.query.filter_by(tenant_id=tenant_id).count()
    return {
        "plan_name": plan_name,
        "max_devices": max_devices,
        "status_pago": tenant.status_pago or "activo",
        "devices_registrados": used,
    }

def can_add_device(tenant_id: int) -> Tuple[bool, Optional[Dict[str, Any]]]:
    """
    Devuelve (puede_agregar: bool, razon: dict|None).
    Si False, razón contiene payload para upsell (message, required_plan_hint).
    """
    info = get_current_subscription(tenant_id)
    # Bloqueo comercial por suspensión
    if info["status_pago"] == "suspendido":
        return False, {
            "upsell": True,
            "message": "Tu suscripción está suspendida. Reactiva tu plan para poder agregar dispositivos.",
            "required_plan_hint": "Ponte al día con el pago para reactivar."
        }

    max_devices = info["max_devices"]
    used = info["devices_registrados"]

    if max_devices is None:
        return True, None  # Ilimitado (PROMAAT)

    if used >= max_devices:
        plan = info["plan_name"]
        # Sugerencia de upgrade
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
    Crea una suscripción inicial para el tenant con límites por plan.
    - No maneja cobros; deja activo_hasta por defecto a 30 días desde ahora.
    - Si el plan es inválido, cae en BASICMAAT.
    """
    p = (plan or "BASICMAAT").upper()
    max_devices = PLAN_LIMITS.get(p, PLAN_LIMITS["BASICMAAT"])
    # Periodo inicial simbólico de 30 días
    activo_hasta = datetime.utcnow() + timedelta(days=30)
    sub = Subscription(
        tenant_id=tenant_id,
        plan_name=p,
        max_devices=max_devices if max_devices is not None else 0,  # None no cabe en Integer; usar 0 como 'ilimitado'
        activo_hasta=activo_hasta,
    )
    db.session.add(sub)
    # commit se realiza en el llamador (transacción envolvente)
    return sub