<template>
  <div>
    <h2 class="section-h2">结果预览</h2>

    <!-- 空状态 -->
    <template v-if="!selectedRunId">
      <div class="empty-state">
        <div class="empty-title">先在「运行」里跑一次</div>
        <div class="empty-desc">或者在左侧选择一个历史输出目录。</div>
      </div>
    </template>

    <template v-else>
      <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.75rem;">
        当前预览目录：<code>{{ selectedRunId }}</code>
      </p>

      <!-- loading -->
      <div v-if="loading" style="text-align:center;padding:2rem;">
        <span class="spinner"></span> 加载中…
      </div>

      <template v-else>
        <!-- ════════════════════════════════════
             实盘预测大卡（forecast-card）
        ════════════════════════════════════ -->
        <template v-if="futureRow">
          <div class="forecast-card">
            <div>
              <div class="forecast-lbl">实盘预测下一天油价</div>
              <div class="forecast-val">{{ futureRow.predPrice }}</div>
              <div class="forecast-date">{{ futureRow.dateText }}</div>
            </div>
            <div style="flex:0 0 auto;">
              <svg width="60" height="60" viewBox="0 0 60 60" fill="none" xmlns="http://www.w3.org/2000/svg">
                <rect x="10" y="15" width="40" height="35" rx="6" stroke="#0080bf" stroke-width="3"/>
                <rect x="10" y="15" width="40" height="12" rx="6" fill="rgba(0,128,191,.15)"/>
                <rect x="17" y="22" width="7" height="7" rx="2" fill="#0080bf"/>
                <rect x="27" y="22" width="7" height="7" rx="2" fill="rgba(0,163,224,.5)"/>
                <rect x="37" y="22" width="7" height="7" rx="2" fill="rgba(0,128,191,.25)"/>
                <path d="M19 9V22" stroke="#006a9e" stroke-width="3" stroke-linecap="round"/>
                <path d="M41 9V22" stroke="#006a9e" stroke-width="3" stroke-linecap="round"/>
              </svg>
            </div>
          </div>
        </template>
        <div v-else class="alert alert-info">未找到下一天实盘预测所需的 future_forecast.csv。</div>

        <!-- ── 两列表格预览 ── -->
        <div class="cols-2" style="margin-top:1rem;">
          <div>
            <h3 class="section-h3">每日预测 vs 真实值</h3>
            <template v-if="dailyRows.length">
              <div style="overflow:auto;max-height:360px;border:1px solid var(--border);border-radius:8px;">
                <table class="data-table">
                  <thead>
                    <tr><th v-for="col in dailyCols" :key="col">{{ col }}</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in dailyRows" :key="i">
                      <td v-for="col in dailyCols" :key="col">{{ row[col] }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
            <div v-else class="alert alert-info">未找到 daily_predictions_vs_actual.csv</div>
          </div>
          <div>
            <h3 class="section-h3">对齐后的完整结果</h3>
            <template v-if="predRows.length">
              <div style="overflow:auto;max-height:360px;border:1px solid var(--border);border-radius:8px;">
                <table class="data-table">
                  <thead>
                    <tr><th v-for="col in predCols" :key="col">{{ col }}</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in predRows" :key="i">
                      <td v-for="col in predCols" :key="col">{{ row[col] }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </template>
            <div v-else class="alert alert-info">未找到 prediction_results.csv</div>
          </div>
        </div>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             企业银行团队报告
        ════════════════════════════════════ -->
        <h2 class="section-h2">企业银行团队报告</h2>
        <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.75rem;">
          底稿由训练脚本生成；AI 解读与页末「AI 专家」共用同一套模型与油价专家角色设定。
        </p>
        <template v-if="bankReport">
          <div class="forecast-card forecast-card--report">
            <div class="fc-prose" v-html="bankReportHtml"></div>
          </div>
        </template>
        <div v-else class="alert alert-info">
          未找到 bank_team_report.md。训练正常结束时主脚本会写入该文件。
        </div>

        <!-- 生成报告按钮 -->
        <div style="margin-top:0.75rem;">
          <button class="btn btn-primary" :disabled="generatingReport" @click="genAIReport">
            <span v-if="generatingReport"><span class="spinner"></span> 正在生成…</span>
            <span v-else">生成企业银行 AI 报告</span>
          </button>
        </div>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             预测图表
        ════════════════════════════════════ -->
        <h3 class="section-h3">预测图表</h3>
        <template v-if="predImgs.length">
          <img v-for="img in predImgs" :key="img.name" :src="img.url" :alt="img.name" class="img-preview" />
        </template>
        <div v-else class="alert alert-info">暂无预测图表</div>

        <h3 class="section-h3">模型解释</h3>
        <div v-if="explainImgs.length" :class="['cols-' + Math.min(explainImgs.length, 3)]">
          <div v-for="img in explainImgs" :key="img.name">
            <img :src="img.url" :alt="img.name" class="img-preview" />
            <p style="font-size:0.72rem;text-align:center;color:var(--text-muted);">{{ img.name }}</p>
          </div>
        </div>
        <div v-else class="alert alert-info">暂无解释类图像</div>

        <h3 class="section-h3">策略回测</h3>
        <template v-if="backtestImgs.length">
          <img v-for="img in backtestImgs" :key="img.name" :src="img.url" :alt="img.name" class="img-preview" />
        </template>
        <div v-else class="alert alert-info">暂无回测图表</div>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             因子分析
        ════════════════════════════════════ -->
        <h2 class="section-h2">因子分析（主要驱动因素）</h2>
        <template v-if="driverRows.length">
          <div class="cols-2">
            <div>
              <h3 class="section-h3">Top 20（按 |Spearman| 排序）</h3>
              <div style="overflow:auto;max-height:360px;border:1px solid var(--border);border-radius:8px;">
                <table class="data-table">
                  <thead>
                    <tr><th v-for="col in driverCols" :key="col">{{ col }}</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in driverRows.slice(0, 20)" :key="i">
                      <td v-for="col in driverCols" :key="col">{{ row[col] }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div>
              <h3 class="section-h3">字段说明</h3>
              <div class="card">
                <p style="font-size:0.85rem;margin:0 0 0.5rem;">
                  <strong>spearman_corr_with_return</strong>：驱动因子与实际收益的 Spearman 相关性
                </p>
                <p style="font-size:0.85rem;margin:0;">
                  <strong>rf_importance</strong>：随机森林对 WTI_Price_t_plus_H 的特征重要性
                </p>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="alert alert-info">
          未找到 driver_factor_analysis.csv（请确认脚本已更新并跑完一次）。
        </div>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             风险区间 / 信号分类
        ════════════════════════════════════ -->
        <h2 class="section-h2">风险区间 / 信号分类</h2>
        <template v-if="riskRows.length">
          <div class="cols-2">
            <div>
              <h3 class="section-h3">样本预览（前 50 行）</h3>
              <div style="overflow:auto;max-height:360px;border:1px solid var(--border);border-radius:8px;">
                <table class="data-table">
                  <thead>
                    <tr><th v-for="col in riskCols" :key="col">{{ col }}</th></tr>
                  </thead>
                  <tbody>
                    <tr v-for="(row, i) in riskRows.slice(0, 50)" :key="i">
                      <td v-for="col in riskCols" :key="col">{{ row[col] }}</td>
                    </tr>
                  </tbody>
                </table>
              </div>
            </div>
            <div>
              <h3 class="section-h3">分布统计</h3>
              <div class="card">
                <p style="font-size:0.85rem;font-weight:600;margin-bottom:0.5rem;">RiskLevel 分布：</p>
                <div v-for="(cnt, lvl) in riskLevelDist" :key="lvl"
                  style="display:flex;justify-content:space-between;font-size:0.82rem;margin:0.2rem 0;">
                  <span>{{ lvl }}</span><span>{{ cnt }}</span>
                </div>
                <div v-if="directionAcc !== null" style="margin-top:0.75rem;">
                  <p style="font-size:0.85rem;font-weight:600;margin-bottom:0.25rem;">方向一致率（含 FLAT）</p>
                  <span class="kpi-value" style="font-size:1.2rem;color:var(--brand);">{{ directionAcc }}</span>
                </div>
              </div>
            </div>
          </div>
        </template>
        <div v-else class="alert alert-info">未找到 risk_signal_classification.csv。</div>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             回测
        ════════════════════════════════════ -->
        <h2 class="section-h2">回测（信号驱动策略 vs Buy&amp;Hold）</h2>
        <template v-if="btMetrics">
          <div class="metrics-grid">
            <div class="metric-card">
              <div class="metric-label">策略总收益</div>
              <div class="metric-value">{{ btMetrics.strategy_total }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">基准总收益</div>
              <div class="metric-value">{{ btMetrics.buyhold_total }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">最大回撤</div>
              <div class="metric-value">{{ btMetrics.max_drawdown }}</div>
            </div>
            <div class="metric-card">
              <div class="metric-label">胜率</div>
              <div class="metric-value">{{ btMetrics.win_rate }}</div>
            </div>
          </div>
        </template>
        <div v-else class="alert alert-info">未找到 backtest_metrics.csv。</div>

        <template v-if="btRows.length">
          <h3 class="section-h3">回测明细（末尾 50 行）</h3>
          <div style="overflow:auto;max-height:360px;border:1px solid var(--border);border-radius:8px;">
            <table class="data-table">
              <thead>
                <tr><th v-for="col in btCols" :key="col">{{ col }}</th></tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in btRows" :key="i">
                  <td v-for="col in btCols" :key="col">{{ row[col] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>

        <hr class="divider" />

        <!-- ── 实盘预测：未来 H 天表格 ── -->
        <h2 class="section-h2">实盘预测：未来 H 天</h2>
        <template v-if="futureRows.length">
          <div style="overflow:auto;max-height:240px;border:1px solid var(--border);border-radius:8px;">
            <table class="data-table">
              <thead>
                <tr><th v-for="col in futureCols" :key="col">{{ col }}</th></tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in futureRows" :key="i">
                  <td v-for="col in futureCols" :key="col">{{ row[col] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </template>
        <div v-else class="alert alert-info">
          未找到 future_forecast.csv（需在运行时勾选「递推预测未来 H 天」）。
        </div>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             新能源整合预测
        ════════════════════════════════════ -->
        <h2 class="section-h2">新能源整合预测</h2>
        <template v-if="!hasPredResults">
          <div class="alert alert-info">
            先在「运行」里跑完石油预测并生成 prediction_results.csv，再点「运行新能源整合预测」。
          </div>
        </template>
        <template v-else>
          <div class="form-group">
            <label class="form-label">要跑的序列（逗号分隔）</label>
            <input type="text" class="form-input" v-model="neSeries" placeholder="new_energy" style="max-width:360px;" />
          </div>

          <p style="font-weight:600;font-size:0.88rem;margin-bottom:0.5rem;">
            上传新能源数据 zip（必选）
          </p>
          <div
            class="upload-area"
            :class="{ dragging: neIsDragging }"
            style="padding:1.2rem;"
            @dragover.prevent="neIsDragging = true"
            @dragleave="neIsDragging = false"
            @drop.prevent="onNeDrop"
            @click="$refs.neFileInput.click()"
          >
            <div class="upload-text">
              {{ neFile ? neFile.name : '点击或拖拽上传新能源数据 .zip' }}
            </div>
            <input ref="neFileInput" type="file" accept=".zip" style="display:none" @change="onNeFile" />
          </div>

          <div class="cols-3" style="margin:0.75rem 0;">
            <div class="form-group">
              <label class="form-label">置信水平</label>
              <input type="number" class="form-input" v-model.number="neConf" min="0.8" max="0.99" step="0.05" />
            </div>
            <div class="form-group">
              <label class="form-label">收益缩放</label>
              <input type="number" class="form-input" v-model.number="neScale" min="10" max="300" step="10" />
            </div>
            <div class="form-group" style="padding-top:1.5rem;">
              <label class="checkbox-wrap">
                <input type="checkbox" v-model="neMakeViz" />
                生成可视化图片（推荐）
              </label>
            </div>
          </div>
          <label class="checkbox-wrap" style="margin-bottom:0.75rem;">
            <input type="checkbox" v-model="neRebuild" />
            重建 returns
          </label>

          <button class="btn btn-primary" :disabled="!neFile || neRunning" @click="runNewEnergy">
            <span v-if="neRunning"><span class="spinner"></span> 运行中…</span>
            <span v-else>运行新能源整合预测</span>
          </button>

          <div v-if="neRunning" style="margin-top:0.75rem;">
            <div class="alert alert-info">新能源整合预测正在运行中…</div>
            <div class="terminal-block">{{ neLog || '（等待日志…）' }}</div>
          </div>

          <!-- 新能源结果图 -->
          <template v-if="neImgs.length">
            <h3 class="section-h3" style="margin-top:1rem;">新能源预测对比图</h3>
            <img v-for="img in neImgs" :key="img.name" :src="img.url" :alt="img.name" class="img-preview" />
          </template>
          <div v-else-if="!neRunning && neLoaded" class="alert alert-info">
            暂无对比可视化图片（可能还没跑完）。
          </div>
        </template>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             绿债预测
        ════════════════════════════════════ -->
        <h2 class="section-h2">绿债预测</h2>
        <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.75rem;">
          绿债侧特征不要求放进油价 zip；应用在项目目录 bond_date/data.csv 中预置。
        </p>

        <div
          class="upload-area"
          style="padding:1.2rem;margin-bottom:0.75rem;"
          @click="$refs.bondFileInput.click()"
        >
          <div class="upload-text">
            {{ bondFile ? bondFile.name : '上传绿债数据 zip（可选）' }}
          </div>
          <input ref="bondFileInput" type="file" accept=".zip" style="display:none" @change="onBondFile" />
        </div>

        <div style="display:flex;align-items:center;gap:1rem;margin-bottom:0.75rem;flex-wrap:wrap;">
          <button class="btn btn-primary" :disabled="bondRunning || !hasOilPred" @click="runBond">
            <span v-if="bondRunning"><span class="spinner"></span> 运行中…</span>
            <span v-else>运行绿债预测（自动识别数据来源）</span>
          </button>
          <span style="font-size:0.82rem;color:var(--text-muted);">
            {{ hasOilPred ? '准备就绪。' : '需先完成石油训练并生成 oil_pred.csv。' }}
          </span>
        </div>

        <div v-if="bondRunning" style="margin-top:0.5rem;">
          <div class="alert alert-info">绿债预测正在运行…</div>
          <div class="terminal-block">{{ bondLog || '（等待日志…）' }}</div>
        </div>

        <!-- 绿债结果 -->
        <template v-if="bondRows.length">
          <h3 class="section-h3">绿债预测结果（前 30 行）</h3>
          <div style="overflow:auto;max-height:240px;border:1px solid var(--border);border-radius:8px;margin-bottom:0.75rem;">
            <table class="data-table">
              <thead>
                <tr><th v-for="col in bondCols" :key="col">{{ col }}</th></tr>
              </thead>
              <tbody>
                <tr v-for="(row, i) in bondRows.slice(0, 30)" :key="i">
                  <td v-for="col in bondCols" :key="col">{{ row[col] }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          <img v-for="img in bondImgs" :key="img.name" :src="img.url" :alt="img.name" class="img-preview" />
        </template>
        <div v-else-if="bondLoaded && !bondRunning" class="alert alert-info">
          未找到绿债预测输出（请先运行）。
        </div>

        <hr class="divider" />

        <!-- ── run.log 终端输出 ── -->
        <p style="font-weight:600;font-size:0.88rem;margin-bottom:0.4rem;">终端输出（run.log）</p>
        <div v-if="runLogContent" class="terminal-block">{{ runLogContent }}</div>
        <div v-else class="alert alert-info">未找到 run.log。</div>

        <hr class="divider" />

        <!-- ════════════════════════════════════
             AI 专家问答
        ════════════════════════════════════ -->
        <h2 class="section-h2">AI 专家：油价预测 &amp; 新能源风险分析</h2>
        <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.75rem;">
          会话咨询与「企业银行团队报告」的自动生成均通过同一 AI 接口；
          企业银行摘要 = 脚本底稿 + 油价专家角色下的行内摘要格式。
        </p>

        <!-- 专家模式切换 -->
        <div style="margin-bottom:0.75rem;">
          <span style="font-size:0.78rem;font-weight:600;margin-right:0.5rem;">选择专家：</span>
          <label style="margin-right:1rem;cursor:pointer;font-size:0.78rem;">
            <input type="radio" v-model="chatMode" value="oil" style="margin-right:0.25rem;" />
            油价预测专家
          </label>
          <label style="cursor:pointer;font-size:0.78rem;">
            <input type="radio" v-model="chatMode" value="new_energy" style="margin-right:0.25rem;" />
            新能源股票专家
          </label>
        </div>

        <div class="chat-wrap">
          <div class="chat-messages" ref="chatRef">
            <div v-for="(msg, i) in chatMessages" :key="i"
              :class="['chat-msg', msg.role === 'user' ? 'user' : 'bot']">
              {{ msg.content }}
            </div>
            <div v-if="chatLoading" class="chat-msg bot">
              <span class="spinner"></span> 思考中…
            </div>
          </div>
          <div class="chat-input-row">
            <input
              class="chat-input"
              type="text"
              v-model="chatInput"
              placeholder="请输入您的问题，如：下一周油价走势如何？"
              @keydown.enter="sendChat"
            />
            <button class="btn btn-primary" style="padding:0.45rem 1rem;" :disabled="chatLoading" @click="sendChat">
              发送
            </button>
          </div>
        </div>

      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import {
  fetchAnalytics,
  fetchFiles,
  fetchDownloadUrl,
  startNewEnergy,
  fetchNewEnergyLatest,
  startBond,
  fetchBondLatest,
  generateAIReport,
  sendAIChat,
  fetchRunLog,
} from '../api/index.js'

const props = defineProps({
  selectedRunId: String,
})

// ── 状态 ──
const loading = ref(false)
const analytics = ref(null)

// 实盘预测卡
const futureRow = ref(null)
const futureRows = ref([])
const futureCols = ref([])

// 表格
const dailyRows = ref([])
const dailyCols = ref([])
const predRows = ref([])
const predCols = ref([])
const driverRows = ref([])
const driverCols = ref([])
const riskRows = ref([])
const riskCols = ref([])
const riskLevelDist = ref({})
const directionAcc = ref(null)
const btMetrics = ref(null)
const btRows = ref([])
const btCols = ref([])

// 图片
const predImgs = ref([])
const explainImgs = ref([])
const backtestImgs = ref([])
const bankReport = ref('')
const bankReportHtml = computed(() => {
  if (!bankReport.value) return ''
  // 简单 md -> html
  return bankReport.value
    .replace(/^## (.+)$/gm, '<h2>$1</h2>')
    .replace(/^### (.+)$/gm, '<h3>$1</h3>')
    .replace(/^# (.+)$/gm, '<h1>$1</h1>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/\n/g, '<br/>')
})
const generatingReport = ref(false)
const hasPredResults = ref(false)
const hasOilPred = ref(false)
const runLogContent = ref('')

// 新能源
const neSeries = ref('new_energy')
const neFile = ref(null)
const neIsDragging = ref(false)
const neConf = ref(0.95)
const neScale = ref(100)
const neMakeViz = ref(true)
const neRebuild = ref(false)
const neRunning = ref(false)
const neLog = ref('')
const neImgs = ref([])
const neLoaded = ref(false)
let neTimer = null

// 绿债
const bondFile = ref(null)
const bondRunning = ref(false)
const bondLog = ref('')
const bondRows = ref([])
const bondCols = ref([])
const bondImgs = ref([])
const bondLoaded = ref(false)
let bondTimer = null

// AI 问答
const chatMode = ref('oil')  // 'oil' | 'new_energy'
const chatMessages = ref([
  { role: 'bot', content: '您好！我是油价与新能源领域的 AI 专家。请问有什么可以帮您分析的？' }
])
const chatInput = ref('')
const chatLoading = ref(false)
const chatRef = ref(null)

// ── 加载分析结果 ──
async function loadAnalytics() {
  if (!props.selectedRunId) return
  loading.value = true
  try {
    const data = await fetchAnalytics(props.selectedRunId)
    analytics.value = data

    // 实盘预测大卡
    if (data.future_forecast && data.future_forecast.length > 0) {
      const r = data.future_forecast[0]
      futureRow.value = {
        predPrice: r.Pred_Price != null ? Number(r.Pred_Price).toFixed(2) : '--',
        dateText: r.Date || '--',
      }
      futureRows.value = data.future_forecast
      futureCols.value = Object.keys(data.future_forecast[0] || {})
    } else {
      futureRow.value = null
    }

    // daily
    if (data.daily_predictions) {
      dailyRows.value = data.daily_predictions
      dailyCols.value = Object.keys(data.daily_predictions[0] || {})
    }

    // pred
    if (data.prediction_results) {
      predRows.value = data.prediction_results
      predCols.value = Object.keys(data.prediction_results[0] || {})
      hasPredResults.value = true
    }

    // driver
    if (data.driver_factors) {
      driverRows.value = data.driver_factors
      driverCols.value = ['feature', 'spearman_corr_with_return', 'rf_importance', 'spearman_pvalue']
        .filter(c => c in (data.driver_factors[0] || {}))
    }

    // risk
    if (data.risk_signals) {
      riskRows.value = data.risk_signals
      riskCols.value = Object.keys(data.risk_signals[0] || {})
      // RiskLevel 分布
      const dist = {}
      data.risk_signals.forEach(r => {
        const l = r.RiskLevel
        if (l !== undefined) dist[l] = (dist[l] || 0) + 1
      })
      riskLevelDist.value = dist
      // 方向准确率
      const withDir = data.risk_signals.filter(r => r.TrueDirection !== undefined && r.PredDirection !== undefined)
      if (withDir.length) {
        const correct = withDir.filter(r => r.TrueDirection === r.PredDirection).length
        directionAcc.value = (correct / withDir.length * 100).toFixed(1) + '%'
      }
    }

    // backtest metrics
    if (data.backtest_metrics) {
      const m = data.backtest_metrics
      btMetrics.value = {
        strategy_total: fmtPct(m.Strategy_TotalReturn),
        buyhold_total: fmtPct(m.BuyHold_TotalReturn),
        max_drawdown: fmtPct(m.Strategy_MaxDrawdown),
        win_rate: fmtPct(m.Strategy_WinRate),
      }
    }

    // backtest results
    if (data.backtest_results) {
      btRows.value = data.backtest_results.slice(-50)
      btCols.value = Object.keys(data.backtest_results[0] || {})
    }

    // 图片
    predImgs.value = buildImgList(data.images, ['future_forecast.png', 'gru_predictions.png', 'gru_returns.png'], props.selectedRunId)
    explainImgs.value = buildImgList(data.images, ['direction_confusion_matrix.png', 'top_drivers_spearman.png', 'top_drivers_rf_importance.png'], props.selectedRunId)
    backtestImgs.value = buildImgList(data.images, ['backtest_nav_curve.png'], props.selectedRunId)

    // 银行报告
    bankReport.value = data.bank_report || ''

    // run.log
    hasOilPred.value = !!data.has_oil_pred

    // 拉日志
    try {
      const log = await fetchRunLog(props.selectedRunId)
      runLogContent.value = typeof log === 'string' ? log : (log?.content || '')
    } catch(e) {}

    // 拉新能源结果
    loadNeLatest()
    // 拉绿债结果
    loadBondLatest()

  } catch (e) {
    // 静默
  } finally {
    loading.value = false
  }
}

function fmtPct(v) {
  if (v === undefined || v === null) return '--'
  return (Number(v) * 100).toFixed(2) + '%'
}

function buildImgList(images, names, runId) {
  if (!images) {
    // 直接用下载 URL
    return names.map(n => ({
      name: n,
      url: `/api/oil/runs/${runId}/download?filename=${n}`
    }))
  }
  return names
    .filter(n => images.includes(n))
    .map(n => ({
      name: n,
      url: `/api/oil/runs/${runId}/download?filename=${n}`
    }))
}

// ── AI 报告 ──
async function genAIReport() {
  generatingReport.value = true
  try {
    const r = await generateAIReport(props.selectedRunId)
    bankReport.value = r.report || r.content || bankReport.value
  } catch(e) {}
  generatingReport.value = false
}

// ── 新能源 ──
function onNeDrop(e) {
  neIsDragging.value = false
  const f = e.dataTransfer.files[0]
  if (f) neFile.value = f
}
function onNeFile(e) {
  neFile.value = e.target.files[0] || null
}

async function runNewEnergy() {
  if (!neFile.value) return
  neRunning.value = true
  try {
    const fd = new FormData()
    fd.append('new_energy_zip_file', neFile.value)
    fd.append('series', neSeries.value)
    fd.append('conf_level', neConf.value)
    fd.append('scale_oil_return', neScale.value)
    fd.append('make_viz', neMakeViz.value)
    fd.append('rebuild_returns', neRebuild.value)
    await startNewEnergy(props.selectedRunId, fd)
    neTimer = setInterval(checkNe, 2000)
  } catch(e) {
    neRunning.value = false
  }
}

async function checkNe() {
  try {
    const data = await fetchNewEnergyLatest(props.selectedRunId)
    neLog.value = data.log || ''
    if (data.status === 'done' || data.images) {
      neRunning.value = false
      clearInterval(neTimer)
      neImgs.value = (data.images || []).map(n => ({
        name: n,
        url: `/api/oil/runs/${props.selectedRunId}/new-energy/download?filename=${n}`
      }))
      neLoaded.value = true
    }
  } catch(e) {}
}

async function loadNeLatest() {
  try {
    const data = await fetchNewEnergyLatest(props.selectedRunId)
    if (data.images && data.images.length) {
      neImgs.value = data.images.map(n => ({
        name: n,
        url: `/api/oil/runs/${props.selectedRunId}/new-energy/latest/download?filename=${n}`
      }))
      neLoaded.value = true
    }
  } catch(e) {}
}

// ── 绿债 ──
function onBondFile(e) {
  bondFile.value = e.target.files[0] || null
}

async function runBond() {
  bondRunning.value = true
  try {
    const fd = new FormData()
    if (bondFile.value) fd.append('bond_zip_file', bondFile.value)
    await startBond(props.selectedRunId, fd)
    bondTimer = setInterval(checkBond, 2000)
  } catch(e) {
    bondRunning.value = false
  }
}

async function checkBond() {
  try {
    const data = await fetchBondLatest(props.selectedRunId)
    bondLog.value = data.log || ''
    if (data.status === 'done' || data.rows) {
      bondRunning.value = false
      clearInterval(bondTimer)
      if (data.rows) {
        bondRows.value = data.rows
        bondCols.value = ['Date_target', 'NewEnergy_MeanPred', 'NewEnergy_Sigma', 'RiskLevel']
          .filter(c => c in (data.rows[0] || {}))
      }
      bondImgs.value = (data.images || []).map(n => ({
        name: n,
        url: `/api/oil/runs/${props.selectedRunId}/bond/latest/download?filename=${n}`
      }))
      bondLoaded.value = true
    }
  } catch(e) {}
}

async function loadBondLatest() {
  try {
    const data = await fetchBondLatest(props.selectedRunId)
    if (data.rows && data.rows.length) {
      bondRows.value = data.rows
      bondCols.value = ['Date_target', 'NewEnergy_MeanPred', 'NewEnergy_Sigma', 'RiskLevel']
        .filter(c => c in (data.rows[0] || {}))
      bondImgs.value = (data.images || []).map(n => ({
        name: n,
        url: `/api/oil/runs/${props.selectedRunId}/bond/latest/download?filename=${n}`
      }))
      bondLoaded.value = true
    }
  } catch(e) {}
}

// ── AI 问答 ──
async function sendChat() {
  if (!chatInput.value.trim() || chatLoading.value) return
  const q = chatInput.value.trim()
  chatInput.value = ''
  chatMessages.value.push({ role: 'user', content: q })
  chatLoading.value = true
  await nextTick()
  if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  try {
    const r = await sendAIChat({
      mode: chatMode.value,
      prompt: q,
      run_id: props.selectedRunId,
    })
    chatMessages.value.push({ role: 'bot', content: r?.answer || '（无回复）' })
  } catch(e) {
    chatMessages.value.push({ role: 'bot', content: '请求失败：' + (e?.message || '网络错误') })
  } finally {
    chatLoading.value = false
    await nextTick()
    if (chatRef.value) chatRef.value.scrollTop = chatRef.value.scrollHeight
  }
}

watch(() => props.selectedRunId, (v) => {
  if (v) loadAnalytics()
})

onMounted(() => {
  if (props.selectedRunId) loadAnalytics()
})
</script>
