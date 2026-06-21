import { apiClient } from './client'
import type { Ticket, ResolveResult } from '../types'

export const ticketsApi = {
  list: () => apiClient.get<Ticket[]>('/tickets/').then(r => r.data),
  get: (id: string) => apiClient.get<Ticket>(`/tickets/${id}`).then(r => r.data),
  create: (payload: { customer_id: string; subject: string; body: string }) =>
    apiClient.post<Ticket>('/tickets/', payload).then(r => r.data),
  resolve: (id: string, key: string, model: string) =>
    apiClient.post<ResolveResult>(`/tickets/${id}/resolve`, {
      openrouter_key: key,
      model,
    }).then(r => r.data),
}
