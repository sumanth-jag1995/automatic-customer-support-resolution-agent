import { useState, useCallback } from 'react'
import { settingsApi } from '../api/settings'
import type { Model } from '../types'

export function useSettings() {
  const [key, setKey] = useState(() => sessionStorage.getItem('openrouter_key') ?? '')
  const [model, setModel] = useState(() => sessionStorage.getItem('openrouter_model') ?? '')
  const [models, setModels] = useState<Model[]>([])
  const [keyValid, setKeyValid] = useState<boolean | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const saveKey = useCallback((k: string) => {
    setKey(k)
    sessionStorage.setItem('openrouter_key', k)
    setKeyValid(null)
  }, [])

  const saveModel = useCallback((m: string) => {
    setModel(m)
    sessionStorage.setItem('openrouter_model', m)
  }, [])

  const validate = useCallback(async () => {
    setLoading(true)
    setError('')
    try {
      const result = await settingsApi.validateKey(key)
      setKeyValid(result.valid)
      const modelList = await settingsApi.listModels(key)
      setModels(modelList)
    } catch {
      setKeyValid(false)
      setError('Invalid key or network error')
    } finally {
      setLoading(false)
    }
  }, [key])

  return { key, saveKey, model, saveModel, models, keyValid, loading, error, validate }
}
