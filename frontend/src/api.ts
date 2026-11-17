export type SearchMode = 'personalized' | 'keywords'

export interface UserProfile {
  id: number
  email: string
  skills: string[]
}

export async function saveSkills(skills: string[]): Promise<string[]> {
  const response = await fetch('/api/me/skills', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ skills }),
  })
  if (!response.ok) {
    throw new Error(response.status === 401
      ? 'Your session expired. Log in again to save your skills.'
      : response.status === 422
        ? 'Use up to 50 nonempty skills, each at most 100 characters.'
        : 'Could not save your skills. Please try again.')
  }
  const data = await response.json()
  return data.skills
}

export interface Repository {
  name: string
  url: string
  language: string
  description: string
  score: number
  bm25: number
  semantic: number
  skill_match: number
  reasons: string[]
}

export interface SearchResponse {
  results: Repository[]
  repository_count: number
  query: string
  mode: SearchMode
}

export async function searchRepositories(
  query: string,
  skills: string[],
): Promise<SearchResponse> {
  const response = await fetch('/api/search', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ query, skills }),
    signal: AbortSignal.timeout(30000),
  })

  if (!response.ok) {
    throw new Error(
      response.status === 422
        ? 'Use a project description under 1,000 characters and up to 50 skills of 100 characters each.'
        : 'Search is unavailable. Check that the Python API is running, then try again.',
    )
  }

  return response.json()
}
