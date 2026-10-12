import React from 'react'

/**
 * Accessible Alert Banner Component
 * @param {{ type?: 'error' | 'success' | 'info' | 'warning', message: string, onClose?: () => void }} props
 */
export function Alert({ type = 'info', message, onClose }) {
  if (!message) return null

  const borderColors = {
    error: 'var(--status-danger)',
    success: 'var(--status-success)',
    warning: 'var(--status-warning)',
    info: 'var(--status-info)',
  }

  const bgColors = {
    error: 'rgba(239, 68, 68, 0.12)',
    success: 'rgba(16, 185, 129, 0.12)',
    warning: 'rgba(245, 158, 11, 0.12)',
    info: 'rgba(59, 130, 246, 0.12)',
  }

  return (
    <div
      role={type === 'error' ? 'alert' : 'status'}
      aria-live={type === 'error' ? 'assertive' : 'polite'}
      aria-atomic="true"
      style={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0.75rem 1rem',
        borderRadius: 'var(--radius-md)',
        background: bgColors[type],
        border: `1px solid ${borderColors[type]}`,
        color: 'var(--text-primary)',
        marginBottom: '1rem',
        fontSize: '0.9rem',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
        <span aria-hidden="true">
          {type === 'error' && '⚠️'}
          {type === 'success' && '✅'}
          {type === 'warning' && '⚡'}
          {type === 'info' && 'ℹ️'}
        </span>
        <span>{message}</span>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Dismiss message"
          style={{
            background: 'transparent',
            border: 'none',
            color: 'var(--text-muted)',
            padding: '0 0.25rem',
            fontSize: '1rem',
          }}
        >
          &times;
        </button>
      )}
    </div>
  )
}
