import { clearToken, getToken, login as authLogin, register as authRegister, fetchMe } from './auth'

const BASE = '/api'

type QueryValue = string | number | boolean | null | undefined

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

function buildUrl(path: string, params?: Record<string, QueryValue>): string {
  let url = BASE + path
  if (!params) return url

  const qs = new URLSearchParams()
  Object.entries(params).forEach(([key, value]) => {
    if (value !== undefined && value !== null) qs.append(key, String(value))
  })
  const query = qs.toString()
  if (query) url += `${url.includes('?') ? '&' : '?'}${query}`
  return url
}

async function request<T = any>(
  method: string,
  path: string,
  body?: unknown,
  isFormData = false,
  params?: Record<string, QueryValue>,
): Promise<T> {
  const url = buildUrl(path, params)
  const opts: RequestInit & { headers: Record<string, string> } = {
    method,
    headers: {
      ...authHeaders(),
    },
  }

  if (body !== undefined && body !== null) {
    if (isFormData) {
      opts.body = body as BodyInit
    } else {
      opts.headers['Content-Type'] = 'application/json'
      opts.body = JSON.stringify(body)
    }
  }

  const res = await fetch(url, opts)
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    if (res.status === 401) handleUnauthorized()
    throw new Error(`HTTP ${res.status}: ${txt}`)
  }

  const contentType = res.headers.get('content-type') || ''
  if (contentType.includes('application/json')) return res.json()
  return (await res.text()) as T
}

async function requestBlob(path: string, params?: Record<string, QueryValue>): Promise<Blob> {
  const url = buildUrl(path, params)
  const res = await fetch(url, { headers: { ...authHeaders() } })
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    if (res.status === 401) handleUnauthorized()
    throw new Error(`HTTP ${res.status}: ${txt}`)
  }
  return res.blob()
}

export async function login(payload: { username: string; password: string }) {
  return authLogin(payload.username, payload.password)
}

export async function register(payload: { username: string; password: string }) {
  return authRegister(payload.username, payload.password)
}

export { fetchMe }

export function logout(): void {
  clearToken()
}

export async function fetchSystemStatus() {
  const raw = await request<any>('GET', '/system/status')
  const lock = raw?.global_lock || null
  return {
    ...raw,
    current_run_id: raw?.current_run_id || lock?.run_id || raw?.latest_run_id || null,
    started_at: raw?.started_at || lock?.started_at || null,
    global_busy: typeof raw?.global_busy === 'boolean' ? raw.global_busy : !!lock,
  }
}

export async function fetchWtiLast20Candles() {
  return request<any>('GET', '/market/wti-last20-candles')
}

export async function fetchWtiSpotLast20() {
  return request<any>('GET', '/market/wti-spot-last20')
}

export async function fetchGlobalGasolinePrices() {
  return request<any>('GET', '/market/global-gasoline-prices')
}

export async function fetchLiveWtiPredict(params?: { run_id?: string; weights_name?: string }) {
  return request<any>('GET', '/live/wti/predict', undefined, false, {
    run_id: params?.run_id,
    weights_name: params?.weights_name,
  })
}

export async function fetchLiveWtiPredictAdvanced(formData: FormData) {
  return request<any>('POST', '/live/wti/predict/advanced', formData, true)
}

export async function fetchRunList() {
  const res = await request<any>('GET', '/oil/runs')
  if (Array.isArray(res)) return res
  return res?.items || []
}

export async function createOilRun(formData: FormData) {
  return request('POST', '/oil/runs', formData, true)
}

export async function fetchOilRun(runId: string) {
  return request('GET', `/oil/runs/${runId}`)
}

export async function stopOilRun(runId: string) {
  return request('POST', `/oil/runs/${runId}/stop`)
}

export async function resolveMonitor({
  mode = 'latest',
  selected_run_id = null,
  manual_dir = null,
}: {
  mode?: 'default' | 'running' | 'active_by_log' | 'selected' | 'latest' | 'manual'
  selected_run_id?: string | null
  manual_dir?: string | null
} = {}) {
  return request('GET', '/oil/monitor/resolve', undefined, false, { mode, selected_run_id, manual_dir })
}

export async function fetchTrainingDashboard(runId: string, rows = 2000) {
  return request('GET', `/oil/runs/${runId}/training-dashboard`, undefined, false, { rows })
}

export async function fetchRunLog(runId: string, lines = 200) {
  return request('GET', `/oil/runs/${runId}/log`, undefined, false, { lines })
}

export async function fetchPredictionPreview(runId: string, rows = 30) {
  return request('GET', `/oil/runs/${runId}/prediction-preview`, undefined, false, { rows })
}

export async function fetchCsvPreview(runId: string, name: string, rows = 50) {
  return request('GET', `/oil/runs/${runId}/csv-preview`, undefined, false, { name, rows })
}

export async function fetchOverview(runId: string) {
  return request('GET', `/oil/runs/${runId}/overview`)
}

export async function fetchAnalytics(runId: string) {
  return request('GET', `/oil/runs/${runId}/analytics`)
}

export async function fetchResultCharts(runId: string, rows = 5000) {
  return request('GET', `/oil/runs/${runId}/result-charts`, undefined, false, { rows })
}

export async function fetchDefaultResultCharts(rows = 5000) {
  return request('GET', '/oil/result-charts/default', undefined, false, { rows })
}

export async function generateAIReport(runId: string, force = false) {
  return request('POST', `/oil/runs/${runId}/ai-report`, undefined, false, { force })
}

export async function startNewEnergy(runId: string, formData: FormData) {
  return request('POST', `/oil/runs/${runId}/new-energy`, formData, true)
}

export async function fetchNewEnergyLatest(runId: string, rows = 50) {
  return request('GET', `/oil/runs/${runId}/new-energy/latest`, undefined, false, { rows })
}

export async function startBond(runId: string, formData: FormData) {
  return request('POST', `/oil/runs/${runId}/bond`, formData, true)
}

export async function fetchBondLatest(runId: string, rows = 50) {
  return request('GET', `/oil/runs/${runId}/bond/latest`, undefined, false, { rows })
}

export async function fetchFiles(runId: string) {
  return request('GET', `/oil/runs/${runId}/files`)
}

export function getFileDownloadUrl(runId: string, name: string) {
  return `${BASE}/oil/runs/${runId}/download?name=${encodeURIComponent(name)}`
}

export const fetchDownloadUrl = getFileDownloadUrl

export function getZipExportUrl(runId: string) {
  return `${BASE}/oil/runs/${runId}/export.zip`
}

export async function downloadOilRunFile(runId: string, name: string): Promise<void> {
  const blob = await requestBlob(`/oil/runs/${runId}/download`, { name })
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = name
  document.body.appendChild(a)
  a.click()
  a.remove()
  setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export async function getOilRunFileObjectUrl(runId: string, name: string): Promise<string> {
  const blob = await requestBlob(`/oil/runs/${runId}/download`, { name })
  return URL.createObjectURL(blob)
}

export async function fetchStaticResultFiles() {
  return request('GET', '/static-results/files')
}

export async function getStaticResultImageObjectUrl(name: string): Promise<string> {
  const blob = await requestBlob('/static-results/image', { name })
  return URL.createObjectURL(blob)
}

export async function sendAIChat({
  mode = 'oil',
  prompt,
  run_id,
}: {
  mode?: 'oil' | 'new_energy'
  prompt: string
  run_id?: string
}) {
  const params: Record<string, QueryValue> = { mode, prompt }
  if (run_id) params.run_id = run_id
  return request('POST', '/ai/chat', undefined, false, params)
}
