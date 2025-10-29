// API de suscripciones (placeholders).
import client from './client'

export const getSubscription = async () => {
  // return client.get('/subscriptions/current')
  return { data: { plan: 'BASICMAAT', maxDevices: 5 } }
}