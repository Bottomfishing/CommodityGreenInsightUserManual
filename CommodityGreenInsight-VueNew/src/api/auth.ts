/**
 * 大宗绿测 - API 认证模块
 * 后端地址：http://127.0.0.1:8000
 */

const BASE = '/api'

// ── Token 管理 ──
export function getToken(): string | null {
  return localStorage.getItem('token') || null
}

export function setToken(token: string): void {
  localStorage.setItem('token', token)
}

export function clearToken(): void {
  localStorage.removeItem('token')
  localStorage.removeItem('username')
}

function handleUnauthorized(): void {
  clearToken()
  if (typeof window !== 'undefined' && window.location.pathname !== '/') {
    window.location.href = '/'
  }
}

function authHeaders(): Record<string, string> {
  const token = getToken()
  return token ? { Authorization: `Bearer ${token}` } : {}
}

// ── 基础请求 ──
async function request<T = any>(
  method: string,
  path: string,
  body?: any,
): Promise<T> {
  const url = BASE + path
  const opts: RequestInit & { headers?: Record<string, string> } = {
    method,
    headers: {
      ...authHeaders(),
    },
  }
  if (body) {
    opts.headers!['Content-Type'] = 'application/json'
    opts.body = JSON.stringify(body)
  }

  const res = await fetch(url, opts)
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    if (res.status === 401) handleUnauthorized()
    throw new Error(`HTTP ${res.status}: ${txt}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text() as unknown as T
}

// ── 认证 API ──

/** POST /api/auth/login */
export async function login(username: string, password: string): Promise<any> {
  const data = await request<{ access_token?: string; token?: string }>(
    'POST',
    '/auth/login',
    { username, password },
  )
  const token = data?.access_token || data?.token || null
  if (token) setToken(token)
  return data
}

/** POST /api/auth/register */
export async function register(username: string, password: string): Promise<any> {
  return request('POST', '/auth/register', { username, password })
}

/** GET /api/auth/me */
export async function fetchMe(): Promise<{ username?: string }> {
  return request('GET', '/auth/me')
}
