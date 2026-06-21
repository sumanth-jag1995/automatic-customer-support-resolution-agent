import { CustomerCard } from './CustomerCard'
import type { Ticket, ResolveResult } from '../../types'

interface Props { ticket: Ticket | null; result: ResolveResult | null }

export function CRMConsole({ ticket, result }: Props) {
  if (!ticket) return <div className="text-sm text-gray-400 text-center py-16">Select a ticket to view CRM data.</div>

  return (
    <div className="space-y-4">
      <h2 className="font-semibold">CRM Console</h2>
      <CustomerCard customerId={ticket.customer_id} />

      {result?.trace && result.trace.filter(s => s.tool).length > 0 && (
        <div>
          <p className="text-sm font-medium mb-2">Tool Actions Executed</p>
          <div className="space-y-2">
            {result.trace.filter(s => s.tool).map((s, i) => (
              <div key={i} className="bg-gray-50 border rounded-lg p-3 text-xs font-mono">
                <span className="text-purple-600 font-semibold">{s.tool}()</span>
                <p className="text-gray-600 mt-1">{s.observation}</p>
              </div>
            ))}
          </div>
        </div>
      )}

      <div>
        <p className="text-sm font-medium mb-2">Ticket Details</p>
        <div className="bg-gray-50 rounded-lg p-3 text-sm space-y-1">
          <p><span className="font-medium">Subject:</span> {ticket.subject}</p>
          <p><span className="font-medium">Intent:</span> {ticket.intent ?? '—'}</p>
          <p><span className="font-medium">Urgency:</span> {ticket.urgency ?? '—'}</p>
          <p><span className="font-medium">Category:</span> {ticket.category ?? '—'}</p>
        </div>
      </div>
    </div>
  )
}
