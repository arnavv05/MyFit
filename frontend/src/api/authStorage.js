/**
 * @file authStorage.js
 * @description Centralized helper for persisting authentication tokens and user state.
 * Encapsulates localStorage to make swapping to cookies or in-memory storage effortless.
 */

const TOKEN_KEY = 'myfitness_jwt_token'
const USER_KEY = 'myfitness_user_data'

export const authStorage = {
  getToken: () => {
    try {
      return localStorage.getItem(TOKEN_KEY) || null
    } catch {
      return null
    }
  },

  setToken: (token) => {
    try {
      if (token) {
        localStorage.setItem(TOKEN_KEY, token)
      } else {
        localStorage.removeItem(TOKEN_KEY)
      }
    } catch (err) {
      console.error('Failed to save auth token:', err)
    }
  },

  getUser: () => {
    try {
      const data = localStorage.getItem(USER_KEY)
      return data ? JSON.parse(data) : null
    } catch {
      return null
    }
  },

  setUser: (user) => {
    try {
      if (user) {
        localStorage.setItem(USER_KEY, JSON.stringify(user))
      } else {
        localStorage.removeItem(USER_KEY)
      }
    } catch (err) {
      console.error('Failed to save user data:', err)
    }
  },

  clear: () => {
    try {
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_KEY)
    } catch (err) {
      console.error('Failed to clear auth storage:', err)
    }
  },
}
