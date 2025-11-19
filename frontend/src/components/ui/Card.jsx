import React from 'react'
import Card from '@/components/ui/Card.jsx'

/**
 * Card
 * - Envoltorio con clase .card de theme.css
 * - Prop elevated para sombra fuerte
 */
export default function Card({ elevated = false, className = '', style, children, ...rest }) {
  return (
    <div
      className={['card', className].filter(Boolean).join(' ')}
      style={{ boxShadow: elevated ? 'var(--shadow-strong)' : undefined, ...style }}
      {...rest}
    >
      {children}
    </div>
  )
}

function Example() {
  return (
    <Card elevated>
      <h3>Título</h3>
      <p>Contenido dentro de la tarjeta.</p>
    </Card>
  )
}