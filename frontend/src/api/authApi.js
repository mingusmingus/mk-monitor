// API de autenticación (placeholders sin implementación real).
import client from './client'

export const login = async (email, password) => {
  // return client.post('/auth/login', { email, password })
  return { data: { access_token: 'dummy', user: { email } } }
}

export const refreshToken = async () => {
  // return client.post('/auth/refresh')
  return { data: { access_token: 'dummy' } }
}