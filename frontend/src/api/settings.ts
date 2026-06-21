import { apiClient } from './client'
import type { Model } from '../types'

export const settingsApi = {
  validateKey: (key: string) =>
    apiClient.post<{ valid: boolean }>('/settings/validate-key', { key }).then(r => r.data),
  listModels: (key: string) =>
    apiClient.get<{ models: Model[] }>(`/settings/models?key=${encodeURIComponent(key)}`).then(r => r.data.models),
}
