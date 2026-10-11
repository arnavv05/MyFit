import React from 'react'

/**
 * Badge Component:
 * Renders diet indicators (veg vs non-veg) and status tags.
 * Required by section 6.1 and 6.4 of the project contract.
 *
 * @param {{ type: 'veg' | 'nonveg' | 'info' | 'warning', text?: string }} props
 */
export function Badge({ type = 'info', text }) {
  if (type === 'veg') {
    return (
      <span className="badge badge-veg" role="status" aria-label="Vegetarian diet item">
        <span aria-hidden="true">🌱</span> {text || 'VEG'}
      </span>
    )
  }

  if (type === 'nonveg') {
    return (
      <span className="badge badge-nonveg" role="status" aria-label="Non-vegetarian diet item">
        <span aria-hidden="true">🍖</span> {text || 'NON-VEG'}
      </span>
    )
  }

  return (
    <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.1)', color: '#e5e7eb' }}>
      {text}
    </span>
  )
}
