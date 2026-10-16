import React, { useState, useEffect } from 'react'
import { api } from '../api'
import { useAuth } from '../hooks/useAuth'
import { Alert } from '../components/Alert'

/**
 * Computes streak: counts consecutive days (up to today) that have a log entry.
 * Why: backend /analytics/me has no streak field; we derive it from the logs list.
 * @param {Array<{date: string}>} logs
 * @returns {number}
 */
function computeStreak(logs) {
  const dates = new Set(logs.map((l) => l.date))
  let streak = 0
  const today = new Date()
  for (let i = 0; i < 365; i++) {
    const d = new Date(today)
    d.setDate(d.getDate() - i)
    const key = d.toISOString().slice(0, 10)
    if (dates.has(key)) streak++
    else break
  }
  return streak
}


/**
 * ProgressPage:
 * Shows user analytics and time-series progress:
 * - Weight trend vs target weight goal
 * - Calories consumed (in) vs calories burned (out)
 * - Sleep hours and hydration consistency
 */
export function ProgressPage({ onNavigate }) {
  const { user } = useAuth()
  const [analytics, setAnalytics] = useState(null)
  const [streak, setStreak] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadAnalytics = async () => {
    try {
      setLoading(true)
      const [data, logs] = await Promise.all([
        api.analytics.getMe(),
        api.logs.getLogs(),
      ])
      setAnalytics(data)
      setStreak(data.current_streak_days ?? data.streak ?? computeStreak(logs))
    } catch (err) {
      setError(err.message || 'Failed to fetch personal progress analytics.')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    let ignore = false
    async function fetchData() {
      try {
        const [data, logs] = await Promise.all([
          api.analytics.getMe(),
          api.logs.getLogs(),
        ])
        if (!ignore) {
          setAnalytics(data)
          setStreak(data.current_streak_days ?? data.streak ?? computeStreak(logs))
        }
      } catch (err) {
        if (!ignore) {
          setError(err.message || 'Failed to fetch personal progress analytics.')
        }
      } finally {
        if (!ignore) setLoading(false)
      }
    }
    fetchData()
    return () => {
      ignore = true
    }
  }, [])

  if (loading && !analytics) {
    return (
      <div className="container" style={{ textAlign: 'center', padding: '4rem 1rem' }}>
        <p>Loading analytics data...</p>
      </div>
    )
  }

  const targetWeight = user?.goal?.target_weight_kg || 69.0
  const weightTrend = analytics?.weight_history || []
  const weightChange =
    weightTrend.length >= 2
      ? +(weightTrend[weightTrend.length - 1].weight_kg - weightTrend[0].weight_kg).toFixed(1)
      : 0

  // Compute chart scales
  const weights = weightTrend.map((w) => w.weight_kg)
  const minWeight = Math.min(...weights, targetWeight) - 1
  const maxWeight = Math.max(...weights, targetWeight) + 1
  const weightRange = maxWeight - minWeight || 1

  const activeStreak = analytics?.current_streak_days ?? streak
  const bestStreak = analytics?.best_streak_days ?? activeStreak
  const goalProgress = analytics?.goal_progress_pct ?? 0.0

  return (
    <div className="container">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <h1 style={{ marginBottom: '0.25rem' }}>Personal Progress &amp; Analytics</h1>
          <p>Track your biometric trajectory against your target fitness milestones.</p>
        </div>
        <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
          {onNavigate && (
            <button
              type="button"
              className="btn-secondary"
              onClick={() => onNavigate('daily-log')}
              style={{ padding: '0.45rem 0.85rem', fontSize: '0.85rem' }}
            >
              + Log Today
            </button>
          )}
          <button
            type="button"
            className="btn-secondary"
            onClick={loadAnalytics}
            disabled={loading}
            style={{ padding: '0.45rem 0.85rem', fontSize: '0.85rem' }}
          >
            🔄 {loading ? 'Refreshing...' : 'Refresh'}
          </button>
        </div>
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
            🔥 {activeStreak}d {bestStreak > activeStreak && <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>(Best: {bestStreak}d)</span>}
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Workouts Logged</div>
          <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>
            💪 {analytics?.total_workouts_completed ?? 0}
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Weight Delta</div>
          <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
            📉 {weightChange > 0 ? `+${weightChange}` : weightChange} kg
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Goal Progress</div>
          <div className="metric-value" style={{ color: 'var(--accent-secondary)' }}>
            🎯 {goalProgress}%
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
                const x = weightTrend.length > 1 ? (idx / (weightTrend.length - 1)) * 480 + 10 : 250
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

        {/* Chart 2: Daily Calories In vs Out */}
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ fontSize: '1.15rem' }}>Daily Calories (In vs Out)</h2>
            <div style={{ display: 'flex', gap: '0.75rem', fontSize: '0.8rem' }}>
              <span style={{ color: 'var(--accent-secondary)' }}>■ In (Meals)</span>
              <span style={{ color: 'var(--accent-primary)' }}>■ Out (Burned)</span>
            </div>
          </div>

          <div style={{ height: '220px', display: 'flex', alignItems: 'flex-end', gap: '0.75rem', justifyContent: 'center', overflowX: 'auto', paddingBottom: '0.5rem' }}>
            {(() => {
              const dailyCalories = analytics?.calories_in_vs_out || []
              if (dailyCalories.length === 0) {
                const maxKcal = Math.max(analytics?.total_kcal_in ?? 0, analytics?.total_kcal_out ?? 0, 1)
                const inH = Math.min(((analytics?.total_kcal_in ?? 0) / maxKcal) * 160, 160)
                const outH = Math.min(((analytics?.total_kcal_out ?? 0) / maxKcal) * 160, 160)
                return (
                  <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1.5rem' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
                      <div
                        title={`Total In: ${analytics?.total_kcal_in ?? 0}`}
                        style={{ width: '40px', height: `${inH}px`, background: 'linear-gradient(180deg, var(--accent-secondary), #4338ca)', borderRadius: '4px 4px 0 0' }}
                      />
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{analytics?.total_kcal_in ?? 0} in</span>
                    </div>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
                      <div
                        title={`Total Out: ${analytics?.total_kcal_out ?? 0}`}
                        style={{ width: '40px', height: `${outH}px`, background: 'linear-gradient(180deg, var(--accent-primary), #047857)', borderRadius: '4px 4px 0 0' }}
                      />
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>{analytics?.total_kcal_out ?? 0} out</span>
                    </div>
                  </div>
                )
              }
              const displayList = dailyCalories.slice(-7)
              const maxKcal = Math.max(
                ...displayList.flatMap((d) => [d.kcal_in, d.kcal_out]),
                1
              )
              return displayList.map((d) => {
                const inH = Math.max(Math.min((d.kcal_in / maxKcal) * 150, 150), 4)
                const outH = Math.max(Math.min((d.kcal_out / maxKcal) * 150, 150), 4)
                return (
                  <div key={d.date} style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '0.35rem' }}>
                    <div style={{ display: 'flex', alignItems: 'flex-end', gap: '4px' }}>
                      <div
                        title={`${d.date} - In: ${d.kcal_in} kcal`}
                        style={{
                          width: '18px',
                          height: `${inH}px`,
                          background: 'linear-gradient(180deg, var(--accent-secondary), #4338ca)',
                          borderRadius: '3px 3px 0 0',
                        }}
                      />
                      <div
                        title={`${d.date} - Out: ${d.kcal_out} kcal`}
                        style={{
                          width: '18px',
                          height: `${outH}px`,
                          background: 'linear-gradient(180deg, var(--accent-primary), #047857)',
                          borderRadius: '3px 3px 0 0',
                        }}
                      />
                    </div>
                    <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{d.date.slice(5)}</span>
                  </div>
                )
              })
            })()}
          </div>
          <p style={{ fontSize: '0.75rem', color: 'var(--text-muted)', textAlign: 'center', marginTop: '0.5rem' }}>
            Daily balance (last 7 days) | Total In: {analytics?.total_kcal_in ?? 0} kcal | Total Out: {analytics?.total_kcal_out ?? 0} kcal
          </p>
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

      {/* Goal-Date Forecast */}
      {analytics?.forecast && (
        <div
          className="card"
          style={{
            marginTop: '1.5rem',
            background: analytics.forecast.on_track
              ? 'linear-gradient(135deg, rgba(16, 185, 129, 0.1), rgba(17, 24, 39, 0.8))'
              : 'linear-gradient(135deg, rgba(245, 158, 11, 0.1), rgba(17, 24, 39, 0.8))',
            border: analytics.forecast.on_track
              ? '1px solid rgba(16, 185, 129, 0.3)'
              : '1px solid rgba(245, 158, 11, 0.3)',
          }}
        >
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '0.75rem', marginBottom: '0.5rem' }}>
            <h2 style={{ fontSize: '1.15rem', display: 'flex', alignItems: 'center', gap: '0.5rem', margin: 0 }}>
              <span>🔮</span> Goal-Date Forecast
            </h2>
            <span
              style={{
                fontSize: '0.8rem',
                fontWeight: 700,
                padding: '0.2rem 0.6rem',
                borderRadius: 'var(--radius-sm)',
                background: analytics.forecast.on_track ? 'rgba(16, 185, 129, 0.2)' : 'rgba(245, 158, 11, 0.2)',
                color: analytics.forecast.on_track ? 'var(--status-success)' : 'var(--status-warning)',
              }}
            >
              {analytics.forecast.on_track ? '✓ On Track' : '⚡ Adjustment Suggested'}
            </span>
          </div>
          <p style={{ fontSize: '0.9rem', color: 'var(--text-secondary)', marginBottom: '0.75rem' }}>
            {analytics.forecast.message}
          </p>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(140px, 1fr))', gap: '0.75rem', fontSize: '0.85rem' }}>
            {analytics.forecast.projected_goal_date && (
              <div className="metric-box" style={{ padding: '0.5rem' }}>
                <div className="metric-label">Projected Date</div>
                <strong style={{ color: 'var(--text-primary)' }}>{analytics.forecast.projected_goal_date}</strong>
              </div>
            )}
            {analytics.forecast.days_to_goal !== undefined && analytics.forecast.days_to_goal !== null && (
              <div className="metric-box" style={{ padding: '0.5rem' }}>
                <div className="metric-label">Days Remaining</div>
                <strong style={{ color: 'var(--accent-primary)' }}>{analytics.forecast.days_to_goal} days</strong>
              </div>
            )}
            {analytics.forecast.weekly_rate_kg !== undefined && analytics.forecast.weekly_rate_kg !== null && (
              <div className="metric-box" style={{ padding: '0.5rem' }}>
                <div className="metric-label">Weekly Velocity</div>
                <strong style={{ color: 'var(--accent-cyan)' }}>{analytics.forecast.weekly_rate_kg} kg/wk</strong>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Anomaly Warnings */}
      {analytics?.anomalies && analytics.anomalies.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem', border: '1px solid rgba(239, 68, 68, 0.3)' }}>
          <h2 style={{ fontSize: '1.15rem', color: '#f87171', marginBottom: '0.75rem', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <span>⚠️</span> Biometric &amp; Caloric Anomaly Warnings
          </h2>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {analytics.anomalies.map((ano, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '0.6rem 0.85rem',
                  borderRadius: 'var(--radius-sm)',
                  background: 'rgba(239, 68, 68, 0.08)',
                  borderLeft: '3px solid #ef4444',
                  fontSize: '0.85rem',
                  flexWrap: 'wrap',
                  gap: '0.5rem',
                }}
              >
                <div>
                  <strong style={{ color: 'var(--text-primary)' }}>[{ano.type || 'Alert'}] </strong>
                  <span style={{ color: 'var(--text-secondary)' }}>{ano.message}</span>
                </div>
                {ano.date && (
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>{ano.date}</span>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>

  )
}
