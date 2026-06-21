import { useState, useCallback } from 'react'
import { ticketsApi } from '../api/tickets'
import type { ResolveResult } from '../types'

export function useTrace() {
  const [result, setResult] = useState<ResolveResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const run = useCallback(async (ticketId: string, key: string, model: string) => {
    setLoading(true)
    setError('')
    setResult(null)
    try {
      const data = await ticketsApi.resolve(ticketId, key, model)
      setResult(data)
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Unknown error'
      setError(msg)
    } finally {
      setLoading(false)
    }
  }, [])

  return { result, loading, error, run }
}
