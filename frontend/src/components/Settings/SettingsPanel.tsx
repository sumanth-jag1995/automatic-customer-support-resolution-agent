import { useSettings } from '../../hooks/useSettings'
import { ModelPicker } from './ModelPicker'

export function SettingsPanel() {
  const { key, saveKey, model, saveModel, models, keyValid, loading, error, validate } = useSettings()

  return (
    <div className="space-y-4 p-6 bg-white rounded-xl shadow">
      <h2 className="text-lg font-semibold">API Settings</h2>

      <div>
        <label className="block text-sm font-medium mb-1">OpenRouter API Key</label>
        <div className="flex gap-2">
          <input
            type="password"
            value={key}
            onChange={e => saveKey(e.target.value)}
            placeholder="sk-or-…"
            className="flex-1 rounded-md border border-gray-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-600"
          />
          <button
            onClick={validate}
            disabled={loading || !key}
            className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50"
          >
            {loading ? 'Validating…' : 'Validate'}
          </button>
        </div>
        {keyValid === true && <p className="text-green-600 text-xs mt-1">✓ Key valid</p>}
        {keyValid === false && <p className="text-red-500 text-xs mt-1">{error || 'Key invalid'}</p>}
      </div>

      <div>
        <label className="block text-sm font-medium mb-1">Model</label>
        <ModelPicker models={models} value={model} onChange={saveModel} />
      </div>
    </div>
  )
}
