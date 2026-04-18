<template>
  <div>
    <h2 class="section-h2">训练监控</h2>

    <!-- ── 监控来源选择（radio，和原版完全一致） ── -->
    <div class="card" style="margin-bottom:1rem;">
      <div class="form-label" style="margin-bottom:0.5rem;">监控来源</div>
      <div class="radio-group">
        <label class="radio-item" v-for="opt in monitorOptions" :key="opt.value">
          <input type="radio" :value="opt.value" v-model="monitorMode" :disabled="opt.disabled" />
          {{ opt.label }}
        </label>
      </div>

      <div v-if="monitorMode === 'manual'" style="margin-top:0.75rem;">
        <label class="form-label">输入要监控的输出目录路径（run_id）</label>
        <input
          type="text"
          class="form-input"
          v-model="manualRunId"
          placeholder="run_YYYYMMDD_HHMMSS_topN"
        />
      </div>
    </div>

    <!-- ── 无监控目录提示 ── -->
    <template v-if="!activeRunId">
      <div class="empty-state">
        <div class="empty-title">还没有可监控的输出目录</div>
        <div class="empty-desc">请先在「运行」页面启动一次训练，或手动输入输出目录路径。</div>
      </div>
    </template>

    <template v-else>
      <!-- ── 当前监控路径提示 ── -->
      <div :class="['alert', isActive ? 'alert-info' : '']" style="margin-bottom:0.75rem;">
        <template v-if="isActive">正在监控：<code>{{ activeRunId }}</code>（训练中 / 日志更新中）</template>
        <template v-else>正在监控：<code>{{ activeRunId }}</code></template>
      </div>

      <!-- ── 文件状态行 ── -->
      <div class="file-status-row">
        <div class="file-status-card">
          <div class="file-status-label">training_log.csv</div>
          <div class="file-status-val">{{ fileStatuses.trainingLog }}</div>
        </div>
        <div class="file-status-card">
          <div class="file-status-label">prediction_results.csv</div>
          <div class="file-status-val">{{ fileStatuses.predResults }}</div>
        </div>
        <div class="file-status-card">
          <div class="file-status-label">run.log</div>
          <div class="file-status-val">{{ fileStatuses.runLog }}</div>
        </div>
      </div>

      <!-- ── 自动刷新控制 ── -->
      <div style="display:flex;align-items:center;gap:1.5rem;margin-bottom:1rem;flex-wrap:wrap;">
        <label class="checkbox-wrap">
          <input type="checkbox" v-model="autoRefresh" />
          自动刷新（训练进行中建议开启）
        </label>
        <div class="range-wrap" style="flex:0 0 220px;" :style="{ opacity: autoRefresh ? 1 : 0.4 }">
          <span style="font-size:0.8rem;color:var(--text-sub);white-space:nowrap;">刷新间隔（秒）</span>
          <input type="range" v-model.number="refreshSec" min="2" max="10" step="1" :disabled="!autoRefresh" />
          <span class="range-val">{{ refreshSec }}</span>
        </div>
        <button class="btn btn-secondary" style="padding:0.35rem 0.85rem;" @click="loadDashboard">
          手动刷新一次
        </button>
      </div>

      <!-- ════════════════════════════════════
           图表区域
      ════════════════════════════════════ -->

      <!-- 训练曲线：Train / Val Loss -->
      <div class="section-title">训练过程：Train / Val Loss</div>
      <template v-if="lossData.length === 0">
        <div class="alert alert-info">
          还没有找到可用的训练曲线数据：training_log.csv 为空，且 run.log 尚未解析到 loss。
        </div>
      </template>
      <template v-else>
        <div ref="lossChartRef" class="chart-box"></div>
      </template>

      <!-- 价格对比 -->
      <div class="section-title">最终预测效果：价格对比</div>
      <template v-if="priceData.length === 0">
        <div class="alert alert-info">
          还没有找到 prediction_results.csv（训练未结束或未写出）。
        </div>
      </template>
      <template v-else>
        <div ref="priceChartRef" class="chart-box"></div>
      </template>

      <!-- 收益对比 -->
      <div class="section-title">最终预测效果：收益对比</div>
      <template v-if="returnData.length === 0">
        <div class="alert alert-info">
          还没有找到 prediction_results.csv（训练未结束或未写出）。
        </div>
      </template>
      <template v-else>
        <div ref="returnChartRef" class="chart-box"></div>
      </template>

      <!-- run.log 终端输出（无曲线时显示） -->
      <template v-if="lossData.length === 0 && logContent">
        <hr class="divider" />
        <p style="font-weight:600;font-size:0.85rem;margin-bottom:0.4rem;">
          还没出现训练曲线？先看 run.log 最后几行（通常卡在数据加载 / 特征工程 / 尚未进入训练）
        </p>
        <div class="terminal-block">{{ logContent }}</div>
      </template>

      <p v-if="autoRefresh" style="font-size:0.78rem;color:var(--text-muted);margin-top:0.5rem;">
        自动刷新已开启：每 {{ refreshSec }} 秒刷新一次
      </p>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { fetchTrainingDashboard, fetchRunLog } from '../api/index.js'

const props = defineProps({
  selectedRunId: String,
  runList: Array,
})

// ── 监控模式选项 ──
const monitorMode = ref('selected')
const manualRunId = ref('')

const monitorOptions = computed(() => [
  { value: 'selected', label: '监控：左侧栏选择的输出目录' },
  { value: 'latest',   label: '监控：最近一次运行（最新）' },
  { value: 'manual',   label: '监控：手动输入输出目录路径' },
])

const activeRunId = computed(() => {
  if (monitorMode.value === 'manual') return manualRunId.value.trim() || ''
  if (monitorMode.value === 'latest') {
    return props.runList?.[0]?.run_id || ''
  }
  return props.selectedRunId || ''
})

const isActive = ref(false)

// ── 文件状态 ──
const fileStatuses = ref({
  trainingLog: '未知',
  predResults: '未知',
  runLog: '未知',
})

// ── 图表数据 ──
const lossData = ref([])
const priceData = ref([])
const returnData = ref([])
const logContent = ref('')

// ── 图表 DOM 引用 ──
const lossChartRef = ref(null)
const priceChartRef = ref(null)
const returnChartRef = ref(null)
let lossChart = null
let priceChart = null
let returnChart = null

// ── 自动刷新 ──
const autoRefresh = ref(true)
const refreshSec = ref(3)
let refreshTimer = null

// ── 加载数据 ──
async function loadDashboard() {
  if (!activeRunId.value) return
  try {
    const data = await fetchTrainingDashboard(activeRunId.value)
    // 后端字段：loss_series / price_series / return_series / run_log_tail / is_log_active
    lossData.value = Array.isArray(data.loss_series) ? data.loss_series : []
    priceData.value = Array.isArray(data.price_series) ? data.price_series : []
    returnData.value = Array.isArray(data.return_series) ? data.return_series : []
    logContent.value = data.run_log_tail || ''

    // 文件状态：后端不再返回 file_statuses，这里用“是否有数据”做最小提示
    fileStatuses.value = {
      trainingLog: lossData.value.length ? '已生成' : '未找到/为空',
      predResults: (priceData.value.length || returnData.value.length) ? '已生成' : '未找到/为空',
      runLog: logContent.value ? '已生成' : '未找到/为空',
    }

    isActive.value = !!data.is_log_active
    await nextTick()
    renderCharts()
  } catch(e) { /* 静默 */ }

  // 同时拉日志
  if (!lossData.value.length) {
    try {
      const log = await fetchRunLog(activeRunId.value)
      // 后端字段是 log_tail
      logContent.value = typeof log === 'string' ? log : (log?.log_tail || log?.content || '')
    } catch(e) { /* 静默 */ }
  }
}

// ── ECharts 渲染 ──
function getECharts() {
  return window.echarts || null
}

function renderCharts() {
  const ec = getECharts()
  if (!ec) return

  // Loss 曲线
  if (lossChartRef.value && lossData.value.length > 0) {
    if (!lossChart) lossChart = ec.init(lossChartRef.value)
    const epochs = lossData.value.map(r => r.epoch)
    const losses = lossData.value.map(r => r.loss ?? r.train_loss)
    const valLosses = lossData.value.map(r => r.val_loss)
    const series = [
      { name: 'train_loss', type: 'line', data: losses, smooth: true,
        lineStyle: { color: '#0080bf', width: 2 }, symbol: 'none' }
    ]
    if (valLosses.some(v => v !== null && v !== undefined)) {
      series.push({
        name: 'val_loss', type: 'line', data: valLosses, smooth: true,
        lineStyle: { color: '#16a34a', width: 2 }, symbol: 'none'
      })
    }
    lossChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: series.map(s => s.name), bottom: 0 },
      xAxis: { type: 'category', data: epochs, name: 'Epoch' },
      yAxis: { type: 'value', name: 'Loss' },
      series,
      grid: { left: 50, right: 20, top: 20, bottom: 40 },
    })
  }

  // 价格对比
  if (priceChartRef.value && priceData.value.length > 0) {
    if (!priceChart) priceChart = ec.init(priceChartRef.value)
    const dates = priceData.value.map(r => r.Date_target || r.date)
    const actual = priceData.value.map(r => r.Actual_P_t_plus_H ?? r.actual)
    const pred   = priceData.value.map(r => r.GRU_Pred_P_t_plus_H ?? r.pred)
    priceChart.setOption({
      tooltip: { trigger: 'axis' },
      legend: { data: ['Actual_Price', 'GRU_Pred_Price'], bottom: 0 },
      xAxis: { type: 'category', data: dates, axisLabel: { rotate: 30, fontSize: 10 } },
      yAxis: { type: 'value', name: 'Price' },
      series: [
        { name: 'Actual_Price', type: 'line', data: actual, smooth: true,
          lineStyle: { color: '#0080bf', width: 2 }, symbol: 'none' },
        { name: 'GRU_Pred_Price', type: 'line', data: pred, smooth: true,
          lineStyle: { color: '#f59e0b', width: 2 }, symbol: 'none' },
      ],
      grid: { left: 60, right: 20, top: 20, bottom: 50 },
    })
  }

  // 收益对比
  if (returnChartRef.value && returnData.value.length > 0) {
    if (!returnChart) returnChart = ec.init(returnChartRef.value)
    const dates2 = returnData.value.map(r => r.Date_target || r.date)
    const aRet = returnData.value.map(r => r.Actual_Return)
    const pRet = returnData.value.map(r => r.GRU_Pred_Return)
    if (aRet.some(v => v !== null && v !== undefined)) {
      returnChart.setOption({
        tooltip: { trigger: 'axis' },
        legend: { data: ['Actual_Return', 'GRU_Pred_Return'], bottom: 0 },
        xAxis: { type: 'category', data: dates2, axisLabel: { rotate: 30, fontSize: 10 } },
        yAxis: { type: 'value', name: 'Return' },
        series: [
          { name: 'Actual_Return', type: 'line', data: aRet, smooth: true,
            lineStyle: { color: '#0080bf', width: 2 }, symbol: 'none' },
          { name: 'GRU_Pred_Return', type: 'line', data: pRet, smooth: true,
            lineStyle: { color: '#16a34a', width: 2 }, symbol: 'none' },
        ],
        grid: { left: 60, right: 20, top: 20, bottom: 50 },
      })
    } else {
      returnData.value = []
    }
  }
}

// ── 监听 activeRunId 变化 ──
watch(activeRunId, (v) => {
  if (v) loadDashboard()
})

// ── 自动刷新控制 ──
watch([autoRefresh, refreshSec], () => {
  clearInterval(refreshTimer)
  if (autoRefresh.value && activeRunId.value) {
    refreshTimer = setInterval(loadDashboard, refreshSec.value * 1000)
  }
})

// ── 窗口 resize ──
function onResize() {
  lossChart?.resize()
  priceChart?.resize()
  returnChart?.resize()
}

onMounted(() => {
  // 动态加载 ECharts CDN（如果未加载）
  if (!window.echarts) {
    const script = document.createElement('script')
    script.src = 'https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js'
    script.onload = () => {
      loadDashboard()
      if (autoRefresh.value) {
        refreshTimer = setInterval(loadDashboard, refreshSec.value * 1000)
      }
    }
    document.head.appendChild(script)
  } else {
    loadDashboard()
    if (autoRefresh.value) {
      refreshTimer = setInterval(loadDashboard, refreshSec.value * 1000)
    }
  }
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  clearInterval(refreshTimer)
  window.removeEventListener('resize', onResize)
  lossChart?.dispose()
  priceChart?.dispose()
  returnChart?.dispose()
})
</script>

<style scoped>
.chart-box {
  width: 100%;
  height: 320px;
  margin-bottom: 1rem;
}
</style>
