import { createContext } from 'react'

/**
 * AuthContext instance:
 * Kept in its own file so AuthContext.jsx only exports the AuthProvider component,
 * adhering to Vite / React Fast Refresh standards.
 */
export const AuthContext = createContext(null)
