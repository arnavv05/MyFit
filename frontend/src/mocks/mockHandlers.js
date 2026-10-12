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
import { ApiError } from '../api/client'

// Mutable in-memory state for local testing
let currentUser = { ...mockUser }
let logsState = [...mockDailyLogs]
const ratingsState = []

const delay = (ms = 120) => new Promise((resolve) => setTimeout(resolve, ms))

export const mockHandlers = {
  // POST /auth/register — returns user only (no token); caller must login separately
  register: async (payload) => {
    await delay()
    if (!payload.email || !payload.password) {
      throw new ApiError('Email and password are required', 400)
    }
    currentUser = {
      ...mockUser,
      id: `usr_${Date.now()}`,
      email: payload.email,
      profile: {
        age: payload.profile?.age ?? 0,
        gender: payload.profile?.gender ?? 'other',
        height_cm: payload.profile?.height_cm ?? 0,
        weight_kg: payload.profile?.weight_kg ?? 0,
        activity_level: payload.profile?.activity_level ?? 'moderately_active',
        diet_type: payload.profile?.diet_type ?? 'veg',
        injuries: payload.profile?.injuries ?? [],
      },
      goal: payload.goal ?? { target_weight_kg: 0, target_date: '' },
    }
    return { ...currentUser }
  },

  // POST /auth/login — returns {access_token, token_type} only (no user_id)
  login: async (payload) => {
    await delay()
    if (!payload.email || !payload.password) {
      throw new ApiError('Invalid credentials', 400)
    }
    return {
      access_token: 'mock_jwt_token_valid',
      token_type: 'bearer',
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

  // POST /logs — frontend must pre-compute kcal_burned and kcal before calling
  saveLog: async (logPayload) => {
    await delay()
    const existingIndex = logsState.findIndex((l) => l.date === logPayload.date)

    // Sum pre-computed values sent by the frontend (backend does the same)
    const kcalIn = Array.isArray(logPayload.meals)
      ? logPayload.meals.reduce((sum, meal) => sum + (meal.kcal || 0), 0)
      : 0

    const workoutBurn = Array.isArray(logPayload.workouts)
      ? logPayload.workouts.reduce((sum, w) => sum + (w.kcal_burned || 0), 0)
      : 0
    const kcalOut = workoutBurn // backend also just sums; TDEE is separate

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
