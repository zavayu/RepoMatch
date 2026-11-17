import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { ArrowRight, ChevronDown, Search } from 'lucide-react'
import { searchRepositories } from './api'
import type { SearchResponse } from './api'
import Header from './Header'
import RepositoryResult from './RepositoryResult'

const examples = ['Web crawler', 'Developer tools', 'Online book reader']
const pageSize = 10

export default function App() {
  const [loggedIn, setLoggedIn] = useState(false)
  const [query, setQuery] = useState('')
  const [skills, setSkills] = useState('')
  const [page, setPage] = useState(1)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const queryInput = useRef<HTMLInputElement>(null)
  const resultsHeading = useRef<HTMLHeadingElement>(null)
  const totalResults = response?.results.length ?? 0
  const totalPages = Math.ceil(totalResults / pageSize)
  const start = (page - 1) * pageSize
  const pageResults = response?.results.slice(start, start + pageSize) ?? []

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/me', { signal: controller.signal })
      .then((response) => response.ok ? response.json() : null)
      .then((user) => {
        if (!user || controller.signal.aborted) return
        setLoggedIn(true)
        setSkills(user.skills.join(', '))
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
    setPage(1)
    try {
      const result = await searchRepositories(
        searchQuery.trim(),
        skills.split(',').map((skill) => skill.trim()).filter(Boolean),
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

  function changePage(nextPage: number) {
    setPage(nextPage)
    resultsHeading.current?.focus({ preventScroll: true })
    resultsHeading.current?.scrollIntoView({ block: 'start' })
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
              <fieldset disabled={loading} className="mt-4 border-y border-line py-5">
                <div>
                  <div className="flex items-center justify-between gap-3 text-xs">
                    <label htmlFor="skills" className="text-muted">Skills for this search (optional)</label>
                    {loggedIn && <Link to="/profile" className="shrink-0 text-accent underline-offset-4 hover:underline">Edit profile</Link>}
                  </div>
                  <input id="skills" value={skills} onChange={(event) => setSkills(event.target.value)} placeholder="Python, JavaScript, React" className="mt-2 w-full border-b border-line bg-transparent py-2 text-sm placeholder:text-muted disabled:opacity-50" />
                </div>
              </fieldset>
            </details>
          </form>
        </section>

        <section aria-labelledby="results-heading" aria-busy={loading} className="mt-16 sm:mt-20">
          <div className="flex flex-wrap items-baseline justify-between gap-3 border-b border-line pb-4">
            <h2 ref={resultsHeading} tabIndex={-1} id="results-heading" className="scroll-mt-6 text-base font-medium">{response ? 'Search results' : 'Repositories'}</h2>
            {response && <span className="text-xs text-muted">{response.results.length} matches · {response.repository_count.toLocaleString()} repositories</span>}
          </div>
          <p role="status" className="sr-only">{loading ? 'Searching repositories.' : response ? `${totalResults} matches found for ${response.query}.${totalResults ? ` Page ${page} of ${totalPages}.` : ''}` : ''}</p>
          {error && <p role="alert" className="py-8 text-sm text-red-800">{error}</p>}
          {loading ? (
            <p className="py-10 text-sm text-muted">Searching repositories…</p>
          ) : response ? (
            response.results.length ? (
              <>
                <p className="py-5 text-xs text-muted">{start + 1}–{Math.min(start + pageSize, totalResults)} of {totalResults} matches for "{response.query}"</p>
                <ol start={start + 1} className="list-none">{pageResults.map((repository) => <RepositoryResult key={repository.name} repository={repository} mode={response.mode} />)}</ol>
                {totalPages > 1 && (
                  <nav aria-label="Search result pages" className="mt-6 flex items-center justify-between gap-3 border-t border-line pt-5 text-sm">
                    <button type="button" disabled={page === 1} onClick={() => changePage(page - 1)} className="rounded-md border border-line px-3 py-2 hover:border-accent disabled:cursor-not-allowed disabled:opacity-40">Previous</button>
                    <span className="text-xs text-muted">Page {page} of {totalPages}</span>
                    <button type="button" disabled={page === totalPages} onClick={() => changePage(page + 1)} className="rounded-md border border-line px-3 py-2 hover:border-accent disabled:cursor-not-allowed disabled:opacity-40">Next</button>
                  </nav>
                )}
              </>
            ) : <p className="py-10 text-sm text-muted">No matches found. Try a broader search.</p>
          ) : !error && <p className="py-10 text-sm text-muted">Enter a project idea to see matches.</p>}
        </section>
      </main>
    </div>
  )
}
