export interface ProfilePreferences {
  skills: string[]
  interests: string[]
}

// Keep the UI draft in this browser until account persistence is added
export function loadPreferences(userId: number): ProfilePreferences {
  try {
    const value = JSON.parse(localStorage.getItem(`repomatch-profile-${userId}`) || '{}')
    const readList = (items: unknown): string[] => Array.isArray(items)
      ? items.filter((item): item is string => typeof item === 'string' && item.length <= 100).slice(0, 50)
      : []
    return { skills: readList(value.skills), interests: readList(value.interests) }
  } catch {
    return { skills: [], interests: [] }
  }
}

export function savePreferences(userId: number, preferences: ProfilePreferences) {
  localStorage.setItem(`repomatch-profile-${userId}`, JSON.stringify(preferences))
}
