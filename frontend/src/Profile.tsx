import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { ArrowLeft, Upload } from 'lucide-react'
import Header from './Header'
import TagEditor from './TagEditor'
import { loadPreferences, savePreferences } from './profilePreferences'
import type { ProfilePreferences } from './profilePreferences'

export default function Profile() {
  const [user, setUser] = useState<{ id: number; email: string } | null>(null)
  const [preferences, setPreferences] = useState<ProfilePreferences>({ skills: [], interests: [] })
  const [resume, setResume] = useState<File | null>(null)
  const [error, setError] = useState('')
  const navigate = useNavigate()

  useEffect(() => {
    const controller = new AbortController()

    async function loadUser() {
      try {
        const response = await fetch('/api/me', { signal: controller.signal })
        if (controller.signal.aborted) return
        if (response.status === 401) {
          navigate('/login', { replace: true })
          return
        }
        if (!response.ok) throw new Error('Could not load your profile.')
        const data = await response.json()
        if (!controller.signal.aborted) {
          setUser(data)
          setPreferences(loadPreferences(data.id))
        }
      } catch {
        if (!controller.signal.aborted) setError('Could not load your profile. Please try again.')
      }
    }

    void loadUser()
    return () => controller.abort()
  }, [navigate])

  function updatePreferences(field: keyof ProfilePreferences, values: string[]) {
    setPreferences((current) => ({ ...current, [field]: values }))
  }

  function save() {
    if (!user) return
    setError('')
    try {
      savePreferences(user.id, preferences)
    } catch {
      setError('Could not save in this browser. Your changes are still shown here.')
    }
  }

  return (
    <div className="min-h-screen text-ink">
      <Header loggedIn={Boolean(user)} />
      <main className="mx-auto max-w-2xl px-5 pt-10 pb-16 sm:px-10 sm:pt-14">
        <Link to="/" className="inline-flex items-center gap-2 rounded-sm text-sm text-muted hover:text-accent">
          <ArrowLeft size={15} aria-hidden="true" /> Back to search
        </Link>
        <h1 className="mt-8 font-serif text-4xl tracking-tight">Your profile</h1>
        <p className="mt-3 text-sm leading-6 text-muted">Manage your skills and resume.</p>

        {user ? (
          <>
            <section aria-labelledby="account-heading" className="mt-10 flex flex-wrap items-center justify-between gap-5 border-b border-line pb-7">
              <div className="min-w-0">
                <h2 id="account-heading" className="text-base font-medium">Account</h2>
                <p className="mt-2 break-words text-sm">{user.email}</p>
              </div>
            </section>

            <form onSubmit={(event) => { event.preventDefault(); save() }}>
              <section aria-labelledby="skills-heading" className="border-b border-line py-7">
                <h2 id="skills-heading" className="text-base font-medium">Skills</h2>
                <p className="mt-1 text-sm text-muted">Languages and tools you work with.</p>
                <TagEditor id="profile-skill" label="Skills" values={preferences.skills} onChange={(values) => updatePreferences('skills', values)} placeholder="e.g. Python or React" />
              </section>

              <section aria-labelledby="resume-heading" className="py-7">
                <h2 id="resume-heading" className="text-base font-medium">Resume <span className="ml-2 text-xs font-normal text-muted">Optional</span></h2>
                <p id="resume-help" className="mt-1 text-sm text-muted">Extract skills from your resume.</p>
                <div className="mt-4 flex flex-wrap items-center gap-4 rounded-lg border border-dashed border-line p-5">
                  <Upload size={21} strokeWidth={1.5} className="shrink-0 text-muted" aria-hidden="true" />
                  <div className="min-w-0 flex-1">
                    <label htmlFor="resume" className="block text-sm">Choose a resume</label>
                    <p className="mt-1 text-xs text-muted">PDF, DOC, or DOCX</p>
                  </div>
                  <input id="resume" type="file" accept=".pdf,.doc,.docx" aria-describedby="resume-help" onChange={(event) => setResume(event.target.files?.[0] || null)} className="w-full min-w-0 text-xs text-muted file:mr-3 file:cursor-pointer file:rounded-md file:border file:border-line file:bg-transparent file:px-3 file:py-2 file:text-ink" />
                  {resume && <p role="status" className="w-full break-all text-xs text-muted">Selected: {resume.name}. The file is cleared when you leave this page.</p>}
                </div>
              </section>

              <div className="mt-3 flex flex-wrap items-center gap-4">
                <button type="submit" className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-white hover:bg-accent-hover">Save profile</button>
              </div>
            </form>
          </>
        ) : !error && <p role="status" className="mt-10 text-sm text-muted">Loading profile...</p>}
        {error && <p role="alert" className="mt-5 text-sm text-red-800">{error}</p>}
      </main>
    </div>
  )
}
