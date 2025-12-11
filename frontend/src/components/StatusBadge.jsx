import React from 'react'
import PropTypes from 'prop-types'

/**
 * StatusBadge
 *
 * Componente visual tipo "etiqueta" para mostrar el estado de severidad de una alerta.
 * Utiliza clases CSS predefinidas para codificación por color.
 *
 * Props:
 * - estado: string ('Alerta Crítica', 'Alerta Severa', 'Alerta Menor', 'Aviso')
 */

const mapClass = (estado) => {
  switch (estado) {
    case 'Alerta Crítica':
      return 'badge badge-critical'
    case 'Alerta Severa':
      return 'badge badge-severe'
    case 'Alerta Menor':
      return 'badge badge-minor'
    default:
      return 'badge badge-info'
  }
}

export default function StatusBadge({ estado = 'Aviso' }) {
  return <span className={mapClass(estado)}>{estado}</span>
}

StatusBadge.propTypes = {
  estado: PropTypes.string
}
