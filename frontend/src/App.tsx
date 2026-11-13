import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import {
  ArrowRight,
  ArrowUpRight,
  CircleAlert,
  GitFork,
  Search,
} from 'lucide-react'
import { searchRepositories } from './api'
import type { SearchMode, SearchResponse } from './api'
import RepositoryResult from './RepositoryResult'

const examples = ['Online book reader', 'Web crawler', 'Developer tools']

export default function App() {
  const [query, setQuery] = useState('')
  const [skills, setSkills] = useState('')
  const [mode, setMode] = useState<SearchMode>('personalized')
  const [limit, setLimit] = useState(5)
  const [response, setResponse] = useState<SearchResponse | null>(null)
  const [repositoryCount, setRepositoryCount] = useState<number | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const queryInput = useRef<HTMLInputElement>(null)

  useEffect(() => {
    const controller = new AbortController()
    fetch('/api/status', { signal: controller.signal })
      .then((response) => (response.ok ? response.json() : null))
      .then((status) => {
        if (status && !controller.signal.aborted)
          setRepositoryCount(status.repository_count)
      })
      .catch(() => {
        /* A search reports connection errors with a recovery message */
      })
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
        mode === 'keywords'
          ? []
          : skills
              .split(',')
              .map((skill) => skill.trim())
              .filter(Boolean),
        mode,
        limit,
      )
      setResponse(result)
      setRepositoryCount(result.repository_count)
    } catch (cause) {
      setError(
        cause instanceof TypeError
          ? 'Could not reach search. Check that the Python API is running, then try again.'
          : cause instanceof DOMException && cause.name === 'TimeoutError'
            ? 'Search took too long. Please try again.'
            : cause instanceof Error
              ? cause.message
              : 'Search failed. Please try again.',
      )
    } finally {
      setLoading(false)
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    void runSearch(query)
  }

  return (
    <div className="min-h-screen bg-canvas text-ink selection:bg-accent-soft selection:text-accent">
      <a
        href="#search"
        className="sr-only z-10 rounded-md bg-accent px-4 py-2 text-white focus:not-sr-only focus:absolute focus:top-3 focus:left-3"
      >
        Skip to search
      </a>

      <header className="border-b border-line">
        <div className="mx-auto flex h-20 max-w-5xl items-center justify-between gap-4 px-5 sm:px-10">
          <div className="flex items-center gap-2.5">
            <GitFork
              size={23}
              strokeWidth={2}
              className="text-accent"
              aria-hidden="true"
            />
            <span className="text-lg font-semibold tracking-tight">
              RepoMatch
            </span>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-5xl px-5 pt-14 pb-12 sm:px-10 sm:pt-20">
        <section aria-labelledby="search-heading">
          <h1
            id="search-heading"
            className="text-3xl leading-tight font-semibold tracking-[-0.035em] text-balance sm:text-[42px]"
          >
            Find your next contribution
          </h1>

          <form
            id="search"
            onSubmit={handleSubmit}
            className="mt-8 overflow-hidden rounded-2xl border border-line bg-white"
          >
            <div className="flex flex-wrap items-center gap-3 p-3 sm:flex-nowrap sm:p-4">
              <Search
                size={21}
                strokeWidth={1.7}
                className="ml-2 shrink-0 text-muted"
                aria-hidden="true"
              />
              <label htmlFor="query" className="sr-only">
                Describe the project you want to find
              </label>
              <input
                ref={queryInput}
                id="query"
                type="search"
                required
                maxLength={1000}
                value={query}
                onChange={(event) => setQuery(event.target.value)}
                placeholder="What would you like to build?"
                className="min-w-0 flex-1 rounded-sm py-3 text-base placeholder:text-muted sm:text-lg"
              />
              <button
                type="submit"
                disabled={loading || !query.trim()}
                className="flex w-full cursor-pointer items-center justify-center gap-3 rounded-lg bg-accent px-5 py-3 text-sm font-medium text-white transition-colors hover:bg-accent-hover active:bg-accent-hover disabled:cursor-not-allowed disabled:bg-disabled motion-reduce:transition-none sm:w-auto"
              >
                {loading ? 'Searching…' : 'Find repositories'}
                <ArrowRight size={16} aria-hidden="true" />
              </button>
            </div>

            <fieldset
              disabled={loading}
              className="grid gap-5 border-t border-line bg-surface/60 px-5 py-4 disabled:opacity-60 sm:grid-cols-[1fr_auto] sm:gap-8"
            >
              <div className="min-w-0">
                <label
                  htmlFor="skills"
                  className="block text-xs font-medium text-muted"
                >
                  Your skills{' '}
                  <span className="font-normal">
                    (optional)
                  </span>
                </label>
                <input
                  id="skills"
                  value={skills}
                  onChange={(event) => setSkills(event.target.value)}
                  disabled={mode === 'keywords'}
                  placeholder={
                    mode === 'keywords'
                      ? 'Not used in keyword mode'
                      : 'e.g. Python, JavaScript, React'
                  }
                  className="mt-1 w-full rounded-sm bg-transparent py-1 text-sm placeholder:text-muted disabled:cursor-not-allowed disabled:text-muted"
                />
              </div>
              <div>
                <label
                  htmlFor="mode"
                  className="block text-xs font-medium text-muted"
                >
                  Matching
                </label>
                <select
                  id="mode"
                  value={mode}
                  onChange={(event) =>
                    setMode(event.target.value as SearchMode)
                  }
                  className="mt-1 max-w-full cursor-pointer rounded-sm bg-transparent py-1 pr-3 text-sm"
                >
                  <option value="personalized">Relevance + skills</option>
                  <option value="keywords">Keywords only</option>
                </select>
              </div>
            </fieldset>
          </form>

          <div className="mt-4 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-muted">
            <span>Try a search</span>
            {examples.map((example) => (
              <button
                key={example}
                type="button"
                disabled={loading}
                onClick={() => {
                  setQuery(example)
                  void runSearch(example)
                }}
                className="inline-flex cursor-pointer items-center gap-1 rounded-sm py-1 text-accent underline-offset-4 hover:underline disabled:cursor-not-allowed disabled:opacity-50"
              >
                {example}
                <ArrowUpRight size={12} aria-hidden="true" />
              </button>
            ))}
          </div>
        </section>

        <section
          aria-labelledby="results-heading"
          aria-busy={loading}
          className="mt-14 sm:mt-16"
        >
          <div className="flex flex-wrap items-center justify-between gap-3 border-b border-line pb-4">
            <div className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
              <h2 id="results-heading" className="text-base font-semibold">
                Results
              </h2>
              <span className="text-xs text-muted">
                {repositoryCount !== null
                  ? `${repositoryCount.toLocaleString()} total repositories`
                  : 'Local collection'}
              </span>
            </div>
            <div className="flex items-center gap-2 text-xs text-muted">
              <label htmlFor="limit">Results per search</label>
              <select
                id="limit"
                value={limit}
                disabled={loading}
                onChange={(event) => setLimit(Number(event.target.value))}
                aria-describedby="limit-help"
                className="cursor-pointer rounded-md border border-line bg-white px-2 py-1.5 text-ink disabled:cursor-not-allowed"
              >
                <option value={5}>5 results</option>
                <option value={10}>10 results</option>
                <option value={20}>20 results</option>
              </select>
              <span id="limit-help" className="sr-only">
                Applies to your next search
              </span>
            </div>
          </div>

          <p role="status" className="sr-only">
            {loading
              ? 'Searching repositories.'
              : response
                ? `${response.results.length} matches found for ${response.query}.`
                : ''}
          </p>

          {error && (
            <div
              role="alert"
              className="my-6 flex items-start gap-3 rounded-xl border border-red-200 bg-red-50 p-5 text-sm leading-6 text-red-800"
            >
              <CircleAlert
                size={18}
                className="mt-1 shrink-0"
                aria-hidden="true"
              />
              <div>
                <p className="font-semibold">Search couldn’t finish</p>
                <p>{error}</p>
              </div>
            </div>
          )}

          {loading ? (
            <div aria-hidden="true" className="divide-y divide-line">
              {[0, 1, 2].map((index) => (
                <div
                  key={index}
                  className="space-y-3 py-7 motion-safe:animate-pulse"
                >
                  <div className="h-4 w-2/5 rounded bg-line" />
                  <div className="h-3 w-4/5 rounded bg-line/60" />
                  <div className="h-3 w-1/4 rounded bg-line/60" />
                </div>
              ))}
            </div>
          ) : response ? (
            response.results.length ? (
              <>
                <p className="pt-5 pb-3 text-xs text-muted">
                  {response.results.length} matches for{' '}
                  <span className="font-medium text-ink">
                    “{response.query}”
                  </span>
                  <span className="mx-2" aria-hidden="true">
                    /
                  </span>
                  {response.mode === 'keywords'
                    ? 'Keyword relevance'
                    : 'Relevance + skills'}
                </p>
                <ol className="list-none">
                  {response.results.map((repository) => (
                    <RepositoryResult
                      key={repository.name}
                      repository={repository}
                      mode={response.mode}
                    />
                  ))}
                </ol>
              </>
            ) : (
              <div className="py-12">
                <h3 className="text-lg font-medium">
                  No matches found.
                </h3>
                <p className="mt-2 max-w-lg text-sm leading-6 text-muted">
                  Try a broader search.
                </p>
              </div>
            )
          ) : (
            !error && (
              <p className="py-12 text-sm text-muted">
                Enter a project idea to see matches.
              </p>
            )
          )}
        </section>

      </main>
    </div>
  )
}
