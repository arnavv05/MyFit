import { useContext } from 'react'
import { AuthContext } from '../context/authContextInstance'

/**
 * React Hook Concept:
 * Custom hooks let us bundle component logic into reusable functions so callers
 * don't have to repeatedly import both useContext and AuthContext.
 */
export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
