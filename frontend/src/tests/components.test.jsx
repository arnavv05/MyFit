import React from 'react'
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Badge } from '../components/Badge'
import { EmptyState } from '../components/EmptyState'
import { Alert } from '../components/Alert'
import { AuthProvider } from '../context/AuthContext'
import { LoginPage } from '../pages/LoginPage'
import { OnboardingPage } from '../pages/OnboardingPage'
import { RecommendationsPage } from '../pages/RecommendationsPage'

describe('UI Components & Accessibility', () => {
  it('renders veg badge with correct aria attributes and icon', () => {
    render(<Badge type="veg" />)
    const badge = screen.getByRole('status')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent('VEG')
    expect(badge).toHaveAttribute('aria-label', 'Vegetarian diet item')
  })

  it('renders non-veg badge with correct aria attributes and icon', () => {
    render(<Badge type="nonveg" />)
    const badge = screen.getByRole('status')
    expect(badge).toBeInTheDocument()
    expect(badge).toHaveTextContent('NON-VEG')
    expect(badge).toHaveAttribute('aria-label', 'Non-vegetarian diet item')
  })

  it('renders EmptyState with custom title, description, and action trigger', () => {
    const handleAction = vi.fn()
    render(
      <EmptyState
        icon="⚡"
        title="No items found"
        description="Try adjusting your filters or rating more items."
        actionLabel="Explore Catalog"
        onAction={handleAction}
      />
    )

    expect(screen.getByText('No items found')).toBeInTheDocument()
    expect(screen.getByText('Try adjusting your filters or rating more items.')).toBeInTheDocument()

    const btn = screen.getByRole('button', { name: 'Explore Catalog' })
    fireEvent.click(btn)
    expect(handleAction).toHaveBeenCalledTimes(1)
  })

  it('renders Alert component with error role and dismiss button', () => {
    const handleClose = vi.fn()
    render(<Alert type="error" message="Invalid email or password" onClose={handleClose} />)

    const alert = screen.getByRole('alert')
    expect(alert).toBeInTheDocument()
    expect(alert).toHaveTextContent('Invalid email or password')

    const closeBtn = screen.getByRole('button', { name: 'Dismiss message' })
    fireEvent.click(closeBtn)
    expect(handleClose).toHaveBeenCalledTimes(1)
  })

  it('renders LoginPage with accessible labels and required validation', () => {
    const navigateMock = vi.fn()
    render(
      <AuthProvider>
        <LoginPage onNavigate={navigateMock} />
      </AuthProvider>
    )

    expect(screen.getByLabelText(/Email Address/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Password/i)).toBeInTheDocument()

    // Trigger submit with empty fields
    const submitBtn = screen.getByRole('button', { name: /Sign In/i })
    fireEvent.click(submitBtn)

    expect(screen.getByRole('alert')).toHaveTextContent(/Please provide both email and password/i)
  })

  it('renders OnboardingPage with accessible form controls and injury tag additions', () => {
    const navigateMock = vi.fn()
    render(
      <AuthProvider>
        <OnboardingPage onNavigate={navigateMock} />
      </AuthProvider>
    )

    expect(screen.getByLabelText(/Age \(years\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Height \(cm\)/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/Target Weight \(kg\)/i)).toBeInTheDocument()

    // Add a common injury tag
    const kneeBtn = screen.getByRole('button', { name: /\+ Knee strain/i })
    fireEvent.click(kneeBtn)
    expect(screen.getByLabelText('Remove Knee strain')).toBeInTheDocument()
  })

  it('renders RecommendationsPage with explainability reason badges and items', async () => {
    render(<RecommendationsPage />)

    // Verify recommendations heading and content render
    expect(screen.getByText(/Today's Personalized Plan/i)).toBeInTheDocument()
    expect(await screen.findByText(/Recommended Workouts/i)).toBeInTheDocument()
    expect(await screen.findByText(/Brisk Walking/i)).toBeInTheDocument()
    expect(await screen.findAllByText(/Why recommended:/i)).toBeTruthy()
  })
})
