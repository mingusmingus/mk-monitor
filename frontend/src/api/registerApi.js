import client from './client'

/**
 * Registra un nuevo tenant + usuario admin.
 *
 * POST /auth/register → app.routes.auth_routes.register
 *
 * @param {Object} payload
 * @param {string} payload.email       Email del usuario administrador.
 * @param {string} payload.password    Contraseña (mín. 8 caracteres).
 * @param {string} [payload.full_name] Nombre completo opcional.
 * @returns {Promise<import('axios').AxiosResponse>} Respuesta Axios.
 * @throws Re-lanza el error de Axios, incluyendo `error.response` (status, data)
 *         para que SignupPage pueda mapear mensajes de error.
 */
export async function register(payload) {
  try {
    const res = await client.post('/auth/register', payload)
    return res
  } catch (error) {
    if (error.response) {
      throw error
    }
    throw error
  }
}