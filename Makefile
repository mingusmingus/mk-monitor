AL_CONFIG=backend/alembic.ini

.PHONY: migrate revision

migrate:
	alembic -c $(AL_CONFIG) upgrade head

revision:
	@if [ -z "$(msg)" ]; then echo "Usage: make revision msg='mensaje'"; exit 1; fi
	alembic -c $(AL_CONFIG) revision --autogenerate -m "$(msg)"
