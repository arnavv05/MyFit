import React, { useState, useEffect } from 'react'
import { api, computeKcalForLog } from '../api'
import { useAuth } from '../hooks/useAuth'
import { Alert } from '../components/Alert'
import { Badge } from '../components/Badge'

/**
 * DailyLogPage:
 * Logs dynamic biometric measurements, workouts, and meals.
 * Submitted through POST /logs. Rolled-up calories are displayed from backend response.
 */
export function DailyLogPage({ onNavigate }) {
  const { user } = useAuth()
  const [selectedDate, setSelectedDate] = useState(() => new Date().toISOString().split('T')[0])

  // Log state
  const [weightKg, setWeightKg] = useState('')
  const [sleepHours, setSleepHours] = useState('')
  const [waterMl, setWaterMl] = useState('')
  const [workouts, setWorkouts] = useState([])
  const [meals, setMeals] = useState([])

  // Server-computed rollups (read-only in UI)
  const [serverKcalIn, setServerKcalIn] = useState(null)
  const [serverKcalOut, setServerKcalOut] = useState(null)

  // Catalog items for selection (addressing Gap #4)
  const [catalog, setCatalog] = useState({ exercises: [], foods: [] })
  const [selectedExId, setSelectedExId] = useState('')
  const [exSearch, setExSearch] = useState('')
  const [exDuration, setExDuration] = useState(30)
  const [exRating, setExRating] = useState(5)

  const [selectedFoodId, setSelectedFoodId] = useState('')
  const [foodSearch, setFoodSearch] = useState('')
  const [foodGrams, setFoodGrams] = useState(200)

  const [isLoading, setIsLoading] = useState(true)
  const [isSaving, setIsSaving] = useState(false)
  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' })

  const filteredExercises = catalog.exercises.filter((ex) =>
    !exSearch ||
    ex.name.toLowerCase().includes(exSearch.toLowerCase()) ||
    (ex.category && ex.category.toLowerCase().includes(exSearch.toLowerCase()))
  )

  const filteredFoods = catalog.foods.filter((f) =>
    !foodSearch ||
    f.name.toLowerCase().includes(foodSearch.toLowerCase()) ||
    (f.cuisine && f.cuisine.toLowerCase().includes(foodSearch.toLowerCase()))
  )


  // Fetch catalog and current day's log
  useEffect(() => {
    async function loadData() {
      setIsLoading(true)
      try {
        const cat = await api.catalog.getCatalog()
        setCatalog(cat)
        if (cat.exercises.length > 0) setSelectedExId(cat.exercises[0].id)
        if (cat.foods.length > 0) setSelectedFoodId(cat.foods[0].id)

        // Load existing log for selected date
        const logs = await api.logs.getLogs({ from: selectedDate, to: selectedDate })
        const existing = logs.find((l) => l.date === selectedDate)

        if (existing) {
          setWeightKg(existing.weight_kg || '')
          setSleepHours(existing.sleep_hours || '')
          setWaterMl(existing.water_ml || '')
          setWorkouts(existing.workouts || [])
          setMeals(existing.meals || [])
          setServerKcalIn(existing.kcal_in ?? null)
          setServerKcalOut(existing.kcal_out ?? null)
        } else {
          // Fresh log for the date
          setWeightKg('')
          setSleepHours('')
          setWaterMl('')
          setWorkouts([])
          setMeals([])
          setServerKcalIn(null)
          setServerKcalOut(null)
        }
      } catch (err) {
        console.error('Failed to load log data:', err)
      } finally {
        setIsLoading(false)
      }
    }
    loadData()
  }, [selectedDate])

  const handleAddWorkout = () => {
    const exItem = catalog.exercises.find((e) => e.id === selectedExId) || filteredExercises[0]
    if (!exItem) return

    setWorkouts([
      ...workouts,
      {
        exercise_id: exItem.id,
        name: exItem.name,
        duration_min: Number(exDuration),
        rating: Number(exRating),
      },
    ])
  }

  const handleRemoveWorkout = (idx) => {
    setWorkouts(workouts.filter((_, i) => i !== idx))
  }

  const handleAddMeal = () => {
    const foodItem = catalog.foods.find((f) => f.id === selectedFoodId) || filteredFoods[0]
    if (!foodItem) return

    setMeals([
      ...meals,
      {
        food_id: foodItem.id,
        name: foodItem.name,
        diet_type: foodItem.diet_type,
        grams: Number(foodGrams),
      },
    ])
  }

  const handleRemoveMeal = (idx) => {
    setMeals(meals.filter((_, i) => i !== idx))
  }

  const handleSaveLog = async (e) => {
    e.preventDefault()
    setStatusMsg({ type: '', text: '' })

    try {
      setIsSaving(true)
      const rawPayload = {
        date: selectedDate,
        weight_kg: weightKg ? Number(weightKg) : undefined,
        sleep_hours: sleepHours ? Number(sleepHours) : undefined,
        water_ml: waterMl ? Number(waterMl) : undefined,
        workouts: workouts.map((w) => ({
          exercise_id: w.exercise_id,
          duration_min: Number(w.duration_min),
          kcal_burned: w.kcal_burned,
          rating: w.rating,
        })),
        meals: meals.map((m) => ({
          food_id: m.food_id,
          grams: Number(m.grams),
          kcal: m.kcal,
        })),
      }

      const activeWeight = weightKg ? Number(weightKg) : (user?.profile?.weight_kg || 70)
      const payload = computeKcalForLog(rawPayload, activeWeight, catalog.exercises)

      const saved = await api.logs.saveLog(payload)
      setServerKcalIn(saved.kcal_in ?? null)
      setServerKcalOut(saved.kcal_out ?? null)
      setStatusMsg({
        type: 'success',
        text: `Log for ${selectedDate} saved successfully! In: +${saved.kcal_in} kcal | Out: -${saved.kcal_out} kcal.`,
      })
      await fetchLogForDate(selectedDate)
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to save log.' })
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <div className="container" style={{ maxWidth: '900px' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.25rem' }}>Daily Fitness Log</h1>
          <p>Track your dynamic biometrics, workouts completed, and meals eaten.</p>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <label htmlFor="log-date" className="form-label" style={{ margin: 0 }}>
            Date:
          </label>
          <input
            id="log-date"
            type="date"
            className="form-input"
            style={{ width: 'auto' }}
            value={selectedDate}
            onChange={(e) => setSelectedDate(e.target.value)}
          />
        </div>
      </div>

      <Alert
        type={statusMsg.type}
        message={statusMsg.text}
        onClose={() => setStatusMsg({ type: '', text: '' })}
      />

      {isLoading && (
        <p
          role="status"
          aria-live="polite"
          style={{ textAlign: 'center', color: 'var(--text-muted)', padding: '1.5rem 0', fontSize: '0.9rem' }}
        >
          Loading your log data…
        </p>
      )}

      {/* Backend Rollup Stat Cards */}
      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08), rgba(17, 24, 39, 0.9))' }}>
          <div className="metric-label">Backend Rollup (Calories Consumed)</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)', marginTop: '0.25rem' }}>
            {serverKcalIn !== null ? `${serverKcalIn} kcal` : '--'}
          </div>
          <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
            Aggregated from logged meals via FastAPI backend.
          </p>
        </div>

        <div className="card" style={{ background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.08), rgba(17, 24, 39, 0.9))' }}>
          <div className="metric-label">Backend Rollup (Calories Burned)</div>
          <div className="metric-value" style={{ color: 'var(--accent-secondary)', marginTop: '0.25rem' }}>
            {serverKcalOut !== null ? `${serverKcalOut} kcal` : '--'}
          </div>
          <p style={{ fontSize: '0.8rem', marginTop: '0.25rem' }}>
            Aggregated from MET formulas and baseline metabolism.
          </p>
        </div>
      </div>

      <form onSubmit={handleSaveLog}>
        {/* Core Daily Biometrics */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
            Biometrics & Recovery
          </h2>
          <div className="grid-3">
            <div className="form-group">
              <label className="form-label" htmlFor="daily-weight">
                Morning Weight (kg)
              </label>
              <input
                id="daily-weight"
                type="number"
                step="0.1"
                className="form-input"
                placeholder="e.g. 73.2"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="daily-sleep">
                Sleep Duration (hours)
              </label>
              <input
                id="daily-sleep"
                type="number"
                step="0.5"
                min="0"
                max="24"
                className="form-input"
                placeholder="e.g. 7.5"
                value={sleepHours}
                onChange={(e) => setSleepHours(e.target.value)}
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="daily-water">
                Water Intake (ml)
              </label>
              <input
                id="daily-water"
                type="number"
                step="100"
                min="0"
                className="form-input"
                placeholder="e.g. 2500"
                value={waterMl}
                onChange={(e) => setWaterMl(e.target.value)}
              />
            </div>
          </div>
        </div>

        {/* Workouts Logged */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: 'var(--accent-primary)' }}>
            Workouts Performed
          </h2>
          <p style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
            Pick exercises from the catalog and rate your session effort (1-5 stars).
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
            <div style={{ flex: '2', minWidth: '220px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                <label className="form-label" htmlFor="workout-select" style={{ margin: 0 }}>
                  Exercise
                </label>
                <input
                  type="text"
                  placeholder="🔍 Search exercise..."
                  value={exSearch}
                  onChange={(e) => {
                    const q = e.target.value
                    setExSearch(q)
                    const m = catalog.exercises.filter((ex) =>
                      !q || ex.name.toLowerCase().includes(q.toLowerCase()) || (ex.category && ex.category.toLowerCase().includes(q.toLowerCase()))
                    )
                    if (m.length > 0 && !m.some((x) => x.id === selectedExId)) {
                      setSelectedExId(m[0].id)
                    }
                  }}
                  style={{
                    fontSize: '0.8rem',
                    padding: '0.2rem 0.5rem',
                    width: '150px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-main)',
                    color: 'var(--text-primary)',
                  }}
                  aria-label="Filter exercises"
                />
              </div>
              <select
                id="workout-select"
                className="form-select"
                value={selectedExId}
                onChange={(e) => setSelectedExId(e.target.value)}
              >
                {filteredExercises.length === 0 ? (
                  <option value="" disabled>No exercises match search</option>
                ) : (
                  filteredExercises.map((ex) => (
                    <option key={ex.id} value={ex.id}>
                      {ex.name} ({ex.category})
                    </option>
                  ))
                )}
              </select>
            </div>

            <div style={{ flex: '1', minWidth: '110px' }}>
              <label className="form-label" htmlFor="workout-duration">
                Duration (min)
              </label>
              <input
                id="workout-duration"
                type="number"
                min="5"
                max="300"
                className="form-input"
                value={exDuration}
                onChange={(e) => setExDuration(e.target.value)}
              />
            </div>

            <div style={{ flex: '1', minWidth: '110px' }}>
              <label className="form-label" htmlFor="workout-rating">
                Rating (1-5)
              </label>
              <select
                id="workout-rating"
                className="form-select"
                value={exRating}
                onChange={(e) => setExRating(e.target.value)}
              >
                <option value="5">⭐⭐⭐⭐⭐ (5)</option>
                <option value="4">⭐⭐⭐⭐ (4)</option>
                <option value="3">⭐⭐⭐ (3)</option>
                <option value="2">⭐⭐ (2)</option>
                <option value="1">⭐ (1)</option>
              </select>
            </div>

            <div style={{ alignSelf: 'flex-end' }}>
              <button type="button" className="btn-secondary" onClick={handleAddWorkout}>
                + Add Workout
              </button>
            </div>
          </div>

          {workouts.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              No workouts logged for this day yet.
            </p>
          ) : (
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {workouts.map((w, idx) => (
                <li
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    background: 'var(--bg-surface-elevated)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div>
                    <strong>{w.name || w.exercise_id}</strong> &mdash;{' '}
                    <span style={{ color: 'var(--text-secondary)' }}>
                      {w.duration_min} minutes
                    </span>{' '}
                    &bull;{' '}
                    <span style={{ color: 'var(--accent-primary)' }}>
                      {'⭐'.repeat(w.rating || 5)}
                    </span>
                  </div>
                  <button
                    type="button"
                    className="btn-outline"
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                    onClick={() => handleRemoveWorkout(idx)}
                    aria-label={`Remove ${w.name || w.exercise_id} from workouts`}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Meals Logged */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.2rem', marginBottom: '0.5rem', color: 'var(--accent-primary)' }}>
            Meals & Nutrition Eaten
          </h2>
          <p style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
            Track meal portions to calculate daily macronutrient and calorie replenishment.
          </p>

          <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap', marginBottom: '1rem' }}>
            <div style={{ flex: '2', minWidth: '220px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                <label className="form-label" htmlFor="meal-select" style={{ margin: 0 }}>
                  Food Item
                </label>
                <input
                  type="text"
                  placeholder="🔍 Search food..."
                  value={foodSearch}
                  onChange={(e) => {
                    const q = e.target.value
                    setFoodSearch(q)
                    const m = catalog.foods.filter((f) =>
                      !q || f.name.toLowerCase().includes(q.toLowerCase()) || (f.cuisine && f.cuisine.toLowerCase().includes(q.toLowerCase()))
                    )
                    if (m.length > 0 && !m.some((x) => x.id === selectedFoodId)) {
                      setSelectedFoodId(m[0].id)
                    }
                  }}
                  style={{
                    fontSize: '0.8rem',
                    padding: '0.2rem 0.5rem',
                    width: '150px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border-subtle)',
                    background: 'var(--bg-main)',
                    color: 'var(--text-primary)',
                  }}
                  aria-label="Filter foods"
                />
              </div>
              <select
                id="meal-select"
                className="form-select"
                value={selectedFoodId}
                onChange={(e) => setSelectedFoodId(e.target.value)}
              >
                {filteredFoods.length === 0 ? (
                  <option value="" disabled>No foods match search</option>
                ) : (
                  filteredFoods.map((f) => (
                    <option key={f.id} value={f.id}>
                      {f.name} ({f.diet_type})
                    </option>
                  ))
                )}
              </select>
            </div>

            <div style={{ flex: '1', minWidth: '120px' }}>
              <label className="form-label" htmlFor="meal-grams">
                Portion (grams)
              </label>
              <input
                id="meal-grams"
                type="number"
                min="10"
                max="2000"
                className="form-input"
                value={foodGrams}
                onChange={(e) => setFoodGrams(e.target.value)}
              />
            </div>

            <div style={{ alignSelf: 'flex-end' }}>
              <button type="button" className="btn-secondary" onClick={handleAddMeal}>
                + Add Meal
              </button>
            </div>
          </div>

          {meals.length === 0 ? (
            <p style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
              No meals logged for this day yet.
            </p>
          ) : (
            <ul style={{ listStyle: 'none', display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
              {meals.map((m, idx) => (
                <li
                  key={idx}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'space-between',
                    padding: '0.65rem 0.85rem',
                    background: 'var(--bg-surface-elevated)',
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border-subtle)',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <strong>{m.name || m.food_id}</strong> &mdash;{' '}
                    <span style={{ color: 'var(--text-secondary)' }}>{m.grams}g</span>
                    {m.diet_type && <Badge type={m.diet_type} />}
                  </div>
                  <button
                    type="button"
                    className="btn-outline"
                    style={{ padding: '0.2rem 0.5rem', fontSize: '0.8rem' }}
                    onClick={() => handleRemoveMeal(idx)}
                    aria-label={`Remove ${m.name || m.food_id} from meals`}
                  >
                    Remove
                  </button>
                </li>
              ))}
            </ul>
          )}
        </div>

        {/* Submit Actions */}
        <div style={{ display: 'flex', justifyContent: 'flex-end', alignItems: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          {statusMsg.type === 'success' && (
            <button
              type="button"
              className="btn-secondary"
              onClick={() => (onNavigate ? onNavigate('progress') : (window.location.hash = '#/progress'))}
            >
              View Updated Progress &rarr;
            </button>
          )}
          <button type="submit" className="btn-primary" disabled={isSaving || isLoading}>
            {isSaving ? 'Submitting to Backend...' : isLoading ? 'Loading...' : "Save Today's Log"}
          </button>
        </div>
      </form>
    </div>
  )
}
