import type { Model } from '../../types'

interface Props {
  models: Model[]
  value: string
  onChange: (id: string) => void
}

export function ModelPicker({ models, value, onChange }: Props) {
  if (models.length === 0) return (
    <p className="text-sm text-gray-400">Validate your key to load models.</p>
  )
  return (
    <select
      value={value}
      onChange={e => onChange(e.target.value)}
      className="w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
    >
      <option value="">Select a model…</option>
      {models.map(m => (
        <option key={m.id} value={m.id}>{m.name || m.id}</option>
      ))}
    </select>
  )
}
