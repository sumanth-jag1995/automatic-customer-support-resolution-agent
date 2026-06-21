import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export const apiClient = axios.create({ baseURL: BASE_URL })

apiClient.interceptors.request.use((config) => {
  const key = sessionStorage.getItem('openrouter_key')
  if (key) config.headers['X-OpenRouter-Key'] = key
  return config
})
