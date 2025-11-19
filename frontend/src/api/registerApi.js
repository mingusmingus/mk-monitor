import client from './client'

// POST /api/auth/register -> app.routes.auth_routes.register
export const register = (payload) => client.post('/auth/register', payload)