# Migraciones (Alembic)

Flujo básico:

1. Asegura variables de entorno de BD (`DATABASE_URL`) o archivo `infra/.env` cargado.
2. Crea revisión (autogenerate) cuando cambien los modelos:
   ```
   alembic -c backend/alembic.ini revision --autogenerate -m "descripcion"
   ```
3. Aplica migraciones pendientes:
   ```
   alembic -c backend/alembic.ini upgrade head
   ```
4. Retrocede un paso (con cuidado):
   ```
   alembic -c backend/alembic.ini downgrade -1
   ```

Notas:
- `env.py` importa todos los modelos para poblar `target_metadata`.
- La URL se resuelve en orden: CLI/ini > `DATABASE_URL` > `Config.SQLALCHEMY_DATABASE_URI`.
- Usa el Makefile en raíz: `make revision msg="descripcion"` / `make migrate`.