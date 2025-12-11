# Gestor de Base de Datos

Este directorio contiene herramientas robustas para la gestión de la base de datos, reemplazando scripts antiguos y frágiles.

## `db_manager.py`

Es la herramienta central para operaciones de base de datos. Funciona en Windows, Linux y Docker.

### Requisitos Previo
Asegúrate de tener instaladas las dependencias del backend (incluyendo `alembic` y `python-dotenv`) y de estar en el entorno virtual correcto.

### Comandos Disponibles

1.  **Verificar Conexión y Estado**
    ```bash
    python scripts/db_manager.py check
    ```
    Muestra la revisión actual de la base de datos. Si hay error de conexión o configuración, fallará con un mensaje claro.

2.  **Crear Migración (Make)**
    ```bash
    python scripts/db_manager.py make "Descripción del cambio"
    ```
    Genera un nuevo archivo de migración en `backend/migrations/versions/` detectando cambios en los modelos.
    *Ejemplo:* `python scripts/db_manager.py make "agregar_columna_full_name"`

3.  **Aplicar Cambios (Upgrade)**
    ```bash
    python scripts/db_manager.py upgrade
    ```
    Aplica todas las migraciones pendientes para actualizar la base de datos a la última versión (`head`).

## Solución de Problemas

*   **Error: No se encontró DATABASE_URL**: Verifica que tengas un archivo `.env` en la carpeta `backend/` o en la raíz del proyecto con la variable `DATABASE_URL` definida correctamente.
*   **ModuleNotFoundError**: Asegúrate de haber activado tu entorno virtual (`venv` o `conda`).
