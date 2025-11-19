    ## Backend Dockerfile (multi-stage)
## Builder: instala dependencias de Python
FROM python:3.12-slim AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/app

# Copiar e instalar dependencias primero (mejor caché)
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir gunicorn

# Copiar código fuente (opcional en builder, útil para validaciones durante el build)
COPY backend/app ./app
COPY backend/wsgi.py ./wsgi.py

## Runtime: imagen final mínima
FROM python:3.12-slim AS runtime

# Variables de entorno de ejecución
ENV APP_ENV=prod \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar paquetes instalados desde el builder (site-packages)
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages

# Copiar binarios de Python instalados (gunicorn, etc.)
COPY --from=builder /usr/local/bin /usr/local/bin

# Copiar la aplicación
COPY backend/app ./app
COPY backend/wsgi.py ./wsgi.py

EXPOSE 5000

# Comando por defecto
CMD ["gunicorn", "-b", "0.0.0.0:5000", "wsgi:app"]
