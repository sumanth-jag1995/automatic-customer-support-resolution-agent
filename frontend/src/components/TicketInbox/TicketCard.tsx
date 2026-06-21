import type { Ticket } from '../../types'

const urgencyColors: Record<string, string> = {
  low: 'bg-green-100 text-green-700',
  medium: 'bg-yellow-100 text-yellow-700',
  high: 'bg-orange-100 text-orange-700',
  critical: 'bg-red-100 text-red-700',
}

const statusColors: Record<string, string> = {
  new: 'bg-blue-100 text-blue-700',
  in_progress: 'bg-purple-100 text-purple-700',
  resolved: 'bg-green-100 text-green-700',
  escalated: 'bg-red-100 text-red-700',
}

interface Props { ticket: Ticket; onClick: () => void; selected: boolean }

export function TicketCard({ ticket, onClick, selected }: Props) {
  return (
    <div
      onClick={onClick}
      className={`cursor-pointer rounded-lg border p-4 transition-colors ${selected ? 'border-indigo-600 bg-indigo-50' : 'border-gray-200 bg-white hover:bg-gray-50'}`}
    >
      <div className="flex items-start justify-between gap-2">
        <p className="font-medium text-sm truncate">{ticket.subject}</p>
        <span className={`shrink-0 text-xs px-2 py-0.5 rounded-full font-medium ${statusColors[ticket.status]}`}>
          {ticket.status.replace('_', ' ')}
        </span>
      </div>
      <p className="text-xs text-gray-500 mt-1 line-clamp-2">{ticket.body}</p>
      <div className="flex gap-2 mt-2">
        {ticket.urgency && (
          <span className={`text-xs px-2 py-0.5 rounded-full ${urgencyColors[ticket.urgency]}`}>{ticket.urgency}</span>
        )}
        {ticket.intent && (
          <span className="text-xs px-2 py-0.5 rounded-full bg-gray-100 text-gray-600">{ticket.intent}</span>
        )}
      </div>
    </div>
  )
}
