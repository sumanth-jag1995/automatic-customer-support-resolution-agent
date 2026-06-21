import { useEffect, useState } from 'react'
import { ticketsApi } from '../../api/tickets'
import type { Ticket } from '../../types'

export function EscalationQueue() {
  const [tickets, setTickets] = useState<Ticket[]>([])

  useEffect(() => {
    ticketsApi.list().then(all => setTickets(all.filter(t => t.status === 'escalated')))
  }, [])

  return (
    <div className="space-y-4">
      <h2 className="font-semibold">Human Escalation Queue</h2>
      {tickets.length === 0 && <p className="text-sm text-gray-400 text-center py-8">No escalated tickets.</p>}
      {tickets.map(t => (
        <div key={t.id} className="bg-white border border-red-200 rounded-xl p-4">
          <div className="flex items-start justify-between">
            <p className="font-medium text-sm">{t.subject}</p>
            <span className="text-xs bg-red-100 text-red-700 px-2 py-0.5 rounded-full">Escalated</span>
          </div>
          <p className="text-xs text-gray-500 mt-1">{t.body}</p>
          <div className="mt-2 flex gap-2 text-xs text-gray-400">
            <span>Customer: {t.customer_id}</span>
            <span>·</span>
            <span>Intent: {t.intent ?? '—'}</span>
            <span>·</span>
            <span>Confidence: {t.confidence != null ? `${(t.confidence * 100).toFixed(0)}%` : '—'}</span>
          </div>
        </div>
      ))}
    </div>
  )
}
