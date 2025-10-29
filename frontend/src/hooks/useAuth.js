// Hook de ayuda para el contexto de autenticación (placeholder).
import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext.jsx'

export default function useAuth() {
  return useContext(AuthContext)
}
