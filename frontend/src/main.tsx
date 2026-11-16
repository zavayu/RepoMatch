import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import App from './App'
import Login from './Login'
import './styles.css'

function ProtectedRoute() {
  const [status, setStatus] = useState<'loading' | 'logged-in' | 'logged-out'>('loading')

  useEffect(() => {
    fetch('/api/me')
      .then(res => setStatus(res.ok ? 'logged-in' : 'logged-out'))
      .catch(() => setStatus('logged-out'))
  }, [])

  if (status === 'loading') return <p>Loading...</p>

  return status === 'logged-in'
    ? <App />
    : <Navigate to="/login" replace />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<ProtectedRoute />} />
        <Route path="/login" element={<Login />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)