"""
Modelo User (usuarios internos por tenant):

Campos esperados:
- id (PK)
- tenant_id (FK -> Tenant)
- email (único por tenant)
- password_hash (bcrypt)
- role ("admin" | "noc")
- is_active
- created_at, updated_at
"""
# class User(Base): ...