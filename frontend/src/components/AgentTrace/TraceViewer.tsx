import { useTrace } from '../../hooks/useTrace'
import { TraceStepCard } from './TraceStep'

interface Props { ticketId: string | null; apiKey: string; model: string }

export function TraceViewer({ ticketId, apiKey, model }: Props) {
  const { result, loading, error, run } = useTrace()

  if (!ticketId) return (
    <div className="text-sm text-gray-400 text-center py-16">Select a ticket to run the agents.</div>
  )

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="font-semibold">Agent Trace</h2>
        <button
          onClick={() => run(ticketId, apiKey, model)}
          disabled={loading || !apiKey || !model}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-md hover:bg-indigo-700 disabled:opacity-50"
        >
          {loading ? 'Running agents…' : 'Run Agents'}
        </button>
      </div>

      {error && <p className="text-red-500 text-sm bg-red-50 p-3 rounded">{error}</p>}

      {loading && (
        <div className="space-y-3">
          {['router', 'diagnosis', 'resolution'].map(s => (
            <div key={s} className="animate-pulse h-20 rounded-lg bg-gray-100" />
          ))}
        </div>
      )}

      {result && (
        <div className="space-y-3">
          <div className={`text-sm font-medium px-3 py-2 rounded ${result.escalated ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'}`}>
            {result.escalated ? '🚨 Escalated to human agent' : '✓ Auto-resolved'}
            {' '}— confidence: {(result.confidence * 100).toFixed(0)}%
          </div>
          {result.trace.map((step, i) => <TraceStepCard key={i} step={step} />)}
          {result.escalation_summary && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-sm font-medium text-red-700 mb-1">Escalation Handoff Summary</p>
              <p className="text-sm text-gray-700 whitespace-pre-wrap">{result.escalation_summary}</p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
