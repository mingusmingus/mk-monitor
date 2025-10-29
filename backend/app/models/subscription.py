"""
Modelo Subscription (gestión de plan comercial):

Campos esperados:
- id (PK)
- tenant_id (FK)
- plan (BASICMAAT | INTERMAAT | PROMAAT)
- status (active | past_due | canceled)
- current_period_start, current_period_end
- external_ref (id de proveedor de pagos)
- created_at, updated_at
"""
# class Subscription(Base): ...