
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { GitFork } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
export default function Login() {
  const [signup, setSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function submit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setLoading(true)
    setMessage('')

    try {
      const res = await fetch(
        signup ? '/api/signup' : '/api/login',
        {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ email, password }),
        }
      )

      const data = await res.json()
      if (res.ok) {
        navigate('/')
        return
       }
      setMessage(data.message || data.detail || 'Request failed')
    } catch {
      setMessage('Cannot connect to server')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-canvas text-ink">
      <header className="border-b border-line">
        <div className="mx-auto flex h-20 max-w-5xl items-center px-5 sm:px-10">
          <Link to="/" className="flex items-center gap-2.5">
            <GitFork size={23} className="text-accent" />
            <span className="text-lg font-semibold">
              RepoMatch
            </span>
          </Link>
        </div>
      </header>

      <main className="mx-auto mt-20 max-w-md px-5">
        <div className="rounded-2xl border border-line bg-white p-8 shadow-sm">
          <h1 className="text-2xl font-semibold">
            {signup ? 'Create an account' : 'Welcome back'}
          </h1>

          <p className="mt-2 text-sm text-muted">
            {signup
              ? 'Sign up to get started with RepoMatch.'
              : 'Log in to your RepoMatch account.'}
          </p>

          <form onSubmit={submit} className="mt-8 space-y-5">
            <div>
              <label htmlFor="email" className="block text-sm font-medium">
                Email
              </label>
              <input
                id="email"
                type="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                placeholder="you@example.com"
                className="mt-2 w-full rounded-lg border border-line px-4 py-3 outline-none focus:border-accent"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium">
                Password
              </label>
              <input
                id="password"
                type="password"
                required
                minLength={signup ? 8 : undefined}
                value={password}
                onChange={e => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="mt-2 w-full rounded-lg border border-line px-4 py-3 outline-none focus:border-accent"
              />
              {signup && (
                <p className="mt-2 text-xs text-muted">
                  Must be at least 8 characters.
                </p>
              )}
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full cursor-pointer rounded-lg bg-accent px-5 py-3 font-medium text-white transition-colors hover:bg-accent-hover disabled:opacity-60"
            >
              {loading
                ? 'Please wait...'
                : signup ? 'Create Account' : 'Log In'}
            </button>
          </form>

          {message && (
            <p role="status" className="mt-4 text-center text-sm">
              {message}
            </p>
          )}

          <div className="mt-7 border-t border-line pt-6 text-center text-sm">
            <span className="text-muted">
              {signup
                ? 'Already have an account? '
                : "Don't have an account? "}
            </span>
            <button
              type="button"
              onClick={() => {
                setSignup(!signup)
                setMessage('')
              }}
              className="cursor-pointer font-medium text-accent hover:underline"
            >
              {signup ? 'Log In' : 'Sign Up'}
            </button>
          </div>
        </div>

        <div className="mt-6 text-center">
          <Link to="/" className="text-sm text-muted hover:text-accent">
            ← Back to RepoMatch
          </Link>
        </div>
      </main>
    </div>
  )
}
