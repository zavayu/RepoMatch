import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft } from 'lucide-react'
import Header from './Header'

export default function Login() {
  const [signup, setSignup] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [message, setMessage] = useState('')
  const [loading, setLoading] = useState(false)
  const navigate = useNavigate()

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (loading) return
    setLoading(true)
    setMessage('')

    try {
      const response = await fetch(signup ? '/api/signup' : '/api/login', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email, password }),
      })
      const data = await response.json()
      if (response.ok) {
        navigate('/')
        return
      }
      setMessage(typeof data.detail === 'string' ? data.detail : 'Check your email and password, then try again.')
    } catch {
      setMessage('Could not connect. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen text-ink">
      <Header showAccount={false} />
      <main className="mx-auto max-w-md px-5 pt-10 pb-16 sm:pt-14">
        <Link to="/" className="inline-flex items-center gap-2 rounded-sm text-sm text-muted hover:text-accent">
          <ArrowLeft size={15} aria-hidden="true" /> Back to search
        </Link>

        <h1 className="mt-8 font-serif text-4xl tracking-tight">{signup ? 'Create an account' : 'Log in'}</h1>
        <p className="mt-3 text-sm leading-6 text-muted">
          {signup ? 'Save your skills for future searches.' : 'Access your profile and saved skills.'}
        </p>

        <form onSubmit={submit} aria-busy={loading} className="mt-9">
          <fieldset disabled={loading} className="space-y-6">
            <div>
              <label htmlFor="email" className="block text-sm font-medium">Email</label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                placeholder="you@example.com"
                className="mt-2 w-full rounded-md border border-line bg-white px-3 py-3 text-sm placeholder:text-muted focus:border-accent disabled:opacity-60"
              />
            </div>
            <div>
              <label htmlFor="password" className="block text-sm font-medium">Password</label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete={signup ? 'new-password' : 'current-password'}
                required
                minLength={signup ? 8 : undefined}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                aria-describedby={signup ? 'password-help' : undefined}
                className="mt-2 w-full rounded-md border border-line bg-white px-3 py-3 text-sm focus:border-accent disabled:opacity-60"
              />
              {signup && <p id="password-help" className="mt-2 text-xs text-muted">At least 8 characters.</p>}
            </div>
            <button type="submit" className="w-full rounded-md bg-accent px-5 py-3 text-sm font-medium text-white hover:bg-accent-hover disabled:opacity-60">
              {loading ? (signup ? 'Creating account...' : 'Logging in...') : (signup ? 'Create account' : 'Log in')}
            </button>
          </fieldset>
          {message && <p role="alert" className="mt-4 text-sm leading-6 text-red-800">{message}</p>}
        </form>

        <p className="mt-8 border-t border-line pt-6 text-sm text-muted">
          {signup ? 'Already have an account? ' : 'No account yet? '}
          <button
            type="button"
            disabled={loading}
            onClick={() => {
              setSignup(!signup)
              setPassword('')
              setMessage('')
            }}
            className="rounded-sm font-medium text-accent underline-offset-4 hover:underline disabled:opacity-50"
          >
            {signup ? 'Log in' : 'Sign up'}
          </button>
        </p>
      </main>
    </div>
  )
}
