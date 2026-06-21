import { useState } from 'react'
import { Sidebar } from './components/Layout/Sidebar'
import { Header } from './components/Layout/Header'
import { TicketInbox } from './components/TicketInbox/TicketInbox'
import { TraceViewer } from './components/AgentTrace/TraceViewer'
import { CRMConsole } from './components/CRMConsole/CRMConsole'
import { EscalationQueue } from './components/EscalationQueue/EscalationQueue'
import { MetricsDashboard } from './components/Metrics/MetricsDashboard'
import { SettingsPanel } from './components/Settings/SettingsPanel'
import { useTrace } from './hooks/useTrace'
import { ticketsApi } from './api/tickets'
import type { Ticket } from './types'

type View = 'inbox' | 'trace' | 'crm' | 'escalation' | 'metrics' | 'settings'

const viewTitles: Record<View, string> = {
  inbox: 'Ticket Inbox',
  trace: 'Agent Trace',
  crm: 'CRM Console',
  escalation: 'Escalation Queue',
  metrics: 'Metrics Dashboard',
  settings: 'Settings',
}

export default function App() {
  const [view, setView] = useState<View>('inbox')
  const [selectedTicket, setSelectedTicket] = useState<Ticket | null>(null)
  const { result } = useTrace()

  const handleSelectTicket = async (id: string) => {
    const ticket = await ticketsApi.get(id)
    setSelectedTicket(ticket)
    setView('trace')
  }

  const apiKey = sessionStorage.getItem('openrouter_key') ?? ''
  const model = sessionStorage.getItem('openrouter_model') ?? ''

  return (
    <div className="flex h-screen overflow-hidden">
      <Sidebar active={view} onNavigate={setView} />
      <div className="flex-1 flex flex-col overflow-hidden">
        <Header title={viewTitles[view]} />
        <main className="flex-1 overflow-y-auto p-6">
          {view === 'inbox' && <TicketInbox selectedId={selectedTicket?.id ?? null} onSelect={handleSelectTicket} />}
          {view === 'trace' && <TraceViewer ticketId={selectedTicket?.id ?? null} apiKey={apiKey} model={model} />}
          {view === 'crm' && <CRMConsole ticket={selectedTicket} result={result} />}
          {view === 'escalation' && <EscalationQueue />}
          {view === 'metrics' && <MetricsDashboard />}
          {view === 'settings' && <SettingsPanel />}
        </main>
      </div>
    </div>
  )
}
