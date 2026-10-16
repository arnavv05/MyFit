import React, { useState, useEffect } from 'react'
import { AuthProvider } from './context/AuthContext'
import { useAuth } from './hooks/useAuth'
import { Navbar } from './components/Navbar'
import { LoginPage } from './pages/LoginPage'
import { RegisterPage } from './pages/RegisterPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { DailyLogPage } from './pages/DailyLogPage'
import { RecommendationsPage } from './pages/RecommendationsPage'
import { ProgressPage } from './pages/ProgressPage'

/**
 * MainAppContent:
 * Handles screen transitions and guards routes requiring authentication.
 */
function MainAppContent() {
  const { isAuthenticated, loading } = useAuth()
  const [currentPage, setCurrentPage] = useState('daily-log')

  // Sync hash routing so back/forward browser buttons work smoothly
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.replace('#/', '')
      if (hash) setCurrentPage(hash)
    }
    window.addEventListener('hashchange', handleHashChange)
    if (window.location.hash) handleHashChange()
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const navigateTo = (page) => {
    setCurrentPage(page)
    window.location.hash = `#/${page}`
  }

  if (loading) {
    return (
      <div style={{ textAlign: 'center', marginTop: '4rem', color: 'var(--text-secondary)' }}>
        Loading MyFitness...
      </div>
    )
  }

  // Route guarding: redirect unauthenticated users to login
  if (!isAuthenticated && currentPage !== 'register') {
    return (
      <>
        <Navbar currentTab="login" onSelectTab={navigateTo} />
        <main>
          <LoginPage onNavigate={navigateTo} />
        </main>
      </>
    )
  }

  if (!isAuthenticated && currentPage === 'register') {
    return (
      <>
        <Navbar currentTab="register" onSelectTab={navigateTo} />
        <main>
          <RegisterPage onNavigate={navigateTo} />
        </main>
      </>
    )
  }

  return (
    <>
      <Navbar currentTab={currentPage} onSelectTab={navigateTo} />
      <main style={{ paddingBottom: '3rem' }}>
        {currentPage === 'daily-log' && <DailyLogPage onNavigate={navigateTo} />}
        {currentPage === 'recommendations' && <RecommendationsPage />}
        {currentPage === 'progress' && <ProgressPage onNavigate={navigateTo} />}
        {currentPage === 'onboarding' && <OnboardingPage onNavigate={navigateTo} />}
        {currentPage === 'login' && <DailyLogPage onNavigate={navigateTo} />}
        {currentPage === 'register' && <DailyLogPage onNavigate={navigateTo} />}
      </main>
    </>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <MainAppContent />
    </AuthProvider>
  )
}
