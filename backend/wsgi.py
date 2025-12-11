"""
Punto de entrada WSGI para el servidor de aplicaciones.

Este módulo inicializa la aplicación Flask y permite su ejecución
tanto en entornos de desarrollo como de producción (vía servidores WSGI).

Ejemplo de ejecución con Gunicorn:
    gunicorn backend.wsgi:app --bind 0.0.0.0:8000
"""
from app import create_app

app = create_app()

if __name__ == "__main__":
    # Ejecución en modo desarrollo
    app.run(host="0.0.0.0", port=5000, debug=True)
