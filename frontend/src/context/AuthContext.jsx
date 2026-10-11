import React, { useState, useEffect } from 'react'
import { api, authStorage } from '../api'
import { AuthContext } from './authContextInstance'

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => authStorage.getUser())
  const [token, setToken] = useState(() => authStorage.getToken())
  const [loading, setLoading] = useState(true)

  // Listen for unauthorized 401 events dispatched by our API client
  useEffect(() => {
    const handleUnauthorized = () => {
      setUser(null)
      setToken(null)
      authStorage.clear()
    }
    window.addEventListener('auth:unauthorized', handleUnauthorized)
    return () => window.removeEventListener('auth:unauthorized', handleUnauthorized)
  }, [])

  // On initial mount, fetch the latest user profile if a token exists
  useEffect(() => {
    async function loadUser() {
      if (token) {
        try {
          const profile = await api.users.getMe()
          setUser(profile)
          authStorage.setUser(profile)
        } catch (err) {
          console.error('Failed to restore user session:', err)
          authStorage.clear()
          setUser(null)
          setToken(null)
        }
      }
      setLoading(false)
    }
    loadUser()
  }, [token])

  const login = async (credentials) => {
    const res = await api.auth.login(credentials)
    authStorage.setToken(res.access_token)
    setToken(res.access_token)
    if (res.user) {
      setUser(res.user)
      authStorage.setUser(res.user)
    } else {
      const profile = await api.users.getMe()
      setUser(profile)
      authStorage.setUser(profile)
    }
    return res
  }

  const register = async (credentials) => {
    const res = await api.auth.register(credentials)
    authStorage.setToken(res.access_token)
    setToken(res.access_token)
    if (res.user) {
      setUser(res.user)
      authStorage.setUser(res.user)
    } else {
      const profile = await api.users.getMe()
      setUser(profile)
      authStorage.setUser(profile)
    }
    return res
  }

  const updateProfile = async (payload) => {
    const updated = await api.users.updateMe(payload)
    setUser(updated)
    authStorage.setUser(updated)
    return updated
  }

  const logout = () => {
    authStorage.clear()
    setUser(null)
    setToken(null)
  }

  const value = {
    user,
    token,
    loading,
    isAuthenticated: Boolean(token),
    login,
    register,
    updateProfile,
    logout,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
