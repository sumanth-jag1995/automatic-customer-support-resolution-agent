import { TicketCard } from './TicketCard'
import type { Ticket } from '../../types'

interface Props { tickets: Ticket[]; selectedId: string | null; onSelect: (id: string) => void }

export function TicketList({ tickets, selectedId, onSelect }: Props) {
  if (tickets.length === 0) return <p className="text-sm text-gray-400 text-center py-8">No tickets yet.</p>
  return (
    <div className="space-y-2">
      {tickets.map(t => (
        <TicketCard key={t.id} ticket={t} selected={t.id === selectedId} onClick={() => onSelect(t.id)} />
      ))}
    </div>
  )
}
