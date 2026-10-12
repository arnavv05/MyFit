import { describe, it, expect, beforeEach } from 'vitest'
import { api, authStorage } from '../api'

describe('API Client in Mock Mode', () => {
  beforeEach(() => {
    authStorage.clear()
  })

  it('retrieves user profile via getMe', async () => {
    const user = await api.users.getMe()
    expect(user).toBeDefined()
    expect(user.email).toBe('student@myfitness.edu')
    expect(user.profile.activity_level).toBe('moderately_active')
  })

  it('updates profile via updateMe', async () => {
    const updated = await api.users.updateMe({
      profile: { weight_kg: 71.5 },
      goal: { target_weight_kg: 68.0 },
    })
    expect(updated.profile.weight_kg).toBe(71.5)
    expect(updated.goal.target_weight_kg).toBe(68.0)
  })

  it('saves daily log and calculates rolled up calories in and out', async () => {
    const log = await api.logs.saveLog({
      date: '2026-10-12',
      weight_kg: 73.2,
      sleep_hours: 7.5,
      water_ml: 2500,
      // frontend pre-computes these (item 5)
      workouts: [{ exercise_id: 'ex_1', duration_min: 30, kcal_burned: 140 }],
      meals: [{ food_id: 'fd_1', grams: 200, kcal: 260 }],
    })
    expect(log.date).toBe('2026-10-12')
    expect(log.kcal_in).toBe(260)
    expect(log.kcal_out).toBeGreaterThanOrEqual(0)
  })

  it('fetches exercise and food recommendations', async () => {
    const exercises = await api.recommend.getExercises('2026-10-12')
    const foods = await api.recommend.getFoods('2026-10-12')

    expect(Array.isArray(exercises)).toBe(true)
    expect(exercises.length).toBeGreaterThan(0)
    expect(exercises[0]).toHaveProperty('reason')

    expect(Array.isArray(foods)).toBe(true)
    expect(foods.length).toBeGreaterThan(0)
    expect(foods[0]).toHaveProperty('diet_type')
  })

  it('authStorage saves, retrieves, and clears tokens', () => {
    authStorage.setToken('test_jwt_123')
    expect(authStorage.getToken()).toBe('test_jwt_123')
    authStorage.clear()
    expect(authStorage.getToken()).toBeNull()
  })
})
