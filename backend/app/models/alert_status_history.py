"""
Modelo AlertStatusHistory (histórico de estados para SLA):

Campos esperados:
- id (PK)
- alert_id (FK)
- old_status, new_status
- changed_by (user_id o sistema)
- changed_at (timestamp)
- comentario (opcional)
"""
# class AlertStatusHistory(Base): ...