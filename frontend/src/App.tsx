import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, ChevronDown, Search } from 'lucide-react'
import { searchRepositories } from './api'
import type { SearchMode, SearchResponse } from './api'
import Header from './Header'
import RepositoryResult from './RepositoryResult'
import { loadPreferences } from './profilePreferences'

const examples = ['Web crawler', 'Developer tools', 'Online book reader']

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [query, setQuery] = useState('')
  const [skills, setSkills] = useState('')
  const [mode, setMode] = useState<SearchMode>('personalized')
  const [limit, setLimit] = useState(5)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const queryInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/me', { signal: controller.signal })
      .then((response) => response.ok ? response.json() : null)
      .then((user) => {
        if (!user || controller.signal.aborted) return
        setLoggedIn(true)
        setSkills(loadPreferences(user.id).skills.join(', '))
      })
      .catch(() => {})
    return () => controller.abort()
  }, [])

  async function runSearch(searchQuery: string) {
    if (loading) return
    if (!searchQuery.trim()) {
      queryInput.current?.focus()
      return
    }

    setLoading(true)
    setError('')
    setResponse(null)
    try {
      const result = await searchRepositories(
        searchQuery.trim(),
        mode === 'keywords' ? [] : skills.split(',').map((skill) => skill.trim()).filter(Boolean),
        mode,
        limit,
      )
      setResponse(result)
    } catch (cause) {
      setError(cause instanceof DOMException && cause.name === 'TimeoutError'
        ? 'Search took too long. Please try again.'
        : cause instanceof TypeError
          ? 'Could not reach search. Please try again.'
          : cause instanceof Error ? cause.message : 'Search failed. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void runSearch(query)
  }

  return (
    <div className="min-h-screen text-ink selection:bg-accent-soft">
      <a href="#query" className="sr-only rounded-md bg-accent px-4 py-2 text-white focus:not-sr-only focus:absolute focus:top-3 focus:left-3">Skip to search</a>
      <Header loggedIn={loggedIn} onLogout={() => { setLoggedIn(false); setSkills('') }} />

      <main className="mx-auto max-w-5xl px-5 pb-16 sm:px-10">
        <section aria-labelledby="search-heading" className="pt-16 sm:pt-24">
          <h1 id="search-heading" className="max-w-xl font-serif text-4xl leading-[1.12] tracking-tight sm:text-5xl">Find your next contribution.</h1>
          <p className="mt-5 text-base leading-7 text-muted">Search open-source projects by what you want to build.</p>

          <form onSubmit={handleSubmit} className="mt-9">
            <div className="flex items-center gap-3 rounded-lg border border-line bg-white p-2 focus-within:border-accent sm:gap-4 sm:p-2.5">
              <Search size={20} strokeWidth={1.5} className="ml-2 shrink-0 text-muted" aria-hidden="true" />
              <label htmlFor="query" className="sr-only">Search repositories</label>
              <input ref={queryInput} id="query" type="search" required maxLength={1000} value={query} onChange={(event) => setQuery(event.target.value)} placeholder="What would you like to build?" className="min-w-0 flex-1 bg-transparent py-3 text-base placeholder:text-muted focus-visible:outline-none" />
              <button type="submit" disabled={loading || !query.trim()} aria-label={loading ? 'Searching repositories' : 'Search repositories'} className="rounded-md bg-accent p-3 text-white hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50">
                <ArrowRight size={21} aria-hidden="true" />
              </button>
            </div>

            {loggedIn && (
              <div className="mt-3 flex flex-wrap justify-between gap-2 text-xs text-muted">
                <span className="min-w-0 break-words">{mode === 'keywords' ? 'Keyword search · profile skills are off' : skills ? `Search skills: ${skills}` : 'Add skills to personalize your search'}</span>
                <Link to="/profile" className="shrink-0 text-accent underline-offset-4 hover:underline">Edit profile</Link>
              </div>
            )}

            <div className="mt-6 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs text-muted">
              <span>Try</span>
              {examples.map((example) => (
                <button key={example} type="button" disabled={loading} onClick={() => { setQuery(example); void runSearch(example) }} className="rounded-sm py-1 text-accent underline-offset-4 hover:underline disabled:opacity-50">{example}</button>
              ))}
            </div>

            <details className="group mt-5">
              <summary className="flex w-fit cursor-pointer list-none items-center gap-2 rounded-sm py-1 text-xs text-muted hover:text-ink [&::-webkit-details-marker]:hidden">
                Search options <ChevronDown size={13} className="group-open:rotate-180" aria-hidden="true" />
              </summary>
              <fieldset disabled={loading} className="mt-4 grid gap-5 border-y border-line py-5 sm:grid-cols-2">
                <div className="sm:col-span-2">
                  <label htmlFor="skills" className="block text-xs text-muted">Skills for this search (optional)</label>
                  <input id="skills" value={skills} onChange={(event) => setSkills(event.target.value)} disabled={mode === 'keywords'} placeholder="Python, JavaScript, React" className="mt-2 w-full border-b border-line bg-transparent py-2 text-sm placeholder:text-muted disabled:opacity-50" />
                </div>
                <div>
                  <label htmlFor="mode" className="block text-xs text-muted">Matching</label>
                  <select id="mode" value={mode} onChange={(event) => setMode(event.target.value as SearchMode)} className="mt-2 w-full bg-transparent py-2 text-sm">
                    <option value="personalized">Relevance + skills</option>
                    <option value="keywords">Keywords only</option>
                  </select>
                </div>
                <div>
                  <label htmlFor="limit" className="block text-xs text-muted">Results per search</label>
                  <select id="limit" value={limit} onChange={(event) => setLimit(Number(event.target.value))} className="mt-2 w-full bg-transparent py-2 text-sm">
                    <option value={5}>5 results</option>
                    <option value={10}>10 results</option>
                    <option value={20}>20 results</option>
                  </select>
                </div>
              </fieldset>
            </details>
          </form>
        </section>

        <section aria-labelledby="results-heading" aria-busy={loading} className="mt-16 sm:mt-20">
          <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-line pb-4">
            <h2 id="results-heading" className="text-base font-medium">{response ? 'Search results' : 'Repositories'}</h2>
            {response && <span className="text-xs text-muted">{response.results.length} matches · {response.repository_count.toLocaleString()} repositories</span>}
          </div>
          <p role="status" className="sr-only">{loading ? 'Searching repositories.' : response ? `${response.results.length} matches found for ${response.query}.` : ''}</p>
          {error && <p role="alert" className="py-8 text-sm text-red-800">{error}</p>}
          {loading ? (
            <p className="py-10 text-sm text-muted">Searching repositories…</p>
          ) : response ? (
            response.results.length ? (
              <>
                <p className="py-5 text-xs text-muted">Results for “{response.query}”</p>
                <ol className="list-none">{response.results.map((repository) => <RepositoryResult key={repository.name} repository={repository} mode={response.mode} />)}</ol>
              </>
            ) : <p className="py-10 text-sm text-muted">No matches found. Try a broader search.</p>
          ) : !error && <p className="py-10 text-sm text-muted">Enter a project idea to see matches.</p>}
        </section>
      </main>
    </div>
  )
}
