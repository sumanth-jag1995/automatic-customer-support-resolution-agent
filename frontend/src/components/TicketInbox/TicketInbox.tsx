import { useTickets } from '../../hooks/useTickets'
import { TicketForm } from './TicketForm'
import { TicketList } from './TicketList'

interface Props { selectedId: string | null; onSelect: (id: string) => void }

export function TicketInbox({ selectedId, onSelect }: Props) {
  const { tickets, loading, createTicket } = useTickets()

  return (
    <div className="flex flex-col gap-4">
      <TicketForm onSubmit={async (data) => {
        const t = await createTicket(data)
        onSelect(t.id)
      }} />
      {loading ? <p className="text-sm text-gray-400 text-center">Loading…</p> : (
        <TicketList tickets={tickets} selectedId={selectedId} onSelect={onSelect} />
      )}
    </div>
  )
}
