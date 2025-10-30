// API de suscripciones (placeholders).
import client from './client'

export const getSubscription = async () => {
  // return client.get('/subscriptions/current')
  return { data: { plan: 'BASICMAAT', maxDevices: 5 } }
}

// Intentar el path estándar; fallback al path con doble prefijo del backend actual si 404.
export const getSubscriptionStatus = async () => {
  try {
    return await client.get('/subscription/status')
  } catch (err) {
    if (err?.response?.status === 404) {
      // Fallback por url_prefix doble en el blueprint actual.
      return await client.get('/subscriptions/subscription/status')
    }
    throw err
  }
}