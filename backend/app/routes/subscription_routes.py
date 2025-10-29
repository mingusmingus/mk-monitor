"""
Rutas de suscripción:

- Estado de plan del tenant, upsell y gestión de límites.
- Placeholder de Blueprint sin endpoints todavía.
"""
from flask import Blueprint

subscription_bp = Blueprint("subscriptions", __name__, url_prefix="/api/subscriptions")