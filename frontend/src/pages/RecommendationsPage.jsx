import React, { useState, useEffect } from 'react'
import { api } from '../api'
import { Badge } from '../components/Badge'
import { Alert } from '../components/Alert'
import { EmptyState } from '../components/EmptyState'

/**
 * RecommendationsPage:
 * Displays ML-recommended exercises and matching recovery meals.
 * Includes "Why recommended" explainability cards, veg/nonveg badges,
 * and 1-5 rating buttons submitting to POST /feedback.
 */
export function RecommendationsPage() {
  const [todayIso] = useState(() => new Date().toISOString().split('T')[0])
  const [exercises, setExercises] = useState([])
  const [foods, setFoods] = useState([])
  const [loading, setLoading] = useState(true)
  const [feedbackStatus, setFeedbackStatus] = useState({})
  const [alertMsg, setAlertMsg] = useState({ type: '', text: '' })

  useEffect(() => {
    async function fetchRecs() {
      setLoading(true)
      try {
        const [exList, foodList] = await Promise.all([
          api.recommend.getExercises(todayIso),
          api.recommend.getFoods(todayIso),
        ])
        setExercises(exList || [])
        setFoods(foodList || [])
      } catch (err) {
        setAlertMsg({ type: 'error', text: err.message || 'Could not load recommendations.' })
      } finally {
        setLoading(false)
      }
    }
    fetchRecs()
  }, [todayIso])

  const handleRate = async (itemType, itemId, rating) => {
    try {
      await api.feedback.submit({
        item_type: itemType,
        item_id: itemId,
        rating,
      })
      setFeedbackStatus((prev) => ({
        ...prev,
        [`${itemType}_${itemId}`]: rating,
      }))
      setAlertMsg({
        type: 'success',
        text: `Feedback recorded (${rating}★)! This refines collaborative filtering predictions.`,
      })
    } catch (err) {
      setAlertMsg({ type: 'error', text: err.message || 'Failed to submit feedback.' })
    }
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>Today's Personalized Plan</h1>
        <p>
          Generated using Collaborative Filtering &amp; K-Means clustering based on similar user profiles.
        </p>
      </div>

      <Alert
        type={alertMsg.type}
        message={alertMsg.text}
        onClose={() => setAlertMsg({ type: '', text: '' })}
      />

      {/* Cold start incentive banner */}
      <div
        style={{
          background: 'linear-gradient(135deg, rgba(99, 102, 241, 0.12), rgba(16, 185, 129, 0.08))',
          border: '1px solid var(--border-subtle)',
          borderRadius: 'var(--radius-md)',
          padding: '0.85rem 1.25rem',
          marginBottom: '2rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
        }}
      >
        <span style={{ fontSize: '1.5rem' }} aria-hidden="true">💡</span>
        <div>
          <strong style={{ color: 'var(--text-primary)' }}>Rate 5 picks to calibrate:</strong>
          <span style={{ color: 'var(--text-secondary)', marginLeft: '0.5rem', fontSize: '0.9rem' }}>
            Every 1-5 rating feeds the matrix factorization model to refine future recommendations.
          </span>
        </div>
      </div>

      {/* Section 1: Recommended Exercises */}
      <div style={{ marginBottom: '2.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent-primary)' }}>
            🏃 Recommended Workouts
          </h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            (Calorie burn estimated via MET formula)
          </span>
        </div>

        {exercises.length === 0 && !loading ? (
          <EmptyState
            icon="🏃"
            title="No workout recommendations found"
            description="Complete your biometric profile to generate exercises matched to your cluster."
          />
        ) : (
          <div className="grid-3">
            {exercises.map((ex) => {
              const currentRating = feedbackStatus[`exercise_${ex.exercise_id}`]
              return (
                <div
                  key={ex.exercise_id}
                  className="card"
                  style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
                >
                  <div>
                    <h3 style={{ fontSize: '1.1rem', marginBottom: '0.5rem' }}>{ex.name}</h3>

                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem' }}>
                      <div className="metric-box" style={{ flex: 1, padding: '0.5rem' }}>
                        <div className="metric-label">Duration</div>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                          {ex.duration_min} min
                        </div>
                      </div>
                      <div className="metric-box" style={{ flex: 1, padding: '0.5rem' }}>
                        <div className="metric-label">Est. Burn</div>
                        <div style={{ fontWeight: 700, color: 'var(--accent-primary)' }}>
                          ~{ex.est_kcal} kcal
                        </div>
                      </div>
                    </div>

                    {/* Visible "Why Recommended" line from reason field */}
                    <div
                      style={{
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderLeft: '3px solid var(--accent-primary)',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                        fontSize: '0.85rem',
                        color: 'var(--text-secondary)',
                        marginBottom: '1rem',
                      }}
                    >
                      <strong style={{ color: 'var(--text-primary)' }}>Why recommended: </strong>
                      {ex.reason}
                    </div>
                  </div>

                  {/* Rating Buttons */}
                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      Rate this recommendation:
                    </div>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          className="btn-outline"
                          onClick={() => handleRate('exercise', ex.exercise_id, star)}
                          style={{
                            padding: '0.2rem 0.4rem',
                            fontSize: '0.8rem',
                            borderColor: currentRating >= star ? 'var(--status-warning)' : undefined,
                            background: currentRating >= star ? 'rgba(245, 158, 11, 0.2)' : undefined,
                          }}
                          aria-label={`Rate ${star} out of 5 stars`}
                          aria-pressed={currentRating === star}
                        >
                          ⭐
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>

      {/* Section 2: Recommended Food Replenishment */}
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
          <h2 style={{ fontSize: '1.4rem', color: 'var(--accent-secondary)' }}>
            🥗 Recovery &amp; Replenishment Meals
          </h2>
          <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            (Personalized for your dietary preference)
          </span>
        </div>

        {foods.length === 0 && !loading ? (
          <EmptyState
            icon="🥗"
            title="No meal recommendations found"
            description="Log today's exercises to see replenishment recommendations matched to your calories burned."
          />
        ) : (
          <div className="grid-3">
            {foods.map((food) => {
              const currentRating = feedbackStatus[`food_${food.food_id}`]
              return (
                <div
                  key={food.food_id}
                  className="card"
                  style={{ display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}
                >
                  <div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
                      <h3 style={{ fontSize: '1.1rem' }}>{food.name}</h3>
                      <Badge type={food.diet_type} />
                    </div>

                    <div style={{ display: 'flex', gap: '1rem', marginBottom: '0.75rem' }}>
                      <div className="metric-box" style={{ flex: 1, padding: '0.5rem' }}>
                        <div className="metric-label">Portion</div>
                        <div style={{ fontWeight: 700, color: 'var(--text-primary)' }}>
                          {food.grams}g
                        </div>
                      </div>
                      <div className="metric-box" style={{ flex: 1, padding: '0.5rem' }}>
                        <div className="metric-label">Calories</div>
                        <div style={{ fontWeight: 700, color: 'var(--accent-secondary)' }}>
                          {food.kcal} kcal
                        </div>
                      </div>
                    </div>

                    {/* Macronutrient breakdown */}
                    {food.macros && (
                      <div
                        style={{
                          display: 'grid',
                          gridTemplateColumns: 'repeat(4, 1fr)',
                          gap: '0.25rem',
                          textAlign: 'center',
                          fontSize: '0.75rem',
                          marginBottom: '0.75rem',
                          background: 'var(--bg-surface-elevated)',
                          padding: '0.4rem',
                          borderRadius: 'var(--radius-sm)',
                        }}
                      >
                        <div>
                          <div style={{ color: 'var(--text-muted)' }}>Protein</div>
                          <strong>{food.macros.protein_g}g</strong>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)' }}>Carbs</div>
                          <strong>{food.macros.carbs_g}g</strong>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)' }}>Fat</div>
                          <strong>{food.macros.fat_g}g</strong>
                        </div>
                        <div>
                          <div style={{ color: 'var(--text-muted)' }}>Fiber</div>
                          <strong>{food.macros.fiber_g}g</strong>
                        </div>
                      </div>
                    )}

                    {/* Visible "Why Recommended" line from reason field */}
                    <div
                      style={{
                        background: 'rgba(255, 255, 255, 0.03)',
                        borderLeft: '3px solid var(--accent-secondary)',
                        padding: '0.5rem 0.75rem',
                        borderRadius: '0 var(--radius-sm) var(--radius-sm) 0',
                        fontSize: '0.85rem',
                        color: 'var(--text-secondary)',
                        marginBottom: '1rem',
                      }}
                    >
                      <strong style={{ color: 'var(--text-primary)' }}>Why recommended: </strong>
                      {food.reason}
                    </div>
                  </div>

                  {/* Rating Buttons */}
                  <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '0.75rem' }}>
                    <div style={{ fontSize: '0.75rem', color: 'var(--text-muted)', marginBottom: '0.25rem' }}>
                      Rate this recommendation:
                    </div>
                    <div style={{ display: 'flex', gap: '0.25rem' }}>
                      {[1, 2, 3, 4, 5].map((star) => (
                        <button
                          key={star}
                          type="button"
                          className="btn-outline"
                          onClick={() => handleRate('food', food.food_id, star)}
                          style={{
                            padding: '0.2rem 0.4rem',
                            fontSize: '0.8rem',
                            borderColor: currentRating >= star ? 'var(--status-warning)' : undefined,
                            background: currentRating >= star ? 'rgba(245, 158, 11, 0.2)' : undefined,
                          }}
                          aria-label={`Rate ${star} out of 5 stars`}
                          aria-pressed={currentRating === star}
                        >
                          ⭐
                        </button>
                      ))}
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}
      </div>
    </div>
  )
}
