import { useEffect, useState } from 'react'
import { metricsApi } from '../../api/metrics'
import { MetricCard } from './MetricCard'
import type { Metrics } from '../../types'

export function MetricsDashboard() {
  const [metrics, setMetrics] = useState<Metrics | null>(null)

  useEffect(() => {
    metricsApi.get().then(setMetrics).catch(() => {})
    const id = setInterval(() => metricsApi.get().then(setMetrics).catch(() => {}), 10000)
    return () => clearInterval(id)
  }, [])

  if (!metrics) return <p className="text-sm text-gray-400">Loading metrics…</p>

  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Metrics Dashboard</h2>
      <div className="grid grid-cols-2 gap-4">
        <MetricCard label="Total Tickets" value={metrics.total} />
        <MetricCard label="Auto-Resolution Rate" value={`${(metrics.auto_resolution_rate * 100).toFixed(1)}%`} color="text-green-600" sub="target: 80%" />
        <MetricCard label="Escalation Rate" value={`${(metrics.escalation_rate * 100).toFixed(1)}%`} color="text-red-500" />
        <MetricCard label="Avg Confidence" value={`${(metrics.avg_confidence * 100).toFixed(0)}%`} color="text-indigo-600" />
        <MetricCard label="Resolved" value={metrics.resolved} color="text-green-600" />
        <MetricCard label="Escalated" value={metrics.escalated} color="text-red-500" />
      </div>
    </div>
  )
}
