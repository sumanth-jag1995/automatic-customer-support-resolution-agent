import type { TraceStep as Step } from '../../types'

const stepColors: Record<string, string> = {
  router: 'border-blue-400 bg-blue-50',
  diagnosis: 'border-purple-400 bg-purple-50',
  resolution: 'border-green-400 bg-green-50',
  escalation: 'border-red-400 bg-red-50',
}

const stepIcons: Record<string, string> = {
  router: '🔀',
  diagnosis: '🔍',
  resolution: '⚙️',
  escalation: '🚨',
}

export function TraceStepCard({ step }: { step: Step }) {
  return (
    <div className={`border-l-4 rounded-r-lg p-4 ${stepColors[step.step] ?? 'border-gray-300 bg-gray-50'}`}>
      <div className="flex items-center gap-2 mb-2">
        <span>{stepIcons[step.step] ?? '•'}</span>
        <span className="font-semibold text-sm capitalize">{step.step} Agent</span>
        {step.confidence != null && (
          <span className="ml-auto text-xs text-gray-500">
            confidence: {(step.confidence * 100).toFixed(0)}%
          </span>
        )}
      </div>
      <p className="text-sm text-gray-700 mb-1"><span className="font-medium">Thought:</span> {step.thought}</p>
      {step.tool && (
        <p className="text-xs font-mono bg-white border border-gray-200 rounded px-2 py-1 mt-1">
          Tool: {step.tool}({step.action})
        </p>
      )}
      {step.observation && (
        <p className="text-xs text-gray-500 mt-1 line-clamp-3">{step.observation}</p>
      )}
    </div>
  )
}
