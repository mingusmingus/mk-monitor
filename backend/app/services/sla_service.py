"""
Servicio de SLA:

- Calcula métricas de tiempo en cada estado (Pendiente/En curso/Resuelta).
- Genera reportes de cumplimiento por tenant/dispositivo.
"""
from datetime import datetime, timedelta
from statistics import mean
from typing import Dict, List, Optional
from ..models.alert import Alert
from ..models.alert_status_history import AlertStatusHistory

def get_sla_metrics(tenant_id: int) -> Dict[str, float]:
    """
    Calcula métricas del mes actual.
    - tiempo_promedio_resolucion_severa_min: promedio (en minutos) desde created_at
      hasta el primer cambio a "Resuelta" para alertas Severas/Críticas.
    Nota: No manejamos zona horaria explícita (se asume UTC en DB). Ajustar si es necesario.
    """
    now = datetime.utcnow()
    month_start = datetime(now.year, now.month, 1)

    # Alertas objetivo
    alerts = (Alert.query
              .filter_by(tenant_id=tenant_id)
              .filter(Alert.created_at >= month_start)
              .filter(Alert.estado.in_(("Alerta Severa", "Alerta Crítica")))
              .all())

    duraciones: List[float] = []
    for a in alerts:
        # Buscar primer cambio a Resuelta
        hist = (AlertStatusHistory.query
                .filter_by(alert_id=a.id)
                .filter(AlertStatusHistory.new_status_operativo == "Resuelta")
                .order_by(AlertStatusHistory.changed_at.asc())
                .first())
        if hist:
            delta = hist.changed_at - a.created_at
            duraciones.append(delta.total_seconds() / 60.0)

    promedio = mean(duraciones) if duraciones else 0.0
    return {
        "tiempo_promedio_resolucion_severa_min": promedio
    }
