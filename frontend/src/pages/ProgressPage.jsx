import React, { useState, useEffect } from 'react'
import { api } from '../api'
import { useAuth } from '../hooks/useAuth'
import { Alert } from '../components/Alert'

/**
 * ProgressPage:
 * Shows user analytics and time-series progress:
 * - Weight trend vs target weight goal
 * - Calories consumed (in) vs calories burned (out)
 * - Sleep hours and hydration consistency
 */
export function ProgressPage() {
  const { user } = useAuth()
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    async function loadAnalytics() {
      try {
        const data = await api.analytics.getMe()
        setAnalytics(data)
      } catch (err) {
        setError(err.message || 'Failed to fetch personal progress analytics.')
      } finally {
        setLoading(false)
      }
    }
    loadAnalytics()
  }, [])

  if (loading) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <p>Loading analytics data...</p>
      </div>
    )
  }

  const targetWeight = user?.goal?.target_weight_kg || 69.0
  const weightTrend = analytics?.weight_trend || []
  const caloriesTrend = analytics?.calories_trend || []

  // Compute chart scales
  const weights = weightTrend.map((w) => w.weight_kg)
  const minWeight = Math.min(...weights, targetWeight) - 1
  const maxWeight = Math.max(...weights, targetWeight) + 1
  const weightRange = maxWeight - minWeight || 1

  return (
    <div className="container">
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>Personal Progress &amp; Analytics</h1>
        <p>Track your biometric trajectory against your target fitness milestones.</p>
      </div>

      <Alert type="error" message={error} onClose={() => setError('')} />

      {/* Summary Metric Ribbon */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
          gap: '1rem',
          marginBottom: '2rem',
        }}
      >
        <div className="metric-box">
          <div className="metric-label">Active Streak</div>
          <div className="metric-value" style={{ color: 'var(--status-warning)' }}>
            🔥 {analytics?.streak_days || 0} days
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Workouts Logged</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>
            💪 {analytics?.total_workouts || 0}
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Weight Delta</div>
          <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
            📉 {analytics?.weight_change_kg > 0 ? `+${analytics.weight_change_kg}` : analytics?.weight_change_kg || 0} kg
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Daily Calorie Target</div>
          <div className="metric-value" style={{ color: 'var(--accent-secondary)' }}>
            🎯 {analytics?.calorie_target || 2150} kcal
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Chart 1: Weight Trend vs Goal */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.15rem' }}>Weight Trajectory vs Goal</h2>
            <span style={{ fontSize: '0.85rem', color: 'var(--accent-primary)', fontWeight: 600 }}>
              Goal: {targetWeight} kg
            </span>
          </div>

          <div style={{ height: '220px', display: 'flex', flexDirection: 'column', justifyContent: 'flex-end', position: 'relative' }}>
            {/* SVG Sparkline chart */}
            <svg viewBox="0 0 500 180" style={{ width: '100%', height: '100%', overflow: 'visible' }}>
              {/* Target goal horizontal dotted line */}
              {(() => {
                const targetY = 180 - ((targetWeight - minWeight) / weightRange) * 160
                return (
                  <g>
                    <line
                      x1="0"
                      y1={targetY}
                      x2="500"
                      y2={targetY}
                      stroke="var(--accent-primary)"
                      strokeWidth="2"
                      strokeDasharray="6,4"
                      opacity="0.8"
                    />
                    <text x="5" y={targetY - 6} fill="var(--accent-primary)" fontSize="11" fontWeight="bold">
                      Target Goal ({targetWeight} kg)
                    </text>
                  </g>
                )
              })()}

              {/* Weight trend polyline */}
              {weightTrend.length > 1 && (
                <polyline
                  fill="none"
                  stroke="var(--accent-cyan)"
                  strokeWidth="3.5"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  points={weightTrend
                    .map((item, idx) => {
                      const x = (idx / (weightTrend.length - 1)) * 480 + 10
                      const y = 180 - ((item.weight_kg - minWeight) / weightRange) * 160
                      return `${x},${y}`
                    })
                    .join(' ')}
                />
              )}

              {/* Data points */}
              {weightTrend.map((item, idx) => {
                const x = (idx / (weightTrend.length - 1)) * 480 + 10
                const y = 180 - ((item.weight_kg - minWeight) / weightRange) * 160
                return (
                  <g key={item.date}>
                    <circle cx={x} cy={y} r="5" fill="var(--bg-main)" stroke="var(--accent-cyan)" strokeWidth="3" />
                    <text x={x} y={y - 10} fill="var(--text-secondary)" fontSize="10" textAnchor="middle">
                      {item.weight_kg}
                    </text>
                  </g>
                )
              })}
            </svg>

            {/* X-axis labels */}
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.75rem', color: 'var(--text-muted)' }}>
              {weightTrend.map((item) => (
                <span key={item.date}>{item.date.slice(5)}</span>
              ))}
            </div>
          </div>
        </div>

        {/* Chart 2: Calories In vs Out */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.15rem' }}>Daily Calories In vs Out</h2>
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--accent-secondary)' }}>■ In (Meals)</span>
              <span style={{ color: 'var(--accent-primary)' }}>■ Out (Burned)</span>
            </div>
          </div>

          <div style={{ height: '220px', display: 'flex', alignItems: 'flex-end', gap: '0.8rem', paddingBottom: '0.5rem' }}>
            {caloriesTrend.map((item) => {
              const maxKcal = 2600
              const inHeight = Math.min((item.kcal_in / maxKcal) * 180, 180)
              const outHeight = Math.min((item.kcal_out / maxKcal) * 180, 180)

              return (
                <div
                  key={item.date}
                  style={{
                    flex: 1,
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.25rem',
                    height: '100%',
                    justifyContent: 'flex-end',
                  }}
                >
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px', width: '100%', justifyContent: 'center' }}>
                    {/* In bar */}
                    <div
                      title={`Kcal In: ${item.kcal_in}`}
                      style={{
                        width: '12px',
                        height: `${inHeight}px`,
                        background: 'linear-gradient(180deg, var(--accent-secondary), #4338ca)',
                        borderRadius: '3px 3px 0 0',
                      }}
                    />
                    {/* Out bar */}
                    <div
                      title={`Kcal Out: ${item.kcal_out}`}
                      style={{
                        width: '12px',
                        height: `${outHeight}px`,
                        background: 'linear-gradient(180deg, var(--accent-primary), #047857)',
                        borderRadius: '3px 3px 0 0',
                      }}
                    />
                  </div>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
                    {item.date.slice(5)}
                  </span>
                </div>
              )
            })}
          </div>
        </div>
      </div>

      {/* Recovery Averages Banner */}
      <div
        className="card"
        style={{
          marginTop: '1.5rem',
          display: 'flex',
          justifyContent: 'space-around',
          textAlign: 'center',
          flexWrap: 'wrap',
          gap: '1rem',
        }}
      >
        <div>
          <div className="metric-label">Avg Sleep Consistency</div>
          <div className="metric-value" style={{ color: '#a78bfa' }}>
            💤 {analytics?.avg_sleep_hours || 7.5} hrs/night
          </div>
        </div>
        <div style={{ borderLeft: '1px solid var(--border-subtle)' }} />
        <div>
          <div className="metric-label">Avg Hydration</div>
          <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
            💧 {analytics?.avg_water_ml || 2500} ml/day
          </div>
        </div>
      </div>
    </div>
  )
}
