"""
Modelo Device (router MikroTik):

Campos esperados:
- id (PK)
- tenant_id (FK)
- nombre_amigable
- ip
- puerto
- username (cifrado en reposo)
- password (cifrado en reposo)
- salud (verde|amarillo|rojo calculado por alertas)
- created_at, updated_at
"""
# class Device(Base): ...