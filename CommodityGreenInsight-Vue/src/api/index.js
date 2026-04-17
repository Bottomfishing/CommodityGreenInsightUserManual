/**
 * 大宗绿测前端 API 封装
 * 后端地址：http://127.0.0.1:8000
 * 本地代理：/api -> 后端（vite.config.js 中配置）
 */

const BASE = '/api'

// ── 认证 Token ──────────────────────────────
export function getToken() {
  return localStorage.getItem('token') || null
}

export function setToken(token) {
  localStorage.setItem('token', token)
}

export function clearToken() {
  localStorage.removeItem('token')
}

function authHeaders() {
  const token = getToken()
  return token ? { 'Authorization': `Bearer ${token}` } : {}
}

// ── 基础请求 ──────────────────────────────
async function request(method, path, body, isFormData = false, params = null) {
  let url = BASE + path
  if (params) {
    const qs = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== undefined && v !== null)
    ).toString()
    if (qs) url += '?' + qs
  }

  const opts = {
    method,
    headers: {
      ...authHeaders(),
    },
  }
  if (body) {
    if (isFormData) {
      opts.body = body
    } else {
      opts.headers['Content-Type'] = 'application/json'
      opts.body = JSON.stringify(body)
    }
  }

  const res = await fetch(url, opts)
  if (!res.ok) {
    const txt = await res.text().catch(() => '')
    throw new Error(`HTTP ${res.status}: ${txt}`)
  }
  const ct = res.headers.get('content-type') || ''
  if (ct.includes('application/json')) return res.json()
  return res.text()
}

// ──────────────────────────────────────────
// 认证
// ──────────────────────────────────────────

/** POST /api/auth/register */
export async function register({ username, password }) {
  return request('POST', '/auth/register', { username, password })
}

/** POST /api/auth/login */
export async function login({ username, password }) {
  const data = await request('POST', '/auth/login', { username, password })
  const token = data?.access_token || data?.token || null
  if (token) {
    setToken(token)
  }
  return data
}

/** GET /api/auth/me */
export async function fetchMe() {
  return request('GET', '/auth/me')
}

/** 登出 */
export function logout() {
  clearToken()
}

// ──────────────────────────────────────────
// 系统状态
// ──────────────────────────────────────────

/** GET /api/system/status */
export async function fetchSystemStatus() {
  const raw = await request('GET', '/api/system/status')
  const lock = raw?.global_lock || null
  return {
    ...raw,
    // 后端当前返回 global_lock.run_id，这里统一成前端已使用的 current_run_id
    current_run_id: raw?.current_run_id || lock?.run_id || raw?.latest_run_id || null,
    started_at: raw?.started_at || lock?.started_at || null,
    // 兜底：如果 lock 存在则视为运行中（兼容不同后端字段）
    global_busy: typeof raw?.global_busy === 'boolean' ? raw.global_busy : !!lock,
  }
}

// ──────────────────────────────────────────
// 油价训练 Run
// ──────────────────────────────────────────

/** GET /api/oil/runs */
export async function fetchRunList() {
  return request('GET', '/oil/runs')
}

/**
 * POST /api/oil/runs
 * FormData: zip_file(必填), top_n, epochs, forecast_steps,
 *            cutoff_date, enable_early_stopping, auto_bond_after_oil
 */
export async function createOilRun(formData) {
  return request('POST', '/oil/runs', formData, true)
}

/** GET /api/oil/runs/{run_id} */
export async function fetchOilRun(runId) {
  return request('GET', `/oil/runs/${runId}`)
}

/** POST /api/oil/runs/{run_id}/stop */
export async function stopOilRun(runId) {
  return request('POST', `/oil/runs/${runId}/stop`)
}

// ──────────────────────────────────────────
// 训练监控
// ──────────────────────────────────────────

/**
 * GET /api/oil/monitor/resolve
 * mode: running | active_by_log | selected | latest | manual
 */
export async function resolveMonitor({ mode = 'latest', selected_run_id = null, manual_dir = null } = {}) {
  return request('GET', '/oil/monitor/resolve', null, false, { mode, selected_run_id, manual_dir })
}

/** GET /api/oil/runs/{run_id}/training-dashboard?rows=2000 */
export async function fetchTrainingDashboard(runId, rows = 2000) {
  return request('GET', `/oil/runs/${runId}/training-dashboard`, null, false, { rows })
}

/** GET /api/oil/runs/{run_id}/log?lines=200 */
export async function fetchRunLog(runId, lines = 200) {
  return request('GET', `/oil/runs/${runId}/log`, null, false, { lines })
}

/** GET /api/oil/runs/{run_id}/prediction-preview?rows=30 */
export async function fetchPredictionPreview(runId, rows = 30) {
  return request('GET', `/oil/runs/${runId}/prediction-preview`, null, false, { rows })
}

/** GET /api/oil/runs/{run_id}/csv-preview?name=xxx&rows=50 */
export async function fetchCsvPreview(runId, name, rows = 50) {
  return request('GET', `/oil/runs/${runId}/csv-preview`, null, false, { name, rows })
}

// ──────────────────────────────────────────
// 结果分析
// ──────────────────────────────────────────

/** GET /api/oil/runs/{run_id}/overview */
export async function fetchOverview(runId) {
  return request('GET', `/oil/runs/${runId}/overview`)
}

/** GET /api/oil/runs/{run_id}/analytics */
export async function fetchAnalytics(runId) {
  return request('GET', `/oil/runs/${runId}/analytics`)
}

/** POST /api/oil/runs/{run_id}/ai-report?force=false */
export async function generateAIReport(runId, force = false) {
  return request('POST', `/oil/runs/${runId}/ai-report`, null, false, { force })
}

// ──────────────────────────────────────────
// 新能源预测
// ──────────────────────────────────────────

/**
 * POST /api/oil/runs/{run_id}/new-energy
 * FormData: ne_zip_file(必填), series, conf_level, scale_oil_return, make_viz, rebuild_returns
 */
export async function startNewEnergy(runId, formData) {
  return request('POST', `/oil/runs/${runId}/new-energy`, formData, true)
}

/** GET /api/oil/runs/{run_id}/new-energy/latest?rows=50 */
export async function fetchNewEnergyLatest(runId, rows = 50) {
  return request('GET', `/oil/runs/${runId}/new-energy/latest`, null, false, { rows })
}

// ──────────────────────────────────────────
// 绿债预测
// ──────────────────────────────────────────

/** POST /api/oil/runs/{run_id}/bond (FormData, bond_zip_file 可选) */
export async function startBond(runId, formData) {
  return request('POST', `/oil/runs/${runId}/bond`, formData, true)
}

/** GET /api/oil/runs/{run_id}/bond/latest?rows=50 */
export async function fetchBondLatest(runId, rows = 50) {
  return request('GET', `/oil/runs/${runId}/bond/latest`, null, false, { rows })
}

// ──────────────────────────────────────────
// 文件下载
// ──────────────────────────────────────────

/** GET /api/oil/runs/{run_id}/files */
export async function fetchFiles(runId) {
  return request('GET', `/oil/runs/${runId}/files`)
}

/**
 * 单文件下载 URL
 * GET /api/oil/runs/{run_id}/download?name=xxx
 */
export function getFileDownloadUrl(runId, name) {
  return `${BASE}/oil/runs/${runId}/download?name=${encodeURIComponent(name)}`
}

export const fetchDownloadUrl = getFileDownloadUrl

/**
 * 整包 zip 下载 URL
 * GET /api/oil/runs/{run_id}/export.zip
 */
export function getZipExportUrl(runId) {
  return `${BASE}/oil/runs/${runId}/export.zip`
}

// ──────────────────────────────────────────
// AI 问答
// ──────────────────────────────────────────

/**
 * POST /api/ai/chat?mode=oil|new_energy&prompt=xxx&run_id=xxx
 * 需要登录认证
 */
export async function sendAIChat({ mode = 'oil', prompt, run_id }) {
  const params = { mode, prompt }
  if (run_id) params.run_id = run_id
  return request('POST', '/ai/chat', null, false, params)
}
