import { ArrowUpRight, BookOpen, Check, ChevronDown } from 'lucide-react'
import type { Repository, SearchMode } from './api'

interface Props {
  repository: Repository
  mode: SearchMode
}

export default function RepositoryResult({ repository: repo, mode }: Props) {
  const matchingSkills = repo.reasons
    .find((reason) => reason.startsWith('matching skills: '))
    ?.replace('matching skills: ', '')

  return (
    <li className="border-b border-line py-7 first:pt-2 last:border-0">
      <article>
        <div className="flex items-start gap-3">
          <BookOpen
            size={19}
            strokeWidth={1.7}
            className="mt-1.5 shrink-0 text-muted"
            aria-hidden="true"
          />
          <div className="min-w-0 flex-1">
            <h3 className="text-lg font-semibold tracking-tight">
              <a
                href={repo.url}
                target="_blank"
                rel="noopener noreferrer"
                className="group inline-flex max-w-full items-start gap-2 rounded-sm text-ink underline-offset-4 hover:text-accent hover:underline"
              >
                <span className="break-words [overflow-wrap:anywhere]">
                  {repo.name}
                </span>
                <ArrowUpRight
                  size={17}
                  className="mt-1 shrink-0 text-muted group-hover:text-accent"
                  aria-hidden="true"
                />
                <span className="sr-only"> (opens on GitHub in a new tab)</span>
              </a>
            </h3>
            <p className="mt-2 max-w-[70ch] text-sm leading-6 text-muted [overflow-wrap:anywhere]">
              {repo.description ||
                'No description available.'}
            </p>
            <div className="mt-3 flex flex-wrap items-center gap-x-5 gap-y-2 text-xs">
              {repo.language && (
                <span className="font-medium text-ink">{repo.language}</span>
              )}
              {matchingSkills && (
                <span className="inline-flex items-center gap-1.5 text-accent">
                  <Check size={13} aria-hidden="true" />
                  Skills: {matchingSkills}
                </span>
              )}
            </div>

            <details className="group mt-4">
              <summary className="flex w-fit cursor-pointer list-none items-center gap-1.5 rounded-sm text-xs font-medium text-muted hover:text-accent [&::-webkit-details-marker]:hidden">
                Why this match
                <ChevronDown
                  size={13}
                  className="transition-transform duration-150 group-open:rotate-180 motion-reduce:transition-none"
                  aria-hidden="true"
                />
              </summary>
              <div className="mt-3 rounded-lg bg-surface p-4 text-xs leading-5 text-muted">
                <dl className="grid max-w-sm grid-cols-2 gap-x-6 gap-y-1.5">
                  <dt>Ranking score</dt>
                  <dd className="text-right font-medium text-ink tabular-nums">
                    {repo.score.toFixed(3)}
                  </dd>
                  <dt>Keyword relevance</dt>
                  <dd className="text-right tabular-nums">
                    {repo.bm25.toFixed(3)}
                  </dd>
                  {mode === 'personalized' && (
                    <>
                      <dt>Text similarity</dt>
                      <dd className="text-right tabular-nums">
                        {repo.semantic.toFixed(3)}
                      </dd>
                      <dt>Skill overlap</dt>
                      <dd className="text-right tabular-nums">
                        {repo.skill_match.toFixed(3)}
                      </dd>
                    </>
                  )}
                </dl>
                <p className="mt-3">
                  Relative scores, not confidence percentages.
                </p>
              </div>
            </details>
          </div>
        </div>
      </article>
    </li>
  )
}
