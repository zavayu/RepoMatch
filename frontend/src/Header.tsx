import { GitFork, UserRound } from 'lucide-react'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'

export default function Header({ loggedIn = false, onLogout }: { loggedIn?: boolean; onLogout?: () => void }) {
  const [loggingOut, setLoggingOut] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  async function logout() {
    setLoggingOut(true)
    setError('')
    try {
      const response = await fetch('/api/logout', { method: 'POST' })
      if (!response.ok) throw new Error('Logout failed')
      onLogout?.()
      navigate('/', { replace: true })
    } catch {
      setError('Could not log out. Please try again.')
    } finally {
      setLoggingOut(false)
    }
  }

  return (
    <header className="border-b border-line">
      <div className="mx-auto flex h-20 max-w-5xl items-center justify-between px-5 sm:px-10">
        <Link to="/" className="flex items-center gap-2.5">
          <GitFork size={22} strokeWidth={1.7} aria-hidden="true" />
          <span className="text-lg font-semibold tracking-tight">RepoMatch</span>
        </Link>
        {loggedIn ? (
          <div className="flex items-center gap-3">
            <Link to="/profile" aria-label="Your profile" title="Your profile" className="rounded-full p-2 text-accent hover:bg-surface">
              <UserRound size={23} strokeWidth={1.7} aria-hidden="true" />
            </Link>
            <button type="button" onClick={logout} disabled={loggingOut} className="rounded-md border border-line px-4 py-2 text-sm font-medium hover:border-accent disabled:opacity-50">
              {loggingOut ? 'Logging out...' : 'Log out'}
            </button>
          </div>
        ) : (
          <Link to="/login" className="rounded-md border border-line px-4 py-2 text-sm font-medium hover:border-accent hover:text-accent">Log in</Link>
        )}
      </div>
      {error && <p role="alert" className="mx-auto max-w-5xl px-5 pb-3 text-sm text-red-800 sm:px-10">{error}</p>}
    </header>
  )
}
