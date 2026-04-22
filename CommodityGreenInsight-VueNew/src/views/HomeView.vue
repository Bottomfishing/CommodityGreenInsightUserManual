<template>
  <div class="home-page">
    <!-- ══════════════════════════════════════════════════
         顶部贯穿导航栏
         ══════════════════════════════════════════════════ -->
    <header class="top-nav">
      <!-- 左侧品牌 -->
      <div class="nav-brand">
        <div class="brand-icon">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <span class="brand-name">大宗绿测</span>
        <span class="brand-sep">|</span>
        <span class="brand-sub">绿色金融智能分析平台</span>
      </div>

      <!-- 中间状态指标 -->
      <div class="nav-stats">
        <div class="stat-item">
          <span class="stat-dot stat-dot--green"></span>
          <span class="stat-label">当前状态</span>
          <span class="stat-val">运行中</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <svg class="stat-icon" width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z" />
          </svg>
          <span class="stat-label">当前目录</span>
          <span class="stat-val stat-val--mono">/home/dashboard</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <svg class="stat-icon" width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span class="stat-label">启动时间</span>
          <span class="stat-val stat-val--mono">{{ uptime }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-dot stat-dot--blue"></span>
          <span class="stat-label">运行测试</span>
          <span class="stat-val stat-val--success">PASSED</span>
        </div>
      </div>

      <!-- 右侧搜索 + 用户 -->
      <div class="nav-right">
        <div class="search-box" :class="{ focused: searchFocused }">
          <svg class="search-icon" width="15" height="15" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <circle cx="11" cy="11" r="8" />
            <line x1="21" y1="21" x2="16.65" y2="16.65" />
          </svg>
          <input
            v-model="searchQuery"
            type="text"
            placeholder="搜索功能、数据、报告..."
            @focus="searchFocused = true"
            @blur="searchFocused = false"
          />
          <kbd class="search-kbd">⌘K</kbd>
        </div>

        <div class="nav-user" @click="handleLogout" title="退出登录">
          <div class="user-avatar">
            {{ username.charAt(0).toUpperCase() }}
          </div>
          <span class="user-name">{{ username }}</span>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor"
            stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4" />
            <polyline points="16 17 21 12 16 7" />
            <line x1="21" y1="12" x2="9" y2="12" />
          </svg>
        </div>
      </div>
    </header>

    <!-- ══════════════════════════════════════════════════
         主内容区域
         ══════════════════════════════════════════════════ -->
    <main class="main-content">
      <!-- 顶部装饰线 -->
      <dv-decoration-5 style="width:100%;height:3px;margin-bottom:4px;" />

      <!-- 核心指标行 -->
      <div class="kpi-row">
        <div class="kpi-card kpi--oil">
          <dv-border-box-8 style="width:100%;height:100%;">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">Brent Crude</span>
                <span class="kpi-live"><i class="live-dot"></i> LIVE</span>
              </div>
              <div class="kpi-price">$78.42</div>
              <div class="kpi-change kpi-change--up">+2.34%</div>
              <div class="kpi-sub">Vol: 2.4M · $76.8 - $79.2</div>
            </div>
          </dv-border-box-8>
        </div>

        <div class="kpi-card kpi--energy">
          <dv-border-box-8 style="width:100%;height:100%;">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">CSI 新能源</span>
                <span class="kpi-badge kpi-badge--up">+1.4%</span>
              </div>
              <div class="kpi-price">3,847</div>
              <div class="kpi-change kpi-change--up">+1.82%</div>
              <div class="kpi-sub">光伏 4,126 · 新能源车 2,934</div>
            </div>
          </dv-border-box-8>
        </div>

        <div class="kpi-card kpi--bond">
          <dv-border-box-8 style="width:100%;height:100%;">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">10Y 国债</span>
                <span class="kpi-badge kpi-badge--stable">Stable</span>
              </div>
              <div class="kpi-price">2.34%</div>
              <div class="kpi-change kpi-change--down">-2bp</div>
              <div class="kpi-sub">SHIBOR 1.68% · LPR 3.45%</div>
            </div>
          </dv-border-box-8>
        </div>

        <div class="kpi-card kpi--ai">
          <dv-border-box-8 style="width:100%;height:100%;">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">AI 洞察</span>
                <span class="kpi-live"><i class="live-dot live-dot--green"></i> Active</span>
              </div>
              <div class="kpi-price">94.7%</div>
              <div class="kpi-change kpi-change--ai">GRU+LSTM</div>
              <div class="kpi-sub">Bullish Brent · Hold Green Bond</div>
            </div>
          </dv-border-box-8>
        </div>
      </div>

      <!-- 主内容区域（图表占位 + 右侧数据面板） -->
      <div class="mid-row">
        <!-- 左侧：待添加内容占位 -->
        <div class="panel panel--chart">
          <dv-border-box-1 style="width:100%;height:100%;">
            <div class="panel-inner placeholder-zone">
              <div class="placeholder-hint">
                <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="currentColor"
                  stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="16" />
                  <line x1="8" y1="12" x2="16" y2="12" />
                </svg>
                <span>待添加内容</span>
              </div>
            </div>
          </dv-border-box-1>
        </div>

        <!-- 右：数据列表 -->
        <div class="panel panel--data">
          <dv-border-box-1 style="width:100%;height:100%;">
            <div class="panel-inner">
              <div class="panel-head">
                <div class="panel-title-row">
                  <span class="panel-tag">DATA</span>
                  <span class="panel-title">实时数据监控</span>
                </div>
              </div>
              <div class="data-table-area">
                <dv-scroll-board :config="scrollConfig" style="width:100%;height:100%;" />
              </div>
            </div>
          </dv-border-box-1>
        </div>
      </div>

      <!-- 底部装饰线 -->
      <dv-decoration-5 style="width:100%;height:3px;margin-top:8px;" />
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from 'vue'
import { useRouter } from 'vue-router'
import { clearToken } from '@/api/auth'

const router = useRouter()
const username = localStorage.getItem('username') || '用户'

// ===== 搜索 =====
const searchQuery = ref('')
const searchFocused = ref(false)

// ===== 时间 =====
const currentTime = ref('')
const startTime = ref(Date.now())
const uptime = computed(() => {
  const diff = Math.floor((Date.now() - startTime.value) / 1000)
  const h = Math.floor(diff / 3600)
  const m = Math.floor((diff % 3600) / 60)
  const s = diff % 60
  return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
})

let clockTimer: number
function updateClock() {
  const d = new Date()
  currentTime.value =
    String(d.getHours()).padStart(2, '0') + ':' +
    String(d.getMinutes()).padStart(2, '0') + ':' +
    String(d.getSeconds()).padStart(2, '0')
}

// ===== 滚动表格数据 =====
const scrollConfig = reactive({
  header: ['标的', '最新价', '涨跌幅', '成交量', '状态'],
  data: [
    ['Brent 原油', '$78.42', '+2.34%', '2.4M', '📈 买入'],
    ['WTI 原油', '$74.56', '+1.87%', '1.8M', '📈 买入'],
    ['CSI 新能源', '3,847', '+1.82%', '862亿', '📈 买入'],
    ['光伏产业', '4,126', '+0.95%', '423亿', '📊 持有'],
    ['新能源车', '2,934', '-0.42%', '312亿', '📉 观望'],
    ['10Y 国债', '2.34%', '-2bp', '1.2万亿', '📊 持有'],
    ['SHIBOR', '1.68%', '0bp', '-', '📊 持有'],
    ['LPR 1Y', '3.45%', '-5bp', '-', '📉 下降'],
  ],
  rowNum: 7,
  headerBGC: 'rgba(59,130,246,0.08)',
  oddRowBGC: 'transparent',
  evenRowBGC: 'rgba(255,255,255,0.015)',
  headerHeight: 36,
  rowHeight: 32,
  align: ['left', 'right', 'right', 'right', 'center'],
  headerFontSize: 12,
  fontSize: 12,
  color: 'rgba(148,163,184,0.7)',
})

// ===== 图表 =====
const chartCanvasRef = ref<HTMLCanvasElement | null>(null)
let chartAnimId: number | null = null
let chartProgress = 0
const OIL_DATA = {
  actual: [82.4, 79.8, 76.3, 72.1, 71.2, 74.5, 78.0, 81.6, 84.3, 82.1],
  predicted: [82.1, 80.4, 83.7, 85.9, 87.1, 87.3],
  wti: [78.2, 76.1, 73.8, 69.5, 68.7, 71.8, 75.3, 78.9, 81.5, 79.3, 77.6, 81.2, 83.4, 84.6, 84.9],
}

function drawMainChart() {
  const c = chartCanvasRef.value
  if (!c) return
  const ctx = c.getContext('2d')
  if (!ctx) return
  const dpr = window.devicePixelRatio || 1
  const W = 800, H = 360
  c.width = W * dpr
  c.height = H * dpr
  c.style.width = '100%'
  c.style.height = H + 'px'
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0)

  const allPrices = [...OIL_DATA.actual, ...OIL_DATA.predicted, ...OIL_DATA.wti]
  const minV = Math.min(...allPrices) - 4
  const maxV = Math.max(...allPrices) + 5
  const range = maxV - minV || 1
  const pad = { top: 28, right: 50, bottom: 32, left: 48 }
  const chartW = W - pad.left - pad.right
  const chartH = H - pad.top - pad.bottom
  const time = Date.now() / 1000
  ctx.clearRect(0, 0, W, H)

  // 扫描线
  const scanY = (time * 40) % H
  const scanGrad = ctx.createLinearGradient(0, scanY - 30, 0, scanY + 30)
  scanGrad.addColorStop(0, 'transparent')
  scanGrad.addColorStop(0.5, 'rgba(59,130,246,.025)')
  scanGrad.addColorStop(1, 'transparent')
  ctx.fillStyle = scanGrad
  ctx.fillRect(0, 0, W, H)

  // 网格
  for (let i = 0; i <= 5; i++) {
    const y = pad.top + (chartH / 5) * i
    ctx.beginPath()
    ctx.moveTo(pad.left, y)
    ctx.lineTo(W - pad.right, y)
    ctx.strokeStyle = i === 5 ? 'rgba(148,163,184,.10)' : 'rgba(148,163,184,.04)'
    ctx.lineWidth = i === 5 ? 0.7 : 0.4
    ctx.stroke()
    const priceVal = maxV - (i / 5) * range
    ctx.font = "10px 'SF Mono','Cascadia Code',monospace"
    ctx.fillStyle = 'rgba(148,163,184,.25)'
    ctx.textAlign = 'right'
    ctx.fillText(`$${priceVal.toFixed(0)}`, pad.left - 8, y + 3)
  }
  for (let i = 0; i <= 6; i++) {
    const x = pad.left + (chartW / 6) * i
    ctx.beginPath()
    ctx.moveTo(x, pad.top)
    ctx.lineTo(x, H - pad.bottom)
    ctx.strokeStyle = 'rgba(148,163,184,.025)'
    ctx.lineWidth = 0.4
    ctx.stroke()
  }

  const brentAll = [...OIL_DATA.actual, ...OIL_DATA.predicted]
  const wtiAll = OIL_DATA.wti
  const totalN = brentAll.length
  const drawN = Math.max(2, Math.floor(chartProgress * totalN))
  const wtiDrawN = Math.min(drawN, wtiAll.length)

  function toX(i: number, len: number) { return pad.left + (i / (len - 1)) * chartW }
  function toY(val: number) { return pad.top + ((maxV - val) / range) * chartH }

  function drawLine(data: number[], maxI: number, color: string, glowColor: string, fillC1: string, fillC2: string, lineW: number, isPrimary: boolean) {
    if (maxI < 2) return
    const pts: Array<{ x: number; y: number }> = []
    for (let i = 0; i < maxI && i < data.length; i++)
      pts.push({ x: toX(i, data.length), y: toY(data[i]) })

    // 面积
    ctx.save()
    ctx.beginPath()
    ctx.moveTo(pts[0].x, pts[0].y)
    for (let i = 1; i < pts.length; i++) {
      if (i < pts.length - 1) {
        const mx = (pts[i].x + pts[i + 1].x) / 2, my = (pts[i].y + pts[i + 1].y) / 2
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my)
      } else ctx.lineTo(pts[i].x, pts[i].y)
    }
    ctx.lineTo(pts[pts.length - 1].x, H - pad.bottom)
    ctx.lineTo(pts[0].x, H - pad.bottom)
    ctx.closePath()
    const fg = ctx.createLinearGradient(0, pad.top, 0, H - pad.bottom)
    fg.addColorStop(0, fillC1)
    fg.addColorStop(1, fillC2)
    ctx.fillStyle = fg
    ctx.fill()
    ctx.restore()

    // 发光
    if (isPrimary) {
      ctx.save()
      ctx.beginPath()
      ctx.moveTo(pts[0].x, pts[0].y)
      for (let i = 1; i < pts.length; i++) {
        if (i < pts.length - 1) {
          const mx = (pts[i].x + pts[i + 1].x) / 2, my = (pts[i].y + pts[i + 1].y) / 2
          ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my)
        } else ctx.lineTo(pts[i].x, pts[i].y)
      }
      ctx.strokeStyle = glowColor
      ctx.lineWidth = 12
      ctx.lineCap = 'round'
      ctx.lineJoin = 'round'
      ctx.filter = 'blur(6px)'
      ctx.stroke()
      ctx.filter = 'none'
      ctx.restore()
    }

    // 主线
    ctx.save()
    ctx.beginPath()
    ctx.moveTo(pts[0].x, pts[0].y)
    for (let i = 1; i < pts.length; i++) {
      if (i < pts.length - 1) {
        const mx = (pts[i].x + pts[i + 1].x) / 2, my = (pts[i].y + pts[i + 1].y) / 2
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my)
      } else ctx.lineTo(pts[i].x, pts[i].y)
    }
    ctx.strokeStyle = color
    ctx.lineWidth = lineW
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.stroke()
    ctx.restore()

    // 粒子
    if (isPrimary && chartProgress >= 1) {
      for (let i = 0; i < 6; i++) {
        const t = (time * 0.35 + i * 0.17) % 1
        const idx = Math.floor(t * (pts.length - 1))
        const frac = t * (pts.length - 1) - idx
        if (idx >= pts.length - 1) continue
        const px = pts[idx].x + (pts[idx + 1].x - pts[idx].x) * frac
        const py = pts[idx].y + (pts[idx + 1].y - pts[idx].y) * frac
        const pr = 1.2 + Math.sin(time * 4 + i) * 0.6
        const alpha = 0.25 + Math.sin(time * 3 + i * 1.3) * 0.15
        ctx.beginPath()
        ctx.arc(px, py, pr, 0, Math.PI * 2)
        ctx.fillStyle = `rgba(180,210,255,${alpha})`
        ctx.fill()
      }
    }

    // 节点
    if (chartProgress >= 1) {
      const nodeIdxs = isPrimary
        ? [0, Math.floor(data.length * 0.25), Math.floor(data.length * 0.5), Math.floor(data.length * 0.75), data.length - 1]
        : [0, Math.floor(data.length * 0.5), data.length - 1]
      nodeIdxs.forEach((idx) => {
        if (idx >= data.length || idx >= pts.length) return
        const p = pts[idx]
        const br = idx === data.length - 1 ? 3.5 : 2
        ctx.beginPath()
        ctx.arc(p.x, p.y, br, 0, Math.PI * 2)
        ctx.fillStyle = '#60a5fa'
        ctx.fill()
      })

      if (isPrimary) {
        const ep = pts[pts.length - 1]
        const lp = data[data.length - 1], pp = data[data.length - 2]
        const chg = lp - pp, chgP = (chg / pp) * 100, isUp = chg >= 0
        const ly = ep.y - 18 - Math.sin(time * 2) * 1.5
        ctx.save()
        ctx.fillStyle = 'rgba(10,18,36,.88)'
        ctx.strokeStyle = 'rgba(148,163,184,.12)'
        ctx.lineWidth = 0.7
        ctx.beginPath()
        ctx.roundRect(ep.x - 29, ly - 14, 58, 28, 5)
        ctx.fill()
        ctx.stroke()
        ctx.font = "bold 12px 'SF Mono','Cascadia Code',monospace"
        ctx.textAlign = 'center'
        ctx.fillStyle = '#f1f5f9'
        ctx.fillText(`$${lp.toFixed(1)}`, ep.x, ly + 2)
        ctx.font = "bold 9px 'SF Mono','Cascadia Code',monospace"
        ctx.fillStyle = isUp ? '#34d399' : '#f87171'
        ctx.fillText(`${isUp ? '+' : ''}${chgP.toFixed(1)}%`, ep.x, ly + 13)
        ctx.restore()
      }
    }
  }

  // 预测分界线
  if (chartProgress >= 0.6) {
    const divIdx = OIL_DATA.actual.length - 1
    if (divIdx < drawN && divIdx < brentAll.length) {
      const dx = toX(divIdx, brentAll.length)
      ctx.save()
      ctx.setLineDash([3, 4])
      ctx.strokeStyle = 'rgba(139,92,246,.15)'
      ctx.lineWidth = 0.7
      ctx.beginPath()
      ctx.moveTo(dx, pad.top)
      ctx.lineTo(dx, H - pad.bottom)
      ctx.stroke()
      ctx.setLineDash([])
      ctx.font = "bold 8px 'SF Mono','Cascadia Code',monospace"
      ctx.textAlign = 'center'
      ctx.fillStyle = 'rgba(139,92,246,.35)'
      ctx.fillText('FORECAST', dx, pad.top - 6)
      ctx.restore()
    }
  }

  // WTI
  drawLine(wtiAll, wtiDrawN, 'rgba(251,191,36,.40)', 'rgba(251,191,36,.03)', 'rgba(251,191,36,.03)', 'rgba(251,191,36,.001)', 1.4, false)
  // Brent
  drawLine(brentAll, drawN, '#60a5fa', 'rgba(96,165,250,.08)', 'rgba(96,165,250,.07)', 'rgba(96,165,250,.001)', 2.2, true)

  // 图例
  if (chartProgress >= 1) {
    ctx.save()
    const legX = W - pad.right + 8, legY = pad.top + 5
    ctx.beginPath(); ctx.moveTo(legX, legY); ctx.lineTo(legX + 14, legY)
    ctx.strokeStyle = '#60a5fa'; ctx.lineWidth = 2.2; ctx.lineCap = 'round'; ctx.stroke()
    ctx.font = "bold 8px 'SF Mono','Cascadia Code',monospace"
    ctx.fillStyle = 'rgba(226,232,240,.4)'; ctx.textAlign = 'left'; ctx.fillText('BRENT', legX, legY + 13)
    ctx.beginPath(); ctx.moveTo(legX, legY + 24); ctx.lineTo(legX + 14, legY + 24)
    ctx.strokeStyle = 'rgba(251,191,36,.55)'; ctx.lineWidth = 1.4; ctx.stroke()
    ctx.fillStyle = 'rgba(226,232,240,.25)'; ctx.fillText('WTI', legX, legY + 37)
    ctx.restore()
  }
}

function animateChart() {
  if (chartProgress < 1) {
    chartProgress += 0.018
    if (chartProgress > 1) chartProgress = 1
    drawMainChart()
    chartAnimId = requestAnimationFrame(animateChart)
  } else {
    chartAnimId = requestAnimationFrame(function tick() {
      drawMainChart()
      chartAnimId = requestAnimationFrame(tick)
    })
  }
}

// ===== 退出 =====
function handleLogout() {
  clearToken()
  router.push({ name: 'Landing' })
}

// ===== 生命周期 =====
onMounted(() => {
  updateClock()
  clockTimer = setInterval(updateClock, 1000)
  animateChart()
})

onBeforeUnmount(() => {
  clearInterval(clockTimer)
  if (chartAnimId !== null) cancelAnimationFrame(chartAnimId)
})
</script>

<style scoped>
/* ================================================================
   HOME PAGE — 大宗绿测 · 数据大屏
   Style: DataV 深色科技风 · 顶部导航 + Bento 布局
   ================================================================ */
.home-page {
  min-height: 100vh;
  background: #050a14;
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
}

/* ══════════════════════════════════════════════════
   顶部导航栏
   ══════════════════════════════════════════════════ */
.top-nav {
  position: sticky;
  top: 0;
  z-index: 100;
  display: flex;
  align-items: center;
  height: 56px;
  padding: 0 24px;
  background: rgba(8, 12, 24, 0.85);
  backdrop-filter: blur(20px) saturate(1.4);
  -webkit-backdrop-filter: blur(20px) saturate(1.4);
  border-bottom: 1px solid rgba(59, 130, 246, 0.08);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.3), 0 0 60px -20px rgba(59, 130, 246, 0.06);
}

/* 品牌 */
.nav-brand {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-shrink: 0;
}
.brand-icon {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: rgba(255, 255, 255, 0.9);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 4px 16px rgba(59, 130, 246, 0.25);
}
.brand-name {
  font-size: 16px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: 1.5px;
}
.brand-sep {
  color: rgba(148, 163, 184, 0.15);
  font-size: 14px;
}
.brand-sub {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.4);
  letter-spacing: 0.5px;
}

/* 中间状态指标 */
.nav-stats {
  display: flex;
  align-items: center;
  gap: 0;
  margin-left: 40px;
  flex: 1;
}
.stat-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 16px;
  transition: background 0.2s;
  border-radius: 8px;
}
.stat-item:hover {
  background: rgba(255, 255, 255, 0.03);
}
.stat-dot {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  flex-shrink: 0;
}
.stat-dot--green {
  background: #34d399;
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.5);
  animation: blink 2s ease-in-out infinite;
}
.stat-dot--blue {
  background: #60a5fa;
  box-shadow: 0 0 8px rgba(96, 165, 250, 0.5);
  animation: blink 2s ease-in-out infinite 0.5s;
}
@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}
.stat-icon {
  color: rgba(148, 163, 184, 0.35);
  flex-shrink: 0;
}
.stat-label {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.45);
  white-space: nowrap;
}
.stat-val {
  font-size: 12px;
  font-weight: 600;
  color: #cbd5e1;
  white-space: nowrap;
}
.stat-val--mono {
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.6);
}
.stat-val--success {
  color: #34d399;
}
.stat-divider {
  width: 1px;
  height: 20px;
  background: rgba(148, 163, 184, 0.08);
}

/* 右侧搜索 + 用户 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
  flex-shrink: 0;
}
.search-box {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 12px;
  height: 34px;
  border-radius: 9px;
  border: 1px solid rgba(255, 255, 255, 0.06);
  background: rgba(255, 255, 255, 0.025);
  transition: all 0.25s;
  min-width: 240px;
}
.search-box.focused {
  border-color: rgba(59, 130, 246, 0.3);
  background: rgba(59, 130, 246, 0.04);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.06);
}
.search-icon {
  color: rgba(148, 163, 184, 0.35);
  flex-shrink: 0;
}
.search-box input {
  flex: 1;
  border: none;
  background: transparent;
  color: #e2e8f0;
  font-size: 13px;
  outline: none;
  min-width: 0;
}
.search-box input::placeholder {
  color: rgba(100, 116, 139, 0.5);
}
.search-kbd {
  font-size: 10px;
  font-family: inherit;
  color: rgba(148, 163, 184, 0.3);
  background: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.06);
  border-radius: 4px;
  padding: 1px 5px;
  line-height: 1.6;
}

/* 用户 */
.nav-user {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 4px 10px 4px 4px;
  border-radius: 10px;
  cursor: pointer;
  transition: background 0.2s;
  color: rgba(148, 163, 184, 0.5);
}
.nav-user:hover {
  background: rgba(255, 255, 255, 0.04);
  color: #94a3b8;
}
.user-avatar {
  width: 30px;
  height: 30px;
  border-radius: 8px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: rgba(255, 255, 255, 0.9);
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
}
.user-name {
  font-size: 13px;
  font-weight: 500;
  color: #cbd5e1;
}

/* ══════════════════════════════════════════════════
   主内容区
   ══════════════════════════════════════════════════ */
.main-content {
  flex: 1;
  padding: 16px 24px 24px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  overflow: auto;
}

/* ─── KPI 卡片行 ─── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
}
.kpi-card {
  min-height: 120px;
}
.kpi-inner {
  padding: 18px 20px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.kpi-label-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10px;
}
.kpi-tag {
  font-size: 9.5px;
  font-weight: 700;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.45);
}
.kpi-live {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: rgba(192, 132, 252, 0.55);
}
.live-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c084fc;
  animation: pulseLive 2s ease infinite;
  box-shadow: 0 0 6px rgba(192, 132, 252, 0.4);
}
.live-dot--green {
  background: #34d399 !important;
  box-shadow: 0 0 6px rgba(52, 211, 153, 0.4) !important;
}
@keyframes pulseLive {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.25; }
}
.kpi-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 3px 8px;
  border-radius: 5px;
  letter-spacing: 0.08em;
}
.kpi-badge--up {
  color: #34d399;
  background: rgba(16, 185, 129, 0.08);
}
.kpi-badge--stable {
  color: rgba(148, 163, 184, 0.5);
  background: rgba(148, 163, 184, 0.06);
}

.kpi-price {
  font-size: 28px;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: -0.03em;
  line-height: 1;
}
.kpi-change {
  font-size: 13px;
  font-weight: 600;
  margin-top: 4px;
}
.kpi-change--up { color: #34d399; }
.kpi-change--down { color: #f87171; }
.kpi-change--ai { color: #a78bfa; }
.kpi-sub {
  font-size: 10.5px;
  color: rgba(148, 163, 184, 0.35);
  margin-top: 6px;
}

/* ─── 中间面板行 ─── */
.mid-row {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 14px;
  flex: 1;
  min-height: 400px;
}
.panel {
  min-height: 0;
}
.panel-inner {
  padding: 16px 18px;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.panel-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.panel-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.15em;
  padding: 3px 8px;
  border-radius: 5px;
  text-transform: uppercase;
  color: #c084fc;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
}
.panel-title {
  font-size: 14px;
  font-weight: 600;
  color: #cbd5e1;
}
.panel-live {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: rgba(192, 132, 252, 0.55);
}

/* 左侧占位区 */
.placeholder-zone {
  display: flex;
  align-items: center;
  justify-content: center;
}
.placeholder-hint {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: rgba(148, 163, 184, 0.15);
}
.placeholder-hint span {
  font-size: 13px;
  letter-spacing: 0.5px;
}

/* 数据表格区 */
.data-table-area {
  flex: 1;
  min-height: 0;
}
.panel-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.35);
  margin-top: 8px;
  flex-shrink: 0;
}
.panel-foot strong {
  color: #a78bfa;
  font-size: 13px;
}

/* ══════════════════════════════════════════════════
   响应式
   ══════════════════════════════════════════════════ */
@media (max-width: 1200px) {
  .nav-stats { margin-left: 20px; }
  .stat-item { padding: 6px 10px; }
  .brand-sub { display: none; }
  .brand-sep { display: none; }
}

@media (max-width: 900px) {
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .mid-row {
    grid-template-columns: 1fr;
  }
  .nav-stats { display: none; }
  .top-nav { padding: 0 16px; }
  .main-content { padding: 12px 16px 16px; }
}

@media (max-width: 600px) {
  .kpi-row {
    grid-template-columns: 1fr;
  }
  .search-box { min-width: 160px; }
  .search-kbd { display: none; }
  .user-name { display: none; }
}
</style>
