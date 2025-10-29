"""
Modelo Alert (alertas operativas generadas por IA):

Campos esperados:
- id (PK)
- tenant_id (FK)
- device_id (FK)
- estado ("Aviso" | "Alerta Menor" | "Alerta Severa" | "Alerta Crítica")
- accion_recomendada (texto corto)
- status_operativo ("Pendiente" | "En curso" | "Resuelta")
- comentario_ultimo
- created_at, updated_at
"""
# class Alert(Base): ...