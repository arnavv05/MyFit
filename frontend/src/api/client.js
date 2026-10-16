/**
 * @file client.js
 * @description Centralized HTTP request client with auth header injection,
 * 401 redirect handling, and seamless toggle between live FastAPI and local mocks.
 */

import { authStorage } from './authStorage'
import { mockHandlers } from '../mocks/mockHandlers'

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api/v1'
const USE_MOCK = import.meta.env.VITE_USE_MOCK === 'true'

/**
 * Custom error class for standardized API error handling.
 */
export class ApiError extends Error {
  constructor(message, status = 500, details = null) {
    super(message)
    this.name = 'ApiError'
    this.status = status
    this.details = details
  }
}

/**
 * Renames `_id` → `id` on a user object from the live backend.
 * Why: MongoDB uses `_id`; we normalise once here so all pages use `user.id`.
 * @param {object} raw
 * @returns {object}
 */
function normalizeUser(raw) {
  if (!raw) return raw
  const { _id, ...rest } = raw
  return { id: _id ?? rest.id, ...rest }
}

/**
 * Pre-computes kcal_burned per workout and kcal per meal before sending to the backend.
 * Why: backend requires these fields; it only sums them, it does not compute them.
 * @param {object} logPayload - raw log from the UI
 * @param {number} weightKg - user's current weight for MET formula
 * @param {Array}  catalog  - array of {id, met_value} from the exercise catalog
 * @returns {object} logPayload with kcal_burned and kcal filled in
 */
export function computeKcalForLog(logPayload, weightKg, catalog = []) {
  const metMap = Object.fromEntries(catalog.map((e) => [e.id, e.met_value]))
  const workouts = (logPayload.workouts || []).map((w) => ({
    ...w,
    // MET × weight_kg × hours = kcal; fall back to 5 kcal/min if MET unknown
    kcal_burned: w.kcal_burned ?? Math.round((metMap[w.exercise_id] ?? 5) * weightKg * (w.duration_min / 60)),
  }))
  const meals = (logPayload.meals || []).map((m) => ({
    ...m,
    // kcal_per_100g × grams / 100; fall back to 2 kcal/g if catalog unknown
    kcal: m.kcal ?? Math.round((m.kcal_per_100g ?? 200) * m.grams / 100),
  }))
  return { ...logPayload, workouts, meals }
}

/**
 * Handles HTTP requests with JWT authorization, error extraction, and 401 handling.
 * @param {string} endpoint - Relative path (e.g. '/users/me')
 * @param {RequestInit} [options] - Fetch options
 * @returns {Promise<any>}
 */
export async function request(endpoint, options = {}) {
  const token = authStorage.getToken()
  const headers = {
    'Content-Type': 'application/json',
    ...(token ? { Authorization: `Bearer ${token}` } : {}),
    ...(options.headers || {}),
  }

  const url = `${BASE_URL.replace(/\/$/, '')}${endpoint.startsWith('/') ? endpoint : `/${endpoint}`}`

  try {
    const res = await fetch(url, { ...options, headers })

    if (res.status === 401) {
      authStorage.clear()
      // Dispatch a custom event so UI can cleanly redirect to login
      window.dispatchEvent(new CustomEvent('auth:unauthorized'))
      throw new ApiError('Session expired. Please log in again.', 401)
    }

    // Try parsing JSON response
    let data = null
    const contentType = res.headers.get('content-type')
    if (contentType && contentType.includes('application/json')) {
      data = await res.json()
    } else {
      data = await res.text()
    }

    if (!res.ok) {
      // FastAPI errors return { detail: string | array }
      const message =
        typeof data?.detail === 'string'
          ? data.detail
          : Array.isArray(data?.detail)
            ? data.detail.map((e) => e.msg || e.message).join(', ')
            : data?.message || `Request failed with status ${res.status}`
      throw new ApiError(message, res.status, data)
    }

    return data
  } catch (err) {
    if (err instanceof ApiError) {
      throw err
    }
    const msg =
      err.message === 'Failed to fetch' || err.name === 'TypeError'
        ? `Cannot connect to backend at ${BASE_URL}. Ensure FastAPI is running on port 8000, or set VITE_USE_MOCK=true in frontend/.env`
        : err.message || 'Network error connecting to backend'
    throw new ApiError(msg, 500)
  }
}

/**
 * Unified API interface. When VITE_USE_MOCK=true, routes through mockHandlers;
 * otherwise dispatches HTTP requests via request().
 */
export const api = {
  auth: {
    // Items 1 & 2: register needs {email,password,profile,goal}, returns user only.
    // We immediately call login so the caller receives {access_token, token_type}.
    register: async (payload) => {
      if (USE_MOCK) {
        await mockHandlers.register(payload) // mutates currentUser inside handler
        // Auto-login: call mock login so caller gets a token
        const token = await mockHandlers.login({ email: payload.email, password: payload.password })
        authStorage.setToken(token.access_token)
        return token
      }
      // Live: register (returns user), then login to get token
      await request('/auth/register', { method: 'POST', body: JSON.stringify(payload) })
      return request('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email: payload.email, password: payload.password }),
      })
    },
    login: async (payload) => {
      if (USE_MOCK) return mockHandlers.login(payload)
      return request('/auth/login', {
        method: 'POST',
        body: JSON.stringify(payload),
      })
    },
  },

  users: {
    getMe: async () => {
      if (USE_MOCK) return mockHandlers.getMe()
      return normalizeUser(await request('/users/me', { method: 'GET' })) // Item 3: _id → id
    },
    updateMe: async (payload) => {
      if (USE_MOCK) return mockHandlers.updateMe(payload)
      return normalizeUser(await request('/users/me', { method: 'PUT', body: JSON.stringify(payload) }))
    },
  },

  logs: {
    getLogs: async (params = {}) => {
      if (USE_MOCK) return mockHandlers.getLogs(params)
      const query = new URLSearchParams()
      if (params.from) query.append('from', params.from)
      if (params.to) query.append('to', params.to)
      const qs = query.toString() ? `?${query.toString()}` : ''
      return request(`/logs${qs}`, { method: 'GET' })
    },
    saveLog: async (logPayload) => {
      if (USE_MOCK) return mockHandlers.saveLog(logPayload)
      return request('/logs', {
        method: 'POST',
        body: JSON.stringify(logPayload),
      })
    },
  },

  recommend: {
    getExercises: async (date) => {
      if (USE_MOCK) return mockHandlers.getExerciseRecommendations(date)
      const qs = date ? `?date=${encodeURIComponent(date)}` : ''
      return request(`/recommend/exercises${qs}`, { method: 'GET' })
    },
    getFoods: async (date) => {
      if (USE_MOCK) return mockHandlers.getFoodRecommendations(date)
      const qs = date ? `?date=${encodeURIComponent(date)}` : ''
      return request(`/recommend/foods${qs}`, { method: 'GET' })
    },
  },

  feedback: {
    submit: async (feedbackPayload) => {
      if (USE_MOCK) return mockHandlers.submitFeedback(feedbackPayload)
      return request('/feedback', {
        method: 'POST',
        body: JSON.stringify(feedbackPayload),
      })
    },
  },

  analytics: {
    getMe: async () => {
      if (USE_MOCK) return mockHandlers.getAnalyticsMe()
      return request('/analytics/me', { method: 'GET' })
    },
    getPopulation: async () => {
      if (USE_MOCK) return mockHandlers.getAnalyticsPopulation()
      return request('/analytics/population', { method: 'GET' })
    },
  },

  catalog: {
    // Adapter addressing Gap #4 until Member A adds search endpoints
    getCatalog: async () => {
      if (USE_MOCK) return mockHandlers.getCatalog()
      try {
        return await request('/catalog', { method: 'GET' })
      } catch {
        // Fallback to mock catalog if backend hasn't implemented it yet
        return mockHandlers.getCatalog()
      }
    },
  },
}
