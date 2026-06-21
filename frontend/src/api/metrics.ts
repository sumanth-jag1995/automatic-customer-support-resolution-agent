import { apiClient } from './client'
import type { Metrics } from '../types'

export const metricsApi = {
  get: () => apiClient.get<Metrics>('/metrics/').then(r => r.data),
}
