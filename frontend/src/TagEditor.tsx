import { useState } from 'react'
import { X } from 'lucide-react'

interface Props {
  id: string
  label: string
  values: string[]
  onChange: (values: string[]) => void
  placeholder: string
}

export default function TagEditor({ id, label, values, onChange, placeholder }: Props) {
  const [draft, setDraft] = useState('')

  function addTag() {
    const value = draft.trim()
    if (!value || values.length >= 50) return
    if (!values.some((item) => item.toLowerCase() === value.toLowerCase())) {
      onChange([...values, value])
    }
    setDraft('')
  }

  return (
    <div className="mt-4">
      <ul aria-label={label} className="flex flex-wrap gap-2">
        {values.map((value) => (
          <li key={value} className="inline-flex max-w-full items-center gap-2 rounded-full bg-surface py-1.5 pr-2 pl-3 text-sm">
            <span className="min-w-0 break-words">{value}</span>
            <button type="button" onClick={() => onChange(values.filter((item) => item !== value))} aria-label={`Remove ${value}`} className="shrink-0 rounded-full p-1 text-muted hover:text-ink">
              <X size={13} aria-hidden="true" />
            </button>
          </li>
        ))}
      </ul>
      <div className="mt-3 flex gap-3">
        <label htmlFor={id} className="sr-only">Add {label.toLowerCase()}</label>
        <input id={id} value={draft} maxLength={100} disabled={values.length >= 50}
          onChange={(event) => setDraft(event.target.value)}
          onKeyDown={(event) => {
            if (event.key === 'Enter') {
              event.preventDefault()
              addTag()
            }
          }}
          placeholder={placeholder}
          className="min-w-0 flex-1 border-b border-line bg-transparent py-2 text-sm placeholder:text-muted focus:border-accent"
        />
        <button type="button" onClick={addTag} disabled={!draft.trim() || values.length >= 50} className="rounded-sm px-2 text-sm font-medium text-accent disabled:opacity-40">Add</button>
      </div>
    </div>
  )
}
