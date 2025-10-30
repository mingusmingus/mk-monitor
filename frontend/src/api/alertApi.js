import client from './client'

// GET /api/alerts -> app.routes.alert_routes.list_alerts
export const getAlerts = (params = {}) => client.get('/alerts', { params })

// PATCH /api/alerts/:id/status -> app.routes.noc_routes.update_alert_status
export const updateAlertStatus = (alertId, body) => client.patch(`/alerts/${alertId}/status`, body)