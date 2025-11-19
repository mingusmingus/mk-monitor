# Tareas simples para migraciones Alembic

.PHONY: migrate revision

migrate:
	alembic upgrade head

revision:
	@if [ -z "$(msg)" ]; then echo "Uso: make revision msg=\"mensaje\""; exit 1; fi; \
	alembic revision -m "$(msg)"
