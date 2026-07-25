import axios, { AxiosError } from 'axios'

export interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 20000,
})

apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const original = error.config || {}
    if (error.response?.status === 401 && !original._retry) {
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          original._retry = true
          const response = await axios.post<ApiResponse<{
            access_token: string
            refresh_token: string
            username: string
            role: string
          }>>('/api/v1/auth/refresh', { refresh_token: refreshToken })
          const data = response.data.data
          localStorage.setItem('access_token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          localStorage.setItem('username', data.username)
          localStorage.setItem('role', data.role)
          original.headers = original.headers || {}
          original.headers.Authorization = `Bearer ${data.access_token}`
          return apiClient(original)
        } catch {
          clearSession()
        }
      } else {
        clearSession()
      }
    }
    return Promise.reject(normalizeApiError(error))
  },
)

function clearSession() {
  localStorage.removeItem('access_token')
  localStorage.removeItem('refresh_token')
  localStorage.removeItem('username')
  localStorage.removeItem('role')
  if (window.location.pathname !== '/login') {
    window.location.assign('/login')
  }
}

export async function unwrap<T>(promise: Promise<{ data: ApiResponse<T> }>): Promise<T> {
  const response = await promise.catch((error) => {
    throw normalizeApiError(error)
  })
  if (response.data.code !== 0) {
    throw new Error(response.data.message || '请求失败')
  }
  return response.data.data
}

function normalizeApiError(error: unknown) {
  if (!(error instanceof AxiosError)) {
    return error instanceof Error ? error : new Error('请求失败，请稍后再试')
  }

  const status = error.response?.status
  const payload = error.response?.data as { detail?: unknown; message?: string } | undefined
  const detail = payload?.detail
  if (typeof payload?.message === 'string' && payload.message) {
    return new Error(payload.message)
  }
  if (typeof detail === 'string' && detail) {
    return new Error(detail)
  }
  if (Array.isArray(detail) && detail.length) {
    return new Error(detail.map(formatValidationDetail).filter(Boolean).join('；') || '请求参数不正确')
  }
  if (status === 401) {
    return new Error('用户名或密码错误，或登录已过期')
  }
  if (status === 422) {
    return new Error('请求参数不正确，请检查输入内容')
  }
  if (status === 423) {
    return new Error('登录失败次数过多，请稍后再试')
  }
  return new Error(error.message || '请求失败，请稍后再试')
}

function formatValidationDetail(item: unknown) {
  if (!item || typeof item !== 'object') return ''
  const detail = item as { loc?: unknown[]; msg?: string }
  const field = Array.isArray(detail.loc) ? String(detail.loc[detail.loc.length - 1] || '') : ''
  const fieldName = FIELD_LABELS[field] || field || '字段'
  const message = detail.msg || '格式不正确'
  return `${fieldName}${translateValidationMessage(message)}`
}

const FIELD_LABELS: Record<string, string> = {
  username: '用户名',
  email: '邮箱',
  password: '密码',
  role: '角色',
  refresh_token: '刷新令牌',
}

function translateValidationMessage(message: string) {
  if (message.includes('String should have at least')) return '长度不足'
  if (message.includes('String should have at most')) return '长度过长'
  if (message.includes('Value error')) return `：${message.replace(/^Value error,\s*/, '')}`
  return `：${message}`
}
