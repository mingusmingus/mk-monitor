import React from 'react'

// Modal de upsell cuando supera el límite de equipos del plan (placeholder).
export default function UpsellModal({ open, onClose }) {
  if (!open) return null
  return (
    <div className="modal">
      <div className="modal-content">
        <h3>Has alcanzado el límite de tu plan</h3>
        <p>Mejora tu plan para agregar más dispositivos.</p>
        <button onClick={onClose}>Cerrar</button>
      </div>
    </div>
  )
}