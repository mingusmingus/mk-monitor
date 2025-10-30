import React from 'react'
import { useNavigate } from 'react-router-dom'

// Modal reutilizable para upsell de plan.
export default function UpsellModal({ open, onClose }) {
  const navigate = useNavigate()
  if (!open) return null
  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal" onClick={(e) => e.stopPropagation()}>
        <h3>Has alcanzado el límite de equipos</h3>
        <p>
          Has alcanzado el límite de equipos de tu plan. Actualiza al plan INTERMAAT o PROMAAT
          para añadir más equipos.
        </p>
        <div className="row gap mt">
          <button className="btn btn-secondary" onClick={onClose}>Cerrar</button>
          <button
            className="btn btn-primary"
            onClick={() => {
              onClose?.()
              navigate('/subscription')
            }}
          >
            Quiero actualizar
          </button>
        </div>
      </div>
    </div>
  )
}