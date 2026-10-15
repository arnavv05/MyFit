import React, { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Alert } from '../components/Alert'
import { Badge } from '../components/Badge'

/**
 * OnboardingPage:
 * Profile setup and goal configuration form.
 * Saved via PUT /users/me.
 *
 * @param {{ onNavigate: (page: string) => void }} props
 */
export function OnboardingPage({ onNavigate }) {
  const { user, updateProfile } = useAuth()

  // Form states initialized with existing user data or defaults
  const [age, setAge] = useState(user?.profile?.age || 21)
  const [gender, setGender] = useState(user?.profile?.gender || 'male')
  const [heightCm, setHeightCm] = useState(user?.profile?.height_cm || 175)
  const [weightKg, setWeightKg] = useState(user?.profile?.weight_kg || 72)
  const [activityLevel, setActivityLevel] = useState(user?.profile?.activity_level || 'moderate')
  const [dietType, setDietType] = useState(user?.profile?.diet_type || 'veg')

  // Injuries state (multi-entry)
  const [injuries, setInjuries] = useState(user?.profile?.injuries || [])
  const [injuryInput, setInjuryInput] = useState('')

  // Goal state
  const [targetWeightKg, setTargetWeightKg] = useState(user?.goal?.target_weight_kg || 68)
  const [targetDate, setTargetDate] = useState(user?.goal?.target_date || '2026-12-31')

  const [statusMsg, setStatusMsg] = useState({ type: '', text: '' })
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Quick injury tags
  const commonInjuries = ['Knee strain', 'Lower back', 'Shoulder impingement', 'Wrist pain']

  const handleAddInjury = (item) => {
    const val = item.trim()
    if (val && !injuries.includes(val)) {
      setInjuries([...injuries, val])
      setInjuryInput('')
    }
  }

  const handleRemoveInjury = (val) => {
    setInjuries(injuries.filter((i) => i !== val))
  }

  // Live estimated BMR & TDEE preview (Mifflin-St Jeor formula)
  const bmr =
    gender === 'male'
      ? Math.round(10 * weightKg + 6.25 * heightCm - 5 * age + 5)
      : Math.round(10 * weightKg + 6.25 * heightCm - 5 * age - 161)

  const activityMultipliers = {
    sedentary: 1.2,
    light: 1.375,
    lightly_active: 1.375,
    moderate: 1.55,
    moderately_active: 1.55,
    active: 1.725,
    very_active: 1.725,
    extra_active: 1.9,
  }
  const tdee = Math.round(bmr * (activityMultipliers[activityLevel] || 1.55))

  const handleSubmit = async (e) => {
    e.preventDefault()
    setStatusMsg({ type: '', text: '' })

    if (age <= 0 || heightCm <= 0 || weightKg <= 0 || targetWeightKg <= 0) {
      setStatusMsg({ type: 'error', text: 'Please enter valid non-zero measurements.' })
      return
    }

    try {
      setIsSubmitting(true)
      const payload = {
        profile: {
          age: Number(age),
          gender,
          height_cm: Number(heightCm),
          weight_kg: Number(weightKg),
          activity_level: activityLevel,
          diet_type: dietType,
          injuries,
        },
        goal: {
          target_weight_kg: Number(targetWeightKg),
          target_date: targetDate,
        },
      }

      await updateProfile(payload)
      setStatusMsg({ type: 'success', text: 'Profile and fitness goals updated successfully!' })
      // Navigate to today's log after a brief confirmation
      setTimeout(() => {
        onNavigate('daily-log')
      }, 700)
    } catch (err) {
      setStatusMsg({ type: 'error', text: err.message || 'Failed to update profile.' })
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="container" style={{ maxWidth: '780px' }}>
      <div style={{ marginBottom: '1.5rem' }}>
        <h1 style={{ marginBottom: '0.25rem' }}>Personal Fitness Profile</h1>
        <p>Set your biometric data and target goals to calibrate your ML recommendations.</p>
      </div>

      <Alert
        type={statusMsg.type}
        message={statusMsg.text}
        onClose={() => setStatusMsg({ type: '', text: '' })}
      />

      <form onSubmit={handleSubmit} noValidate>
        {/* Section 1: Biometrics */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
            1. Biometrics & Activity
          </h2>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="profile-age">
                Age (years)
              </label>
              <input
                id="profile-age"
                type="number"
                min="14"
                max="100"
                className="form-input"
                value={age}
                onChange={(e) => setAge(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="profile-gender">
                Gender
              </label>
              <select
                id="profile-gender"
                className="form-select"
                value={gender}
                onChange={(e) => setGender(e.target.value)}
              >
                <option value="male">Male</option>
                <option value="female">Female</option>
                <option value="other">Other</option>
              </select>
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="profile-height">
                Height (cm)
              </label>
              <input
                id="profile-height"
                type="number"
                min="100"
                max="250"
                className="form-input"
                value={heightCm}
                onChange={(e) => setHeightCm(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="profile-weight">
                Current Weight (kg)
              </label>
              <input
                id="profile-weight"
                type="number"
                step="0.1"
                min="30"
                max="300"
                className="form-input"
                value={weightKg}
                onChange={(e) => setWeightKg(e.target.value)}
                required
              />
            </div>
          </div>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="profile-activity">
                Activity Level
              </label>
              <select
                id="profile-activity"
                className="form-select"
                value={activityLevel}
                onChange={(e) => setActivityLevel(e.target.value)}
              >
                <option value="sedentary">Sedentary (desk job, minimal exercise)</option>
                <option value="lightly_active">Light (exercise 1-3 days/week)</option>
                <option value="moderately_active">Moderate (exercise 3-5 days/week)</option>
                <option value="very_active">Very Active (exercise 6-7 days/week)</option>
                <option value="extra_active">Extra Active (heavy physical job/training)</option>
              </select>
            </div>

            <div className="form-group">
              <label className="form-label">Dietary Preference</label>
              <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.25rem' }}>
                <button
                  type="button"
                  className={dietType === 'veg' ? 'btn-primary' : 'btn-secondary'}
                  onClick={() => setDietType('veg')}
                  style={{ flex: 1 }}
                >
                  <Badge type="veg" />
                </button>
                <button
                  type="button"
                  className={dietType === 'nonveg' ? 'btn-primary' : 'btn-secondary'}
                  onClick={() => setDietType('nonveg')}
                  style={{ flex: 1 }}
                >
                  <Badge type="nonveg" />
                </button>
              </div>
            </div>
          </div>

          {/* Calorie baseline preview banner */}
          <div
            style={{
              marginTop: '1rem',
              padding: '1rem',
              background: 'var(--bg-surface-elevated)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border-subtle)',
              display: 'flex',
              justifyContent: 'space-around',
              textAlign: 'center',
            }}
          >
            <div>
              <div className="metric-label">Estimated BMR</div>
              <div className="metric-value" style={{ color: 'var(--accent-cyan)' }}>
                {bmr} <span style={{ fontSize: '0.8rem' }}>kcal</span>
              </div>
            </div>
            <div style={{ borderLeft: '1px solid var(--border-subtle)' }} />
            <div>
              <div className="metric-label">Maintenance TDEE</div>
              <div className="metric-value" style={{ color: 'var(--accent-primary)' }}>
                {tdee} <span style={{ fontSize: '0.8rem' }}>kcal/day</span>
              </div>
            </div>
          </div>
        </div>

        {/* Section 2: Injuries & Physical Limitations */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '0.5rem', color: 'var(--accent-primary)' }}>
            2. Injuries & Physical Limitations
          </h2>
          <p style={{ fontSize: '0.85rem', marginBottom: '1rem' }}>
            Exercises flagged with matching injuries will be filtered out by the collaborative recommender.
          </p>

          <div className="form-group">
            <label className="form-label" htmlFor="injury-input">
              Add Injury / Limitation
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <input
                id="injury-input"
                type="text"
                className="form-input"
                placeholder="e.g. Knee strain, Lower back ache..."
                value={injuryInput}
                onChange={(e) => setInjuryInput(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    handleAddInjury(injuryInput)
                  }
                }}
              />
              <button
                type="button"
                className="btn-secondary"
                onClick={() => handleAddInjury(injuryInput)}
              >
                + Add
              </button>
            </div>
          </div>

          {/* Quick pick suggestions */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1rem' }}>
            <span style={{ fontSize: '0.8rem', color: 'var(--text-muted)', alignSelf: 'center' }}>
              Quick suggestions:
            </span>
            {commonInjuries.map((item) => (
              <button
                key={item}
                type="button"
                className="btn-outline"
                style={{ padding: '0.2rem 0.5rem', fontSize: '0.75rem' }}
                onClick={() => handleAddInjury(item)}
              >
                + {item}
              </button>
            ))}
          </div>

          {/* Selected injury chips */}
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {injuries.length === 0 ? (
              <span style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
                No injuries recorded (recommender will consider full exercise catalog).
              </span>
            ) : (
              injuries.map((injury) => (
                <span
                  key={injury}
                  style={{
                    background: 'rgba(239, 68, 68, 0.15)',
                    border: '1px solid rgba(239, 68, 68, 0.3)',
                    color: '#fca5a5',
                    borderRadius: 'var(--radius-full)',
                    padding: '0.25rem 0.75rem',
                    fontSize: '0.85rem',
                    display: 'inline-flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                  }}
                >
                  ⚠️ {injury}
                  <button
                    type="button"
                    onClick={() => handleRemoveInjury(injury)}
                    aria-label={`Remove ${injury}`}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#fca5a5',
                      padding: 0,
                      cursor: 'pointer',
                      fontSize: '0.9rem',
                    }}
                  >
                    &times;
                  </button>
                </span>
              ))
            )}
          </div>
        </div>

        {/* Section 3: Goal Target */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ fontSize: '1.25rem', marginBottom: '1rem', color: 'var(--accent-primary)' }}>
            3. Fitness Goal & Target
          </h2>

          <div className="grid-2">
            <div className="form-group">
              <label className="form-label" htmlFor="goal-target-weight">
                Target Weight (kg)
              </label>
              <input
                id="goal-target-weight"
                type="number"
                step="0.1"
                min="30"
                max="300"
                className="form-input"
                value={targetWeightKg}
                onChange={(e) => setTargetWeightKg(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="goal-target-date">
                Target Date
              </label>
              <input
                id="goal-target-date"
                type="date"
                className="form-input"
                value={targetDate}
                onChange={(e) => setTargetDate(e.target.value)}
                required
              />
            </div>
          </div>
        </div>

        {/* Submit Actions */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
          <button
            type="button"
            className="btn-secondary"
            onClick={() => onNavigate('daily-log')}
          >
            Cancel
          </button>
          <button type="submit" className="btn-primary" disabled={isSubmitting}>
            {isSubmitting ? 'Saving Profile...' : 'Save & Calibrate Plan'}
          </button>
        </div>
      </form>
    </div>
  )
}
