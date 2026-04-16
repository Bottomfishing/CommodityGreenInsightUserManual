<template>
  <div>
    <!-- ══════════════════════════════════════════
         Hero 区域
    ══════════════════════════════════════════ -->
    <div class="hero">
      <h1 class="hero-title">大宗绿测 · 油价预测平台</h1>
      <p class="hero-sub">基于 GRU 的油价预测与绿色金融风险分析一体化工作台</p>
      <div class="hero-actions">
        <a class="hero-btn-primary" href="#task-config">立即开始</a>
        <a class="hero-btn-secondary" href="/用户手册.pdf" target="_blank">用户手册</a>
      </div>
      <div class="kpi-row">
        <div class="kpi-card">
          <div class="kpi-label">当前状态</div>
          <div :class="['kpi-value', systemStatus.valCls]">
            {{ systemStatus.dot === 'active' ? '●' : '○' }} {{ systemStatus.text }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">当前目录</div>
          <div class="kpi-value blue" style="font-size:1rem;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;">
            {{ currentRunDir || '—' }}
          </div>
        </div>
        <div class="kpi-card">
          <div class="kpi-label">启动时间</div>
          <div class="kpi-value" style="font-size:0.95rem;">{{ startedAt || '—' }}</div>
        </div>
      </div>
    </div>

    <!-- ── 步骤指示器 ── -->
    <div class="pipeline-wrap">
      <div class="hero-steps">
        <div class="hero-step-item">
          <div :class="['hero-step-circle', runCount > 0 ? 'done' : 'wait']">1</div>
          <div :class="['hero-step-lbl', runCount > 0 ? 'done' : '']">上传数据</div>
        </div>
        <div :class="['hero-connector', runCount > 0 ? 'done' : '']"></div>
        <div class="hero-step-item">
          <div :class="['hero-step-circle', runCount === 0 ? 'active' : (runCount > 0 ? 'done' : 'wait')]">2</div>
          <div :class="['hero-step-lbl', runCount === 0 ? 'active' : (runCount > 0 ? 'done' : '')]">配置参数</div>
        </div>
        <div class="hero-connector"></div>
        <div class="hero-step-item">
          <div class="hero-step-circle wait">3</div>
          <div class="hero-step-lbl">训练监控</div>
        </div>
        <div class="hero-connector"></div>
        <div class="hero-step-item">
          <div class="hero-step-circle wait">4</div>
          <div class="hero-step-lbl">查看结果</div>
        </div>
      </div>
    </div>

    <!-- ── KPI 卡片行（主区域） ── -->
    <div class="cols-3" style="margin-bottom:1rem;">
      <div class="kpi-card kpi-card--light">
        <div class="kpi-label">累计运行次数</div>
        <div class="kpi-value">{{ runCount }}</div>
      </div>
      <div class="kpi-card kpi-card--light">
        <div class="kpi-label">当前任务</div>
        <div :class="['kpi-value', systemStatus.valCls]" style="font-size:1rem;">
          {{ systemStatus.dot === 'active' ? '●' : '○' }} {{ systemStatus.text }}
        </div>
      </div>
      <div class="kpi-card kpi-card--light">
        <div class="kpi-label">当前目录</div>
        <div class="kpi-value" style="font-size:0.9rem;">{{ selectedRunId || '未选择' }}</div>
      </div>
    </div>

    <!-- ── 实盘预测（展开面板） ── -->
    <div class="expander" style="margin-bottom:1rem;">
      <div class="expander-header" @click="forecastOpen = !forecastOpen">
        <span>实盘预测（默认开启）</span>
        <span :class="['expander-chevron', forecastOpen ? 'open' : '']">▼</span>
      </div>
      <div v-if="forecastOpen" class="expander-body">
        <label class="checkbox-wrap" style="margin-bottom:0.75rem;">
          <input type="checkbox" v-model="enableForecast" />
          训练完成后，递推预测未来 H 天
        </label>
        <div v-if="enableForecast" class="cols-2">
          <div class="form-group">
            <label class="form-label">截止日期（默认：数据最后一天）</label>
            <input type="date" class="form-input" v-model="cutoffDate" />
          </div>
          <div class="form-group">
            <label class="form-label">预测未来天数 H</label>
            <input type="number" class="form-input" v-model.number="forecastSteps"
              min="1" max="90" step="1" />
          </div>
        </div>
      </div>
    </div>

    <!-- ══════════════════════════════════════════
         任务配置与启动
    ══════════════════════════════════════════ -->
    <div id="task-config" class="section-title">任务配置与启动</div>

    <!-- ① 上传 -->
    <p style="font-weight:600;font-size:0.88rem;margin:0 0 0.5rem;">
      ① 上传标准zip包，系统自动识别目录结构并校验关键文件（必选）
    </p>
    <div
      class="upload-area"
      :class="{ dragging: isDragging }"
      @dragover.prevent="isDragging = true"
      @dragleave="isDragging = false"
      @drop.prevent="onDrop"
      @click="$refs.fileInput.click()"
    >
      <div class="upload-icon">📦</div>
      <div class="upload-text">
        {{ uploadedFile ? uploadedFile.name : '点击或拖拽上传 .zip 数据包' }}
      </div>
      <div class="upload-hint">仅支持 .zip 格式，需包含 raw_data/ 和 能源基本面与下游产业/ 目录</div>
      <input ref="fileInput" type="file" accept=".zip" style="display:none" @change="onFileChange" />
    </div>
    <div v-if="uploadedFile" style="margin-top:0.4rem;">
      <span class="alert alert-success" style="display:inline-block;padding:0.3rem 0.75rem;font-size:0.8rem;">
        ✓ 已选：{{ uploadedFile.name }} ({{ formatSize(uploadedFile.size) }})
      </span>
    </div>

    <!-- ② 参数 -->
    <p style="font-weight:600;font-size:0.88rem;margin:1rem 0 0.5rem;">
      ② 选择Top-N与实盘预测参数，兼顾速度、稳定性和可解释性
    </p>

    <div class="form-group">
      <label class="form-label">随机森林特征选择 Top‑N（推荐选择 top-15）</label>
      <div class="range-wrap">
        <input type="range" v-model.number="topN" min="5" max="200" step="1" />
        <span class="range-val">{{ topN }}</span>
      </div>
    </div>

    <p style="font-weight:600;font-size:0.88rem;margin:0 0 0.5rem;">建模参数</p>
    <div class="form-group">
      <label class="form-label">训练轮数 Epochs</label>
      <input type="number" class="form-input" v-model.number="epochs"
        min="1" max="2000" step="10" style="max-width:200px;" />
    </div>

    <!-- ③ 启动 -->
    <p style="font-weight:600;font-size:0.88rem;margin:0 0 0.5rem;">
      ③ 任务启动后可实时查看日志与训练曲线，异常可直接排查
    </p>

    <label class="checkbox-wrap" style="margin-bottom:0.5rem;">
      <input type="checkbox" v-model="enableEarlyStopping" />
      启用早停 EarlyStopping（推荐）
    </label>

    <label class="checkbox-wrap" style="margin-bottom:1rem;">
      <input type="checkbox" v-model="autoBond" />
      训练成功后自动运行绿债预测
      <span style="font-size:0.75rem;color:var(--text-muted);margin-left:0.4rem;">
        （使用工程内 bond_date/data.csv 及本次 oil_pred.csv）
      </span>
    </label>

    <!-- ④ 启动按钮行 -->
    <div style="display:flex;align-items:center;gap:1rem;margin-bottom:1rem;">
      <button
        class="btn btn-primary"
        :disabled="!uploadedFile || isRunning || isStarting"
        @click="startRun"
      >
        <span v-if="isStarting"><span class="spinner"></span> 启动中…</span>
        <span v-else>④ 开始运行</span>
      </button>
      <span style="font-size:0.82rem;color:var(--text-muted);">
        提示：训练可能较久。开始运行后可以切到「训练监控」实时看曲线。
      </span>
    </div>

    <!-- 错误提示 -->
    <div v-if="errorMsg" class="alert alert-error" style="margin-bottom:0.75rem;">{{ errorMsg }}</div>

    <!-- ══════════════════════════════════════════
         运行中：实时日志
    ══════════════════════════════════════════ -->
    <template v-if="isRunning">
      <div class="alert alert-info" style="margin-bottom:0.75rem;">
        当前有后台任务正在运行：输出目录 <code>{{ currentRunDir }}</code>（开始时间：{{ startedAt }}）
      </div>

      <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;">
        <label class="checkbox-wrap">
          <input type="checkbox" v-model="autoRefreshLog" />
          实时刷新日志（每 2 秒）
        </label>
        <button class="btn btn-secondary" style="padding:0.35rem 0.85rem;" @click="stopRun">
          停止当前任务
        </button>
      </div>

      <h3 class="section-h3">实时终端输出（最近 400 行）</h3>
      <div class="terminal-block" ref="terminalRef">{{ logContent || '（等待日志…）' }}</div>
    </template>

    <!-- ══════════════════════════════════════════
         上一次任务结束后展示（run.log末行 + 银行报告）
    ══════════════════════════════════════════ -->
    <template v-if="!isRunning && lastRunStatus">
      <div v-if="lastRunStatus === 'success'" class="alert alert-success" style="margin-bottom:0.75rem;">
        上一次任务已结束（正常退出）。可以去「结果预览 / 下载」查看输出。
      </div>
      <div v-else-if="lastRunStatus === 'error'" class="alert alert-error" style="margin-bottom:0.75rem;">
        上一次任务异常结束。请查看下面的 run.log 最后几行。
      </div>
      <div v-if="prevLogTail" class="terminal-block">{{ prevLogTail }}</div>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, onUnmounted } from 'vue'
import { createOilRun, stopOilRun, fetchRunLog, fetchSystemStatus } from '../api/index.js'

const props = defineProps({
  systemStatus: Object,
  runCount: Number,
  selectedRunId: String,
})

const emit = defineEmits(['run-started', 'tab-change'])

// ── 参数状态 ──
const forecastOpen = ref(true)
const enableForecast = ref(true)
const cutoffDate = ref('')
const forecastSteps = ref(1)
const topN = ref(10)
const epochs = ref(200)
const enableEarlyStopping = ref(true)
const autoBond = ref(false)
const uploadedFile = ref(null)
const isDragging = ref(false)

// ── 运行状态 ──
const isStarting = ref(false)
const isRunning = computed(() => props.systemStatus?.dot === 'active')
const currentRunDir = ref('')
const startedAt = ref('')
const errorMsg = ref('')
const lastRunStatus = ref('')
const prevLogTail = ref('')

// ── 日志 ──
const logContent = ref('')
const autoRefreshLog = ref(true)
const terminalRef = ref(null)
let logTimer = null

// ── 文件上传 ──
function onFileChange(e) {
  const f = e.target.files[0]
  if (f) uploadedFile.value = f
}
function onDrop(e) {
  isDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f && f.name.endsWith('.zip')) uploadedFile.value = f
}
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

// ── 轮询日志 ──
async function pollLog() {
  if (!isRunning.value) return
  try {
    // 获取系统状态以拿到当前 run_id
    const status = await fetchSystemStatus()
    if (status.current_run_id) {
      currentRunDir.value = status.current_run_id
      startedAt.value = status.started_at || ''
      const logResp = await fetchRunLog(status.current_run_id)
      logContent.value = typeof logResp === 'string' ? logResp : (logResp?.content || '')
      if (terminalRef.value) {
        terminalRef.value.scrollTop = terminalRef.value.scrollHeight
      }
    }
  } catch (e) { /* 静默 */ }
}

watch(autoRefreshLog, (v) => {
  clearInterval(logTimer)
  if (v) logTimer = setInterval(pollLog, 2000)
})

watch(() => props.systemStatus, (s) => {
  if (s?.dot === 'active') {
    if (autoRefreshLog.value && !logTimer) {
      logTimer = setInterval(pollLog, 2000)
    }
  } else {
    clearInterval(logTimer)
    logTimer = null
  }
}, { immediate: true })

// ── 启动训练 ──
async function startRun() {
  if (!uploadedFile.value) return
  isStarting.value = true
  errorMsg.value = ''
  try {
    const formData = new FormData()
    formData.append('zip_file', uploadedFile.value)
    formData.append('top_n', topN.value)
    formData.append('epochs', epochs.value)
    if (enableForecast.value) {
      formData.append('forecast_steps', forecastSteps.value)
      if (cutoffDate.value) formData.append('cutoff_date', cutoffDate.value)
    } else {
      formData.append('forecast_steps', 0)
    }
    formData.append('enable_early_stopping', enableEarlyStopping.value)
    formData.append('auto_bond', autoBond.value)

    const result = await createOilRun(formData)
    if (result.run_id) {
      currentRunDir.value = result.run_id
      emit('run-started', result.run_id)
      autoRefreshLog.value = true
      logTimer = setInterval(pollLog, 2000)
    }
  } catch (e) {
    errorMsg.value = e?.message || '启动失败，请检查网络或后端服务'
  } finally {
    isStarting.value = false
  }
}

// ── 停止任务 ──
async function stopRun() {
  try {
    const status = await fetchSystemStatus()
    if (status.current_run_id) {
      await stopOilRun(status.current_run_id)
    }
  } catch (e) {
    errorMsg.value = '停止失败：' + (e?.message || '')
  }
}

onUnmounted(() => {
  clearInterval(logTimer)
})
</script>
