"""
Modelo LogEntry (entrada de log crudo/normalizado):

Campos esperados:
- id (PK)
- tenant_id (FK)
- device_id (FK)
- raw (texto del log)
- normalized (opcional)
- timestamp_log (cuando ocurrió en el equipo)
- created_at
"""
# class LogEntry(Base): ...