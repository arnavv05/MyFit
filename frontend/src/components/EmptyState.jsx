import React from 'react'

/**
 * EmptyState Component:
 * Provides clear, friendly messaging for cold starts (e.g., no logs logged yet,
 * rating prompts to bootstrap recommendation models).
 *
 * @param {{ icon?: string, title: string, description: string, actionLabel?: string, onAction?: () => void }} props
 */
export function EmptyState({ icon = '📋', title, description, actionLabel, onAction }) {
  return (
    <div
      style={{
        textAlign: 'center',
        padding: '3rem 1.5rem',
        background: 'var(--bg-surface)',
        border: '1px dashed var(--border-subtle)',
        borderRadius: 'var(--radius-lg)',
        margin: '1.5rem 0',
      }}
    >
      <div style={{ fontSize: '2.5rem', marginBottom: '0.75rem' }} aria-hidden="true">
        {icon}
      </div>
      <h3 style={{ marginBottom: '0.5rem', color: 'var(--text-primary)' }}>{title}</h3>
      <p style={{ maxWidth: '450px', margin: '0 auto 1.25rem', color: 'var(--text-secondary)' }}>
        {description}
      </p>
      {actionLabel && onAction && (
        <button type="button" className="btn-primary" onClick={onAction}>
          {actionLabel}
        </button>
      )}
    </div>
  )
}
