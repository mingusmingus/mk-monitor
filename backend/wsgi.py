"""
WSGI entrypoint para servidores como gunicorn/uwsgi.

Ejemplo:
gunicorn backend.app.wsgi:app --bind 0.0.0.0:8000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Para desarrollo local
    app.run(host="0.0.0.0", port=5000, debug=True)