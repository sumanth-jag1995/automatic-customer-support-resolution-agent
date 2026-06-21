export interface Ticket {
  id: string
  customer_id: string
  subject: string
  body: string
  intent: string | null
  urgency: 'low' | 'medium' | 'high' | 'critical' | null
  category: string | null
  status: 'new' | 'in_progress' | 'resolved' | 'escalated'
  confidence: number | null
  created_at: string
  resolved_at: string | null
}

export interface TraceStep {
  step: string
  thought: string
  action: string | null
  tool: string | null
  observation: string | null
  confidence: number | null
}

export interface ResolveResult {
  ticket_id: string
  status: string
  confidence: number
  escalated: boolean
  escalation_summary: string | null
  trace: TraceStep[]
}

export interface Model {
  id: string
  name: string
}

export interface Metrics {
  total: number
  resolved: number
  escalated: number
  in_progress: number
  auto_resolution_rate: number
  escalation_rate: number
  avg_confidence: number
}

export interface Customer {
  id: string
  name: string
  email: string
  plan: string
  status: string
}

export interface Order {
  id: string
  customer_id: string
  product: string
  amount: number
  status: string
}
