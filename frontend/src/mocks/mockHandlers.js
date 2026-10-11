/**
 * @file mockHandlers.js
 * @description In-memory mock handlers simulating FastAPI backend responses.
 * Follows exact contracts defined in docs/decisions.md and prompt section 4.
 */

import {
  mockUser,
  mockDailyLogs,
  mockExerciseRecommendations,
  mockFoodRecommendations,
  mockCatalogExercises,
  mockCatalogFoods,
  mockAnalyticsMe,
  mockAnalyticsPopulation,
} from './fixtures'

// Mutable in-memory state for local testing
let currentUser = { ...mockUser }
let logsState = [...mockDailyLogs]
const ratingsState = []

const delay = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms))

export const mockHandlers = {
  // POST /auth/register
  register: async (payload) => {
    await delay()
    if (!payload.email || !payload.password) {
      throw { status: 400, message: 'Email and password are required' }
    }
    currentUser = {
      ...mockUser,
      id: `usr_${Date.now()}`,
      email: payload.email,
      profile: {
        age: 0,
        gender: 'other',
        height_cm: 0,
        weight_kg: 0,
        activity_level: 'moderate',
        diet_type: 'veg',
        injuries: [],
      },
      goal: { target_weight_kg: 0, target_date: '' },
    }
    return {
      access_token: 'mock_jwt_token_' + Date.now(),
      token_type: 'bearer',
      user_id: currentUser.id,
      user: currentUser,
    }
  },

  // POST /auth/login
  login: async (payload) => {
    await delay()
    if (!payload.email || !payload.password) {
      throw { status: 400, message: 'Invalid credentials' }
    }
    return {
      access_token: 'mock_jwt_token_valid',
      token_type: 'bearer',
      user_id: currentUser.id,
      user: currentUser,
    }
  },

  // GET /users/me
  getMe: async () => {
    await delay()
    return { ...currentUser }
  },

  // PUT /users/me
  updateMe: async (payload) => {
    await delay()
    currentUser = {
      ...currentUser,
      profile: { ...currentUser.profile, ...payload.profile },
      goal: { ...currentUser.goal, ...payload.goal },
    }
    return { ...currentUser }
  },

  // GET /logs?from=&to=
  getLogs: async (params = {}) => {
    await delay()
    let filtered = [...logsState]
    if (params.from) {
      filtered = filtered.filter((log) => log.date >= params.from)
    }
    if (params.to) {
      filtered = filtered.filter((log) => log.date <= params.to)
    }
    return filtered
  },

  // POST /logs (create or update today's log)
  saveLog: async (logPayload) => {
    await delay()
    const existingIndex = logsState.findIndex((l) => l.date === logPayload.date)

    // Calculate kcal_in and kcal_out as backend rollup simulation
    let kcalIn = 0
    if (Array.isArray(logPayload.meals)) {
      kcalIn = logPayload.meals.reduce((sum, meal) => sum + (meal.kcal || (meal.grams ? Math.round(meal.grams * 1.5) : 0)), 0)
    }

    let kcalOut = 1800 // base metabolic estimation
    if (Array.isArray(logPayload.workouts)) {
      const workoutBurn = logPayload.workouts.reduce(
        (sum, w) => sum + (w.kcal_burned || (w.duration_min ? Math.round(w.duration_min * 5.5) : 0)),
        0
      )
      kcalOut += workoutBurn
    }

    const savedRecord = {
      id: existingIndex >= 0 ? logsState[existingIndex].id : `log_${Date.now()}`,
      user_id: currentUser.id,
      ...logPayload,
      kcal_in: kcalIn,
      kcal_out: kcalOut,
    }

    if (existingIndex >= 0) {
      logsState[existingIndex] = savedRecord
    } else {
      logsState.push(savedRecord)
    }

    return savedRecord
  },

  // GET /recommend/exercises?date=
  getExerciseRecommendations: async (_date) => {
    await delay()
    return [...mockExerciseRecommendations]
  },

  // GET /recommend/foods?date=
  getFoodRecommendations: async (_date) => {
    await delay()
    // Filter recommendations by user's diet_type if veg
    if (currentUser?.profile?.diet_type === 'veg') {
      return mockFoodRecommendations.filter((f) => f.diet_type === 'veg')
    }
    return [...mockFoodRecommendations]
  },

  // POST /feedback
  submitFeedback: async (feedbackPayload) => {
    await delay()
    ratingsState.push({
      ...feedbackPayload,
      timestamp: new Date().toISOString(),
    })
    return { success: true, message: 'Rating recorded successfully' }
  },

  // GET /analytics/me
  getAnalyticsMe: async () => {
    await delay()
    return { ...mockAnalyticsMe }
  },

  // GET /analytics/population
  getAnalyticsPopulation: async () => {
    await delay()
    return { ...mockAnalyticsPopulation }
  },

  // Fallback catalog for exercise & food selection (Gap #4)
  getCatalog: async () => {
    await delay()
    return {
      exercises: mockCatalogExercises,
      foods: mockCatalogFoods,
    }
  },
}
