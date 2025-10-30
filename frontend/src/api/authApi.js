// API de autenticación (placeholders sin implementación real).
import client from './client'

// POST /api/auth/login -> app.routes.auth_routes.login
export const login = (email, password) => client.post('/auth/login', { email, password })