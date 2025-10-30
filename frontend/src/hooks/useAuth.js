import { useContext } from 'react'
import { AuthContext } from '../context/AuthContext.jsx'

// Helper para acceder al AuthContext.
export default function useAuth() {
  return useContext(AuthContext)
}
