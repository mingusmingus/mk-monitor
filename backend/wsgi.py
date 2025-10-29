"""
WSGI entrypoint para servidores como gunicorn/uwsgi.

Ejemplo:
gunicorn backend.app.wsgi:app --bind 0.0.0.0:8000
"""
from app import create_app

app = create_app()