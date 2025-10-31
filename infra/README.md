# Infraestructura (docker-compose)

## Servicios disponibles

- postgres: base de datos principal
- pgadmin: interfaz web para administrar PostgreSQL

Copia variables:
- cp .env.example .env

Levantar Postgres y pgAdmin:
- docker compose up -d postgres pgadmin
- pgAdmin en http://localhost:5050 (credenciales desde .env)

Backend y frontend tendrán Dockerfile pronto:
- El `docker-compose.yml` ya define servicios `backend` y `frontend` con `build.context`, a la espera de Dockerfiles.
- Una vez agregados, podrás levantar todo con:
  - docker compose up -d

Producción:
- Rotar y gestionar de forma segura `ENCRYPTION_KEY` y `JWT_SECRET` (no usar valores por defecto).
- Usa volúmenes y backups para Postgres.
- Configura redes y firewalls adecuados.