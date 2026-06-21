import { useState, useEffect, useCallback } from 'react'
import { ticketsApi } from '../api/tickets'
import type { Ticket } from '../types'

export function useTickets() {
  const [tickets, setTickets] = useState<Ticket[]>([])
  const [loading, setLoading] = useState(false)

  const refresh = useCallback(async () => {
    setLoading(true)
    try {
      const data = await ticketsApi.list()
      setTickets(data)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => { refresh() }, [refresh])

  const createTicket = useCallback(async (payload: { customer_id: string; subject: string; body: string }) => {
    const ticket = await ticketsApi.create(payload)
    setTickets(prev => [ticket, ...prev])
    return ticket
  }, [])

  return { tickets, loading, refresh, createTicket }
}
