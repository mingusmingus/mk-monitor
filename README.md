# MK-Monitor Enterprise Grade

**Plataforma de Operaciones de Red (NetOps) Multi-Tenant Potenciada por IA**

![Status](https://img.shields.io/badge/Status-Stable-success)
![License](https://img.shields.io/badge/License-Proprietary-blue)
![Python](https://img.shields.io/badge/Backend-Python%203.11-yellow)
![React](https://img.shields.io/badge/Frontend-React%2018-blue)

MK-Monitor es una solución SaaS diseñada para proveedores de servicios de internet (ISP) y administradores de red que requieren visibilidad profunda, detección proactiva de amenazas y análisis forense automatizado de dispositivos Mikrotik.

---

## 🚀 Características Principales

*   **Inteligencia Artificial Forense:** Integración con modelos LLM (DeepSeek) para el análisis contextual de incidentes y generación de recomendaciones operativas.
*   **Arquitectura Multi-Tenant:** Aislamiento estricto de datos y recursos por cliente.
*   **Minería de Datos Profunda:** Extracción avanzada de telemetría (L1/L2/L3) utilizando `routeros_api`.
*   **Gestión de Ciclo de Vida de Alertas:** Flujo de trabajo completo para detección, triaje y resolución de incidentes (SLA).
*   **Seguridad Enterprise:** Cifrado de credenciales en reposo (Fernet), protección contra fuerza bruta y autenticación JWT.

## 🛠 Stack Tecnológico

### Backend
*   **Framework:** Python / Flask (Blueprints modularizados).
*   **Base de Datos:** PostgreSQL + SQLAlchemy (ORM) + Alembic (Migraciones).
*   **Seguridad:** Cryptography (Fernet) + JWT.
*   **IA:** Estrategia agnóstica de proveedor (DeepSeek implementado).

### Frontend
*   **Core:** React 18 + Vite.
*   **Estilos:** CSS Modules con Variables CSS (Diseño Minimalista "Apple-like").
*   **Estado:** Context API + Custom Hooks.

### Infraestructura
*   **Contenedores:** Docker & Docker Compose.
*   **Proxy Inverso:** Nginx.

## 📦 Instalación y Despliegue

### Requisitos Previos
*   Docker Desktop (v4.0+)
*   Git

### Paso a Paso

1.  **Clonar el repositorio:**
    ```bash
    git clone https://github.com/tu-organizacion/mk-monitor.git
    cd mk-monitor
    ```

2.  **Configurar Variables de Entorno:**
    Copie el archivo de ejemplo y ajuste los secretos (especialmente `DEEPSEEK_API_KEY` para habilitar IA).
    ```bash
    cp infra/.env.example infra/.env
    ```

3.  **Iniciar Servicios:**
    ```bash
    docker compose -f infra/docker-compose.yml up -d --build
    ```

4.  **Acceso:**
    *   **Frontend:** [http://localhost:8080](http://localhost:8080)
    *   **Backend Health:** [http://localhost:5000/api/health](http://localhost:5000/api/health)

## 🤝 Guía de Contribución

1.  **Estándares de Código:**
    *   **Python:** PEP8, Docstrings en Español (Google Style), Type Hints.
    *   **JavaScript:** ES6+, JSDoc en Español, Componentes Funcionales.
    *   **Commits:** Usar Conventional Commits (ej. `feat: agregar panel NOC`).

2.  **Flujo de Trabajo:**
    *   Crear rama `feature/nombre-funcionalidad` desde `main`.
    *   Realizar cambios y verificar localmente.
    *   Solicitar Pull Request (PR) para revisión.

3.  **Sanitización:**
    *   **Cero Emojis:** El código y logs deben ser profesionales y libres de emojis.
    *   **Logs Estructurados:** Usar `[INFO]`, `[WARNING]`, `[ERROR]`.

## 📄 Licencia

Este software es propietario y confidencial. Prohibida su distribución sin autorización expresa.

---
*Mantenido por el Equipo de Ingeniería de MK-Monitor.*
