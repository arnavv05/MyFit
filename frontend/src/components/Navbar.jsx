import React from 'react'
import { useAuth } from '../hooks/useAuth'

/**
 * Navbar Component:
 * Accessible, mobile-responsive top navigation bar.
 *
 * @param {{ currentTab: string, onSelectTab: (tab: string) => void }} props
 */
export function Navbar({ currentTab, onSelectTab }) {
  const { user, isAuthenticated, logout } = useAuth()

  return (
    <header className="navbar">
      <div className="nav-brand">
        <span aria-hidden="true">⚡</span>
        <button
          type="button"
          onClick={() => onSelectTab(isAuthenticated ? 'daily-log' : 'login')}
          style={{
            background: 'none',
            border: 'none',
            color: 'inherit',
            font: 'inherit',
            cursor: 'pointer',
            padding: 0,
          }}
        >
          <span>MyFitness</span>
        </button>
      </div>

      <nav aria-label="Main Navigation">
        <div className="nav-links">
          {isAuthenticated ? (
            <>
              <button
                type="button"
                className={`nav-link ${currentTab === 'daily-log' ? 'active' : ''}`}
                onClick={() => onSelectTab('daily-log')}
                aria-current={currentTab === 'daily-log' ? 'page' : undefined}
              >
                📝 Daily Log
              </button>
              <button
                type="button"
                className={`nav-link ${currentTab === 'recommendations' ? 'active' : ''}`}
                onClick={() => onSelectTab('recommendations')}
                aria-current={currentTab === 'recommendations' ? 'page' : undefined}
              >
                🎯 Recommendations
              </button>
              <button
                type="button"
                className={`nav-link ${currentTab === 'progress' ? 'active' : ''}`}
                onClick={() => onSelectTab('progress')}
                aria-current={currentTab === 'progress' ? 'page' : undefined}
              >
                📊 Progress
              </button>
              <button
                type="button"
                className={`nav-link ${currentTab === 'onboarding' ? 'active' : ''}`}
                onClick={() => onSelectTab('onboarding')}
                aria-current={currentTab === 'onboarding' ? 'page' : undefined}
              >
                ⚙️ Profile & Goal
              </button>
            </>
          ) : (
            <>
              <button
                type="button"
                className={`nav-link ${currentTab === 'login' ? 'active' : ''}`}
                onClick={() => onSelectTab('login')}
              >
                Log In
              </button>
              <button
                type="button"
                className={`nav-link ${currentTab === 'register' ? 'active' : ''}`}
                onClick={() => onSelectTab('register')}
              >
                Register
              </button>
            </>
          )}
        </div>
      </nav>

      {isAuthenticated && (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span
            style={{
              fontSize: '0.85rem',
              color: 'var(--text-secondary)',
              maxWidth: '180px',
              overflow: 'hidden',
              textOverflow: 'ellipsis',
              whiteSpace: 'nowrap',
            }}
            title={user?.email}
          >
            {user?.email}
          </span>
          <button
            type="button"
            className="btn-outline"
            onClick={logout}
            style={{ padding: '0.4rem 0.75rem', fontSize: '0.8rem' }}
          >
            Log Out
          </button>
        </div>
      )}
    </header>
  )
}
