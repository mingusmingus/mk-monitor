import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext.jsx'

/**
 * Hook personalizado para acceder al contexto de autenticación.
 *
 * Permite a los componentes acceder a la sesión del usuario, token, rol,
 * y funciones de login/logout.
 *
 * @returns {Object} Contexto de autenticación.
 */
export default function useAuth() {
  return useContext(AuthContext)
}
