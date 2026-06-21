type View = 'inbox' | 'trace' | 'crm' | 'escalation' | 'metrics' | 'settings'

interface Props { active: View; onNavigate: (v: View) => void }

const nav: { id: View; label: string; icon: string }[] = [
  { id: 'inbox', label: 'Ticket Inbox', icon: '📥' },
  { id: 'trace', label: 'Agent Trace', icon: '🤖' },
  { id: 'crm', label: 'CRM Console', icon: '👤' },
  { id: 'escalation', label: 'Escalation Queue', icon: '🚨' },
  { id: 'metrics', label: 'Metrics', icon: '📊' },
  { id: 'settings', label: 'Settings', icon: '⚙️' },
]

export function Sidebar({ active, onNavigate }: Props) {
  return (
    <aside className="w-56 shrink-0 bg-white border-r border-gray-200 flex flex-col">
      <div className="px-5 py-4 border-b border-gray-100">
        <p className="font-bold text-indigo-600 text-sm">SupportAI</p>
        <p className="text-xs text-gray-400">Multi-Agent System</p>
      </div>
      <nav className="flex-1 p-3 space-y-1">
        {nav.map(item => (
          <button
            key={item.id}
            onClick={() => onNavigate(item.id)}
            className={`w-full text-left flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors ${active === item.id ? 'bg-indigo-50 text-indigo-600 font-medium' : 'text-gray-600 hover:bg-gray-50'}`}
          >
            <span>{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>
    </aside>
  )
}
