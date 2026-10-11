import React, { useState } from 'react'
import { useAuth } from '../hooks/useAuth'
import { Alert } from '../components/Alert'

/**
 * RegisterPage:
 * User registration screen with password confirmation validation.
 *
 * @param {{ onNavigate: (page: string) => void }} props
 */
export function RegisterPage({ onNavigate }) {
  const { register } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')

    if (!email.trim() || !password) {
      setError('Please provide an email and password.')
      return
    }

    if (password.length < 6) {
      setError('Password must be at least 6 characters.')
      return
    }

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    try {
      setIsSubmitting(true)
      await register({ email, password })
      // New users must be guided to the onboarding form
      onNavigate('onboarding')
    } catch (err) {
      setError(err.message || 'Registration failed. Try again.')
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <div className="container" style={{ maxWidth: '440px', marginTop: '2rem' }}>
      <div className="card">
        <h1 style={{ fontSize: '1.75rem', marginBottom: '0.5rem', textAlign: 'center' }}>
          Join MyFitness
        </h1>
        <p style={{ textAlign: 'center', marginBottom: '1.5rem' }}>
          Personalized ML-driven fitness and nutrition recommendations
        </p>

        <Alert type="error" message={error} onClose={() => setError('')} />

        <form onSubmit={handleSubmit} noValidate>
          <div className="form-group">
            <label className="form-label" htmlFor="register-email">
              Email Address
            </label>
            <input
              id="register-email"
              type="email"
              className="form-input"
              placeholder="you@college.edu"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              autoComplete="email"
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="register-password">
              Create Password
            </label>
            <input
              id="register-password"
              type="password"
              className="form-input"
              placeholder="Minimum 6 characters"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              autoComplete="new-password"
              aria-required="true"
            />
          </div>

          <div className="form-group">
            <label className="form-label" htmlFor="register-confirm-password">
              Confirm Password
            </label>
            <input
              id="register-confirm-password"
              type="password"
              className="form-input"
              placeholder="Re-enter password"
              value={confirmPassword}
              onChange={(e) => setConfirmPassword(e.target.value)}
              required
              autoComplete="new-password"
              aria-required="true"
            />
          </div>

          <button
            type="submit"
            className="btn-primary"
            style={{ width: '100%', marginTop: '0.75rem' }}
            disabled={isSubmitting}
          >
            {isSubmitting ? 'Creating account...' : 'Create Account & Continue'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.9rem' }}>
          <span style={{ color: 'var(--text-muted)' }}>Already registered? </span>
          <button
            type="button"
            onClick={() => onNavigate('login')}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--accent-primary)',
              cursor: 'pointer',
              fontWeight: 600,
              padding: 0,
            }}
          >
            Sign in
          </button>
        </div>
      </div>
    </div>
  )
}
