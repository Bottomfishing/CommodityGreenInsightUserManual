<template>
  <div class="home-page">
    <!-- ══════════════════════════════════════════════════
         顶部贯穿导航栏
         ══════════════════════════════════════════════════ -->
    <header class="top-nav">
      <!-- 左侧品牌 -->
      <div class="nav-brand">
        <div class="brand-icon">
          <svg
            width="22"
            height="22"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
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
          <span class="stat-val">{{ systemBusy ? "运行中" : "空闲" }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <svg
            class="stat-icon"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <path
              d="M22 19a2 2 0 01-2 2H4a2 2 0 01-2-2V5a2 2 0 012-2h5l2 3h9a2 2 0 012 2z"
            />
          </svg>
          <span class="stat-label">当前目录</span>
          <span class="stat-val stat-val--mono">{{ currentPath }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <svg
            class="stat-icon"
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
            <circle cx="12" cy="12" r="10" />
            <polyline points="12 6 12 12 16 14" />
          </svg>
          <span class="stat-label">启动时间</span>
          <span class="stat-val stat-val--mono">{{ uptime }}</span>
        </div>
        <div class="stat-divider"></div>
        <div class="stat-item">
          <span class="stat-dot stat-dot--blue"></span>
          <span class="stat-label">历史运行</span>
          <span class="stat-val stat-val--success">{{ runCount }}</span>
        </div>
      </div>

      <!-- 右侧搜索 + 用户 -->
      <div class="nav-right">
        <div class="search-box" :class="{ focused: searchFocused }">
          <svg
            class="search-icon"
            width="15"
            height="15"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
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
          <svg
            width="14"
            height="14"
            viewBox="0 0 24 24"
            fill="none"
            stroke="currentColor"
            stroke-width="2"
            stroke-linecap="round"
            stroke-linejoin="round"
          >
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
      <section class="page-heading">
        <div class="page-heading-inner">
          <div class="heading-lines">
            <span class="heading-line heading-line--left"></span>
            <div class="heading-text">
              <h1 class="heading-title">大宗绿测综合数据</h1>
              <dv-decoration-5 class="heading-decoration" />
            </div>
            <span class="heading-line heading-line--right"></span>
          </div>
        </div>
      </section>

      <nav class="page-tabs">
        <button
          v-for="tab in pageTabs"
          :key="tab.key"
          class="page-tab-btn"
          :class="{ active: activePage === tab.key }"
          @click="activePage = tab.key"
        >
          {{ tab.label }}
        </button>
      </nav>

      <template v-if="activePage === 'dashboard'">
      <!-- 顶部装饰线 -->
      <dv-decoration-5 class="dashboard-top-line" />

      <!-- 核心指标行 -->
      <div class="kpi-row">
        <div class="kpi-card kpi--oil">
          <dv-border-box-8 style="width: 100%; height: 100%">
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
          <dv-border-box-8 style="width: 100%; height: 100%">
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
          <dv-border-box-8 style="width: 100%; height: 100%">
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
          <dv-border-box-8 style="width: 100%; height: 100%">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">AI 洞察</span>
                <span class="kpi-live"
                  ><i class="live-dot live-dot--green"></i> Active</span
                >
              </div>
              <div class="kpi-price">94.7%</div>
              <div class="kpi-change kpi-change--ai">GRU+LSTM</div>
              <div class="kpi-sub">Bullish Brent · Hold Green Bond</div>
            </div>
          </dv-border-box-8>
        </div>
      </div>

      <!-- 主要内容区域：左侧功能区 + 右侧监控区 -->
      <div class="main-content-grid">
        <!-- 左侧：Bento Grid 功能区 -->
        <div class="left-section">
          <div class="bento-grid">
            <!-- AI 助手大卡片 -->
            <div class="bento-card bento-card--large">
              <dv-border-box-1 style="width: 100%; height: 100%">
                <div class="bento-inner bento-ai">
                  <div class="bento-icon ai-icon">
                    <svg
                      width="28"
                      height="28"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path
                        d="M12 2a10 10 0 1 0 10 10 4 4 0 0 1-5-5 4 4 0 0 1-5-5"
                      />
                      <path d="M8.5 8.5v.01" />
                      <path d="M16 15.5v.01" />
                      <path d="M12 12v.01" />
                      <path d="M11 17v.01" />
                      <path d="M7 14v.01" />
                    </svg>
                  </div>
                  <div class="bento-title">AI 助手</div>
                  <div class="bento-desc">智能问答 · 数据分析 · 报告生成</div>
                  <button
                    class="bento-btn bento-btn--primary"
                    @click="openAIChat"
                  >
                    <svg
                      width="14"
                      height="14"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="2"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path
                        d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"
                      />
                    </svg>
                    开始对话
                  </button>
                </div>
              </dv-border-box-1>
            </div>

            <!-- 上传数据 -->
            <div class="bento-card">
              <dv-border-box-8 style="width: 100%; height: 100%">
                <div class="bento-inner bento-upload" @click="handleUpload">
                  <div class="bento-icon upload-icon">
                    <svg
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                      <polyline points="17 8 12 3 7 8" />
                      <line x1="12" y1="3" x2="12" y2="15" />
                    </svg>
                  </div>
                  <div class="bento-title">上传数据</div>
                  <div class="bento-desc">CSV / Excel / JSON</div>
                </div>
              </dv-border-box-8>
            </div>

            <!-- 开始训练 -->
            <div class="bento-card">
              <dv-border-box-8 style="width: 100%; height: 100%">
                <div class="bento-inner bento-train" @click="startTraining">
                  <div class="bento-icon train-icon">
                    <svg
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <polygon
                        points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"
                      />
                    </svg>
                  </div>
                  <div class="bento-title">开始训练</div>
                  <div class="bento-desc">GRU / LSTM 模型</div>
                </div>
              </dv-border-box-8>
            </div>

            <!-- 训练监控 -->
            <div class="bento-card">
              <dv-border-box-8 style="width: 100%; height: 100%">
                <div class="bento-inner bento-monitor">
                  <div class="bento-icon monitor-icon">
                    <svg
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                      <line x1="8" y1="21" x2="16" y2="21" />
                      <line x1="12" y1="17" x2="12" y2="21" />
                    </svg>
                  </div>
                  <div class="bento-title">训练监控</div>
                  <div class="bento-status">
                    <span class="status-dot status-dot--idle"></span>
                    <span>空闲</span>
                  </div>
                  <div class="mini-progress">
                    <div class="mini-bar" style="width: 0%"></div>
                  </div>
                </div>
              </dv-border-box-8>
            </div>

            <!-- 结果显示 -->
            <div class="bento-card bento-card--clickable" @click="goToResults">
              <dv-border-box-8 style="width: 100%; height: 100%">
                <div class="bento-inner bento-results">
                  <div class="bento-icon result-icon">
                    <svg
                      width="22"
                      height="22"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      stroke-width="1.8"
                      stroke-linecap="round"
                      stroke-linejoin="round"
                    >
                      <path
                        d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"
                      />
                      <polyline points="14 2 14 8 20 8" />
                      <line x1="16" y1="13" x2="8" y2="13" />
                      <line x1="16" y1="17" x2="8" y2="17" />
                      <polyline points="10 9 9 9 8 9" />
                    </svg>
                  </div>
                  <div class="bento-title">结果预览</div>
                  <div class="bento-desc">点击查看详情 →</div>
                  <div class="result-preview">
                    <span class="rp-item">MAE: 0.023</span>
                    <span class="rp-item">RMSE: 0.041</span>
                  </div>
                </div>
              </dv-border-box-8>
            </div>
          </div>
        </div>

        <!-- 右侧：监控区域 -->
        <div class="right-section">
          <!-- 飞线图区域 -->
          <div class="flyline-row">
            <dv-border-box-1 style="width: 100%; height: 100%">
              <div class="flyline-inner">
                <div class="flyline-head">
                  <div class="panel-title-row">
                    <span class="panel-tag">NETWORK</span>
                    <span class="panel-title">数据流向监控</span>
                  </div>
                  <span class="panel-live"><i class="live-dot"></i> LIVE</span>
                </div>
                <div class="flyline-area">
                  <dv-flyline-chart-enhanced
                    :config="flylineConfig"
                    style="width: 100%; height: 230px"
                  />
                </div>
              </div>
            </dv-border-box-1>
          </div>

          <!-- 实时数据监控 -->
          <div class="monitor-row">
            <dv-border-box-1 style="width: 100%; height: 100%">
              <div class="panel-inner">
                <div class="panel-head">
                  <div class="panel-title-row">
                    <span class="panel-tag">DATA</span>
                    <span class="panel-title">实时数据监控</span>
                  </div>
                  <span class="panel-live"><i class="live-dot"></i> LIVE</span>
                </div>
                <div class="data-table-area">
                  <dv-scroll-board
                    :config="scrollConfig"
                    style="width: 100%; height: 100%"
                  />
                </div>
              </div>
            </dv-border-box-1>
          </div>
        </div>
      </div>

      <!-- 底部装饰线 -->
      <dv-decoration-5 class="dashboard-bottom-line" />
      </template>

      <section v-else class="feature-panel">
        <dv-border-box-1 style="width: 100%; height: 100%">
          <div class="feature-panel-inner">
            <h2 class="feature-title">{{ currentTabTitle }}</h2>
            <p class="feature-desc">{{ currentTabDesc }}</p>

            <div v-if="activePage === 'run'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">RUN CONFIG</span>
                <span class="module-head-title">运行配置面板</span>
              </div>
              <dv-decoration-3 class="module-head-line" />
              <div class="form-grid">
                <label class="field">
                  <span>数据 ZIP</span>
                  <input type="file" accept=".zip" @change="onRunFileSelected" />
                </label>
                <label class="field">
                  <span>TopN</span>
                  <input v-model.number="runForm.topN" type="number" min="1" />
                </label>
                <label class="field">
                  <span>Epochs</span>
                  <input v-model.number="runForm.epochs" type="number" min="1" />
                </label>
                <label class="field">
                  <span>预测步长</span>
                  <input v-model.number="runForm.forecastSteps" type="number" min="1" />
                </label>
                <label class="field">
                  <span>截止日期（可选）</span>
                  <input v-model="runForm.cutoffDate" type="date" />
                </label>
                <label class="checkbox-field">
                  <input v-model="runForm.enableEarlyStopping" type="checkbox" />
                  <span>启用早停</span>
                </label>
              </div>
              <div class="feature-actions">
                <button class="feature-btn feature-btn--primary" :disabled="runLoading" @click="submitRun">
                  {{ runLoading ? "启动中..." : "开始运行" }}
                </button>
                <button class="feature-btn" :disabled="!selectedRunId || runLoading" @click="stopCurrentRun">
                  停止当前运行
                </button>
              </div>
            </div>

            <div v-else-if="activePage === 'monitor'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">MONITOR</span>
                <span class="module-head-title">训练监控面板</span>
              </div>
              <dv-decoration-3 class="module-head-line" />
              <div class="monitor-mode-row">
                <label class="radio-item"><input v-model="monitorMode" type="radio" value="selected" /> 监控已选 Run</label>
                <label class="radio-item"><input v-model="monitorMode" type="radio" value="latest" /> 监控最新 Run</label>
                <label class="radio-item"><input v-model="monitorMode" type="radio" value="manual" /> 手动输入 RunId</label>
              </div>
              <label v-if="monitorMode === 'manual'" class="field">
                <span>手动 RunId</span>
                <input v-model.trim="manualRunId" type="text" placeholder="run_YYYYMMDD_HHMMSS_topN" />
              </label>
              <div class="form-grid">
                <label class="field">
                  <span>选择 run</span>
                  <select v-model="selectedRunId">
                    <option value="">自动选择最新</option>
                    <option v-for="run in runList" :key="run.run_id" :value="run.run_id">
                      {{ run.run_id }}（{{ run.status || "unknown" }}）
                    </option>
                  </select>
                </label>
              </div>
              <div class="feature-actions">
                <button class="feature-btn feature-btn--primary" :disabled="monitorLoading" @click="refreshMonitor">
                  刷新监控
                </button>
                <label class="checkbox-field checkbox-inline">
                  <input v-model="monitorAutoRefresh" type="checkbox" />
                  <span>自动刷新</span>
                </label>
                <label class="field inline-field">
                  <span>间隔(秒)</span>
                  <input v-model.number="monitorRefreshSec" type="number" min="2" max="15" :disabled="!monitorAutoRefresh" />
                </label>
              </div>
              <div class="monitor-status-grid">
                <div class="status-chip">training_log.csv: {{ fileStatuses.trainingLog }}</div>
                <div class="status-chip">prediction_results.csv: {{ fileStatuses.predResults }}</div>
                <div class="status-chip">run.log: {{ fileStatuses.runLog }}</div>
              </div>
              <div class="data-block">
                <h3>Loss 曲线（实时）</h3>
                <div v-if="!hasLossSeries" class="chart-empty">暂无 Loss 数据</div>
                <div v-else ref="lossChartRef" class="chart-box"></div>
              </div>
              <div class="data-block">
                <h3>价格对比曲线（实时）</h3>
                <div v-if="!hasPriceSeries" class="chart-empty">暂无价格对比数据</div>
                <div v-else ref="priceChartRef" class="chart-box"></div>
              </div>
              <div class="data-block">
                <h3>收益对比曲线（实时）</h3>
                <div v-if="!hasReturnSeries" class="chart-empty">暂无收益对比数据</div>
                <div v-else ref="returnChartRef" class="chart-box"></div>
              </div>
              <div class="data-block">
                <h3>训练面板</h3>
                <pre>{{ dashboardPreview }}</pre>
              </div>
              <div class="data-block">
                <h3>运行日志</h3>
                <pre>{{ logText || "暂无日志" }}</pre>
              </div>
            </div>

            <div v-else-if="activePage === 'results'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">RESULTS</span>
                <span class="module-head-title">结果预览面板</span>
              </div>
              <dv-decoration-3 class="module-head-line" />
              <div class="feature-actions">
                <button class="feature-btn feature-btn--primary" :disabled="resultsLoading" @click="refreshResults">
                  刷新结果
                </button>
                <button class="feature-btn" :disabled="resultsLoading || !selectedRunId" @click="generateReport">
                  生成 AI 报告
                </button>
              </div>
              <div class="data-block">
                <h3>概览</h3>
                <pre>{{ overviewPreview }}</pre>
              </div>
              <div class="data-block">
                <h3>分析指标</h3>
                <pre>{{ analyticsPreview }}</pre>
              </div>
              <div class="data-block">
                <h3>AI 报告</h3>
                <pre>{{ aiReportText || "暂无报告" }}</pre>
              </div>
            </div>

            <div v-else-if="activePage === 'download'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">EXPORT</span>
                <span class="module-head-title">下载导出面板</span>
              </div>
              <dv-decoration-3 class="module-head-line" />
              <div class="feature-actions">
                <button class="feature-btn feature-btn--primary" :disabled="filesLoading" @click="refreshFiles">
                  刷新文件列表
                </button>
                <button class="feature-btn" :disabled="!selectedRunId" @click="exportZip">
                  下载整包 ZIP
                </button>
              </div>
              <div class="file-list">
                <button
                  v-for="file in runFiles"
                  :key="file.name || file"
                  class="file-item"
                  @click="downloadFile(file.name || file)"
                >
                  {{ file.name || file }}
                </button>
                <p v-if="!runFiles.length" class="empty-text">暂无可下载文件</p>
              </div>
            </div>

            <div class="feature-actions">
              <button class="feature-btn" @click="activePage = 'dashboard'">返回总览</button>
            </div>
          </div>
        </dv-border-box-1>
      </section>
    </main>

    <HomeAiDrawer
      :open="aiChatOpen"
      :loading="aiChatLoading"
      :input="aiChatInput"
      :messages="aiChatMessages"
      @update:open="aiChatOpen = $event"
      @update:input="aiChatInput = $event"
      @send="sendDashboardAIMessage"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed, watch, nextTick } from "vue";
import { useRouter } from "vue-router";
import { clearToken } from "../api/auth";
import worldMap from "../assets/world-map.svg";
import HomeAiDrawer from "../components/home/HomeAiDrawer.vue";
import { useMonitorDashboard } from "../composables/useMonitorDashboard";
import {
  createOilRun,
  fetchAnalytics,
  fetchFiles,
  fetchOverview,
  fetchRunList,
  fetchRunLog,
  fetchSystemStatus,
  fetchTrainingDashboard,
  generateAIReport,
  getZipExportUrl,
  downloadOilRunFile,
  resolveMonitor,
  sendAIChat,
  stopOilRun,
} from "../api/index";

const router = useRouter();
const username = localStorage.getItem("username") || "用户";
const activePage = ref<"dashboard" | "run" | "monitor" | "results" | "download">("dashboard");
const pageTabs = [
  { key: "dashboard", label: "总览" },
  { key: "run", label: "运行配置" },
  { key: "monitor", label: "训练监控" },
  { key: "results", label: "结果预览" },
  { key: "download", label: "下载导出" },
] as const;
const pageMeta: Record<(typeof pageTabs)[number]["key"], { title: string; desc: string }> = {
  dashboard: { title: "总览大屏", desc: "核心行情、功能入口与实时数据监控。" },
  run: { title: "运行配置", desc: "配置数据上传、模型参数与任务启动流程。" },
  monitor: { title: "训练监控", desc: "查看任务状态、训练进度与运行日志。" },
  results: { title: "结果预览", desc: "查看指标结果、图表表现与分析摘要。" },
  download: { title: "下载导出", desc: "导出报告、图表和模型输出文件。" },
};
const currentTabTitle = computed(() => pageMeta[activePage.value].title);
const currentTabDesc = computed(() => pageMeta[activePage.value].desc);
const currentPath = computed(() => `/home/${activePage.value}`);
const systemBusy = ref(false);
const runList = ref<any[]>([]);
const selectedRunId = ref("");

const runForm = reactive({
  topN: 50,
  epochs: 100,
  forecastSteps: 15,
  cutoffDate: "",
  enableEarlyStopping: true,
  autoBondAfterOil: false,
});
const selectedRunFile = ref<File | null>(null);
const runLoading = ref(false);
const monitorLoading = ref(false);
const resultsLoading = ref(false);
const filesLoading = ref(false);
const logText = ref("");
const dashboardData = ref<any>(null);
const overviewData = ref<any>(null);
const analyticsData = ref<any>(null);
const aiReportText = ref("");
const runFiles = ref<any[]>([]);
let refreshTimer: number | undefined;
const monitorMode = ref<"selected" | "latest" | "manual">("selected");
const manualRunId = ref("");
const monitorAutoRefresh = ref(true);
const monitorRefreshSec = ref(3);
const fileStatuses = reactive({
  trainingLog: "未知",
  predResults: "未知",
  runLog: "未知",
});
const aiChatOpen = ref(false);
const aiChatInput = ref("");
const aiChatLoading = ref(false);
const aiChatMessages = ref<{ role: "user" | "bot"; content: string }[]>([
  {
    role: "bot",
    content:
      "你好，我是总览 AI 助手。你可以让我解读当前训练状态、结果指标，或给出下一步训练建议。",
  },
]);
const {
  lossChartRef,
  priceChartRef,
  returnChartRef,
  ensureEchartsReady,
  renderMonitorCharts,
  resizeCharts,
  disposeMonitorCharts,
} = useMonitorDashboard(activePage, dashboardData);
void lossChartRef;
void priceChartRef;
void returnChartRef;

const dashboardPreview = computed(() =>
  dashboardData.value ? JSON.stringify(dashboardData.value, null, 2) : "暂无训练面板数据",
);
const overviewPreview = computed(() =>
  overviewData.value ? JSON.stringify(overviewData.value, null, 2) : "暂无概览数据",
);
const analyticsPreview = computed(() =>
  analyticsData.value ? JSON.stringify(analyticsData.value, null, 2) : "暂无分析数据",
);
const runCount = computed(() => runList.value.length);
const activeMonitorRunId = computed(() => {
  if (monitorMode.value === "manual") return manualRunId.value || "";
  if (monitorMode.value === "latest") return runList.value?.[0]?.run_id || "";
  return selectedRunId.value;
});
const hasLossSeries = computed(
  () => Array.isArray(dashboardData.value?.loss_series) && dashboardData.value.loss_series.length > 0,
);
const hasPriceSeries = computed(
  () => Array.isArray(dashboardData.value?.price_series) && dashboardData.value.price_series.length > 0,
);
const hasReturnSeries = computed(
  () => Array.isArray(dashboardData.value?.return_series) && dashboardData.value.return_series.length > 0,
);

// ===== 搜索 =====
const searchQuery = ref("");
const searchFocused = ref(false);

// ===== 时间 =====
const currentTime = ref("");
const startTime = ref(Date.now());
const uptime = computed(() => {
  const diff = Math.floor((Date.now() - startTime.value) / 1000);
  const h = Math.floor(diff / 3600);
  const m = Math.floor((diff % 3600) / 60);
  const s = diff % 60;
  return `${String(h).padStart(2, "0")}:${String(m).padStart(2, "0")}:${String(s).padStart(2, "0")}`;
});

let clockTimer: number;
function updateClock() {
  const d = new Date();
  currentTime.value =
    String(d.getHours()).padStart(2, "0") +
    ":" +
    String(d.getMinutes()).padStart(2, "0") +
    ":" +
    String(d.getSeconds()).padStart(2, "0");
}

// ===== 飞线图配置 =====
const flylineConfig = reactive({
  points: [
    { name: "纽约", coordinate: [0.28, 0.35] },
    { name: "伦敦", coordinate: [0.42, 0.25] },
    { name: "上海", coordinate: [0.72, 0.45] },
    { name: "东京", coordinate: [0.82, 0.35] },
    { name: "迪拜", coordinate: [0.55, 0.55] },
    { name: "新加坡", coordinate: [0.68, 0.7] },
    { name: "北京", coordinate: [0.68, 0.3] },
  ],
  lines: [
    { source: "纽约", target: "伦敦" },
    { source: "伦敦", target: "迪拜" },
    { source: "迪拜", target: "新加坡" },
    { source: "上海", target: "东京" },
    { source: "北京", target: "上海" },
    { source: "纽约", target: "东京" },
    { source: "伦敦", target: "上海" },
  ],
  line: {
    width: 1,
    color: "#ffde93",
    orbitColor: "rgba(103, 224, 227, 0.2)",
    duration: [24, 50],
    radius: 100,
  },
  halo: {
    show: true,
    duration: [20, 30],
    color: "#fb7293",
    radius: 40,
  },
  text: {
    show: true,
    offset: [0, 15],
    color: "#ffdb5c",
    fontSize: 12,
  },
  bgImgSrc: worldMap,
  curvature: 5,
  relative: true,
});

// ===== 滚动表格数据 =====
const scrollConfig = reactive({
  header: ["标的", "最新价", "涨跌幅", "成交量", "状态"],
  data: [
    ["Brent", "$78.42", "+2.34%", "2.4M", "买入"],
    ["WTI", "$74.56", "+1.87%", "1.8M", "买入"],
    ["新能源", "3,847", "+1.82%", "862亿", "买入"],
    ["光伏", "4,126", "+0.95%", "423亿", "持有"],
    ["新能车", "2,934", "-0.42%", "312亿", "观望"],
    ["10Y 国债", "2.34%", "-2bp", "1.2万亿", "持有"],
    ["SHIBOR", "1.68%", "0bp", "-", "持有"],
    ["LPR 1Y", "3.45%", "-5bp", "-", "下降"],
  ],
  rowNum: 6,
  waitTime: 2600,
  carousel: "single",
  animation: true,
  headerBGC: "rgba(59,130,246,0.08)",
  oddRowBGC: "transparent",
  evenRowBGC: "rgba(255,255,255,0.015)",
  headerHeight: 34,
  rowHeight: 30,
  align: ["left", "right", "right", "right", "center"],
  headerFontSize: 11,
  fontSize: 11,
  color: "rgba(148,163,184,0.7)",
});

// ===== 退出 =====
function handleLogout() {
  clearToken();
  router.push({ name: "Landing" });
}

// ===== Bento 功能 =====
function openAIChat() {
  aiChatOpen.value = true;
}

async function sendDashboardAIMessage() {
  const prompt = aiChatInput.value.trim();
  if (!prompt || aiChatLoading.value) return;
  aiChatMessages.value.push({ role: "user", content: prompt });
  aiChatInput.value = "";
  aiChatLoading.value = true;

  try {
    const data = await sendAIChat({
      mode: "oil",
      prompt,
      run_id: selectedRunId.value || undefined,
    });
    aiChatMessages.value.push({
      role: "bot",
      content: data?.answer || data?.content || "已收到请求，但没有返回有效内容。",
    });
  } catch (err: any) {
    aiChatMessages.value.push({
      role: "bot",
      content: `请求失败：${err?.message || "网络异常"}`,
    });
  } finally {
    aiChatLoading.value = false;
  }
}

function handleUpload() {
  openUploadDialog();
}

function onRunFileSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  selectedRunFile.value = target.files?.[0] || null;
}

async function refreshRuns() {
  try {
    const [status, runs] = await Promise.all([fetchSystemStatus(), fetchRunList()]);
    systemBusy.value = !!status?.global_busy;
    runList.value = Array.isArray(runs) ? runs : [];
    if (!selectedRunId.value && runList.value.length) {
      selectedRunId.value = runList.value[0].run_id || "";
    }
  } catch {
    systemBusy.value = false;
  }
}


async function submitRun() {
  if (!selectedRunFile.value) {
    window.alert("请先选择 ZIP 文件");
    return;
  }
  runLoading.value = true;
  try {
    const formData = new FormData();
    formData.append("zip_file", selectedRunFile.value);
    formData.append("top_n", String(runForm.topN));
    formData.append("epochs", String(runForm.epochs));
    formData.append("forecast_steps", String(runForm.forecastSteps));
    if (runForm.cutoffDate) formData.append("cutoff_date", runForm.cutoffDate);
    formData.append("enable_early_stopping", String(runForm.enableEarlyStopping));
    formData.append("auto_bond_after_oil", String(runForm.autoBondAfterOil));

    const result = await createOilRun(formData);
    selectedRunId.value = result?.run_id || selectedRunId.value;
    activePage.value = "monitor";
    await refreshRuns();
    await refreshMonitor();
  } catch (err: any) {
    window.alert(`启动运行失败：${err?.message || "未知错误"}`);
  } finally {
    runLoading.value = false;
  }
}

async function stopCurrentRun() {
  if (!selectedRunId.value) return;
  runLoading.value = true;
  try {
    await stopOilRun(selectedRunId.value);
    await refreshRuns();
  } catch (err: any) {
    window.alert(`停止失败：${err?.message || "未知错误"}`);
  } finally {
    runLoading.value = false;
  }
}

async function refreshMonitor() {
  let runId = activeMonitorRunId.value;
  if (!runId) {
    await refreshRuns();
    runId = activeMonitorRunId.value;
    if (!runId) return;
  }

  try {
    const resolved = await resolveMonitor({
      mode: monitorMode.value,
      selected_run_id: monitorMode.value === "selected" ? selectedRunId.value || undefined : undefined,
      manual_dir: monitorMode.value === "manual" ? manualRunId.value || undefined : undefined,
    });
    if (resolved?.run_id) {
      runId = resolved.run_id;
      if (monitorMode.value !== "manual") selectedRunId.value = resolved.run_id;
    }
  } catch {
    // 后端不支持 resolve 时回退到当前前端 runId
  }

  monitorLoading.value = true;
  try {
    await ensureEchartsReady();
    const [dashboard, runLog] = await Promise.all([
      fetchTrainingDashboard(runId),
      fetchRunLog(runId, 300),
    ]);
    dashboardData.value = dashboard;
    logText.value = typeof runLog === "string" ? runLog : JSON.stringify(runLog, null, 2);
    const hasLoss = Array.isArray(dashboard?.loss_series) && dashboard.loss_series.length > 0;
    const hasPrice =
      (Array.isArray(dashboard?.price_series) && dashboard.price_series.length > 0) ||
      (Array.isArray(dashboard?.return_series) && dashboard.return_series.length > 0);
    const hasLog = !!logText.value;
    fileStatuses.trainingLog = hasLoss ? "已生成" : "未找到/为空";
    fileStatuses.predResults = hasPrice ? "已生成" : "未找到/为空";
    fileStatuses.runLog = hasLog ? "已生成" : "未找到/为空";
    await nextTick();
    renderMonitorCharts();
  } catch (err: any) {
    logText.value = `读取监控失败：${err?.message || "未知错误"}`;
  } finally {
    monitorLoading.value = false;
  }
}

async function refreshResults() {
  if (!selectedRunId.value) {
    await refreshRuns();
    if (!selectedRunId.value) return;
  }
  resultsLoading.value = true;
  try {
    const [overview, analytics] = await Promise.all([
      fetchOverview(selectedRunId.value),
      fetchAnalytics(selectedRunId.value),
    ]);
    overviewData.value = overview;
    analyticsData.value = analytics;
  } catch (err: any) {
    window.alert(`读取结果失败：${err?.message || "未知错误"}`);
  } finally {
    resultsLoading.value = false;
  }
}

async function generateReport() {
  if (!selectedRunId.value) return;
  resultsLoading.value = true;
  try {
    const data = await generateAIReport(selectedRunId.value);
    aiReportText.value = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  } catch (err: any) {
    window.alert(`生成报告失败：${err?.message || "未知错误"}`);
  } finally {
    resultsLoading.value = false;
  }
}

async function refreshFiles() {
  if (!selectedRunId.value) {
    await refreshRuns();
    if (!selectedRunId.value) return;
  }
  filesLoading.value = true;
  try {
    const files = await fetchFiles(selectedRunId.value);
    runFiles.value = Array.isArray(files) ? files : files?.items || [];
  } catch (err: any) {
    window.alert(`读取文件失败：${err?.message || "未知错误"}`);
  } finally {
    filesLoading.value = false;
  }
}

async function downloadFile(name: string) {
  if (!selectedRunId.value) return;
  try {
    await downloadOilRunFile(selectedRunId.value, name);
  } catch (err: any) {
    window.alert(`下载失败：${err?.message || "未知错误"}`);
  }
}

function exportZip() {
  if (!selectedRunId.value) return;
  window.open(getZipExportUrl(selectedRunId.value), "_blank");
}

async function handlePageChange() {
  if (activePage.value === "monitor") await refreshMonitor();
  if (activePage.value === "results") await refreshResults();
  if (activePage.value === "download") await refreshFiles();
}

function setupAutoRefresh() {
  refreshTimer = window.setInterval(async () => {
    try {
      await refreshRuns();
      if (activePage.value === "monitor" && monitorAutoRefresh.value && activeMonitorRunId.value) {
        await refreshMonitor();
      }
    } catch {
      // keep polling without interrupting UI
    }
  }, Math.max(2, monitorRefreshSec.value) * 1000);
}

async function setActivePage(page: (typeof pageTabs)[number]["key"]) {
  activePage.value = page;
  await handlePageChange();
}

async function warmupData() {
  await refreshRuns();
  await handlePageChange();
}

function cleanupTimers() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = undefined;
  }
}

function handleGlobalKeydown(event: KeyboardEvent) {
  if (event.key === "Escape" && aiChatOpen.value) {
    aiChatOpen.value = false;
  }
}

function openUploadDialog() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".zip";
  input.onchange = () => {
    if (input.files?.length) {
      selectedRunFile.value = input.files[0];
      activePage.value = "run";
    }
  };
  input.click();
}

function startTraining() {
  setActivePage("run");
}

function goToResults() {
  setActivePage("results");
}

// ===== 生命周期 =====
onMounted(() => {
  updateClock();
  clockTimer = setInterval(updateClock, 1000);
  warmupData();
  setupAutoRefresh();
  window.addEventListener("resize", resizeCharts);
  window.addEventListener("keydown", handleGlobalKeydown);
});

watch(activePage, () => {
  if (activePage.value !== "monitor") {
    disposeMonitorCharts();
  }
  handlePageChange();
});

watch(selectedRunId, () => {
  handlePageChange();
});

watch([monitorMode, manualRunId], () => {
  if (activePage.value === "monitor") refreshMonitor();
});

watch([monitorAutoRefresh, monitorRefreshSec], () => {
  cleanupTimers();
  setupAutoRefresh();
});

onBeforeUnmount(() => {
  clearInterval(clockTimer);
  cleanupTimers();
  window.removeEventListener("resize", resizeCharts);
  window.removeEventListener("keydown", handleGlobalKeydown);
  disposeMonitorCharts();
});
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
  box-shadow:
    0 2px 20px rgba(0, 0, 0, 0.3),
    0 0 60px -20px rgba(59, 130, 246, 0.06);
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
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.3;
  }
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
  font-family: "SF Mono", "Cascadia Code", "Consolas", monospace;
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
.dashboard-top-line,
.dashboard-bottom-line {
  width: 100%;
  height: 3px;
}
.dashboard-top-line { margin-bottom: 4px; }
.dashboard-bottom-line { margin-top: 8px; }

.page-heading {
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  padding: 4px 2px 2px;
}
.page-heading-inner {
  width: 100%;
}
.heading-lines {
  display: flex;
  align-items: center;
  gap: 12px;
}
.heading-line {
  flex: 1;
  height: 2px;
  position: relative;
  background: linear-gradient(90deg, transparent, rgba(103, 232, 249, 0.8));
}
.heading-line::before {
  content: "";
  position: absolute;
  top: -8px;
  width: 100%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(125, 211, 252, 0.55));
}
.heading-line::after {
  content: "";
  position: absolute;
  bottom: -8px;
  width: 72%;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(56, 189, 248, 0.45));
}
.heading-line--left {
  transform: scaleX(-1);
}
.heading-text {
  min-width: 380px;
  text-align: center;
}
.heading-title {
  font-size: 34px;
  line-height: 1.15;
  color: #f8fafc;
  font-weight: 800;
  letter-spacing: 0.06em;
  text-shadow: 0 0 18px rgba(56, 189, 248, 0.35);
}

.heading-decoration {
  width: 304px;
  height: 40px;
  margin: -2px auto 0;
}

.page-tabs {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}
.page-tab-btn {
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(15, 23, 42, 0.55);
  color: rgba(148, 163, 184, 0.8);
  padding: 6px 14px;
  border-radius: 999px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.2s;
}
.page-tab-btn:hover {
  color: #cbd5e1;
  border-color: rgba(59, 130, 246, 0.35);
}
.page-tab-btn.active {
  color: #dbeafe;
  border-color: rgba(96, 165, 250, 0.7);
  background: rgba(59, 130, 246, 0.18);
  box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.12) inset;
}

.feature-panel {
  flex: 1;
  min-height: 360px;
}
.feature-panel-inner {
  height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: flex-start;
  gap: 12px;
}
.feature-title {
  font-size: 24px;
  color: #f8fafc;
}
.feature-desc {
  color: rgba(148, 163, 184, 0.78);
  max-width: 560px;
}
.feature-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}
.feature-btn {
  border: 1px solid rgba(56, 189, 248, 0.28);
  background: rgba(7, 25, 52, 0.68);
  color: #bae6fd;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.feature-btn--primary {
  border-color: rgba(34, 211, 238, 0.55);
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.62), rgba(37, 99, 235, 0.55));
  color: #ecfeff;
  box-shadow: 0 4px 16px rgba(14, 116, 144, 0.3);
}
.feature-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.feature-btn:hover {
  border-color: rgba(34, 211, 238, 0.55);
  color: #e0f2fe;
  transform: translateY(-1px);
}
.work-panel {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  background:
    linear-gradient(180deg, rgba(8, 18, 38, 0.68), rgba(3, 9, 24, 0.72)),
    radial-gradient(circle at 90% 10%, rgba(56, 189, 248, 0.09), transparent 45%);
  box-shadow:
    inset 0 0 24px rgba(56, 189, 248, 0.05),
    0 10px 24px rgba(2, 6, 23, 0.24);
}
.module-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.module-head-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: #67e8f9;
  background: rgba(8, 145, 178, 0.18);
  border: 1px solid rgba(34, 211, 238, 0.32);
}
.module-head-title {
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
}
.module-head-line {
  width: 220px;
  height: 18px;
}
.form-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.field,
.checkbox-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: rgba(191, 219, 254, 0.92);
  font-size: 12px;
}
.checkbox-field {
  flex-direction: row;
  align-items: center;
  margin-top: 20px;
}
.checkbox-inline {
  margin-top: 0;
}
.inline-field {
  max-width: 120px;
}
.field input,
.field select {
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  background: rgba(4, 16, 38, 0.72);
  color: #e0f2fe;
  padding: 8px 10px;
  transition: all 0.2s;
}
.field input:focus,
.field select:focus {
  outline: none;
  border-color: rgba(34, 211, 238, 0.7);
  box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.12);
}
.data-block {
  width: 100%;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 8px;
  padding: 10px;
  background:
    linear-gradient(180deg, rgba(2, 12, 28, 0.8), rgba(1, 8, 20, 0.82)),
    radial-gradient(circle at 0% 0%, rgba(45, 212, 191, 0.08), transparent 40%);
}
.data-block h3 {
  margin-bottom: 8px;
  font-size: 13px;
  color: rgba(186, 230, 253, 0.98);
  letter-spacing: 0.03em;
}
.data-block pre {
  margin: 0;
  max-height: 220px;
  overflow: auto;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(226, 232, 240, 0.9);
  font-family: "Cascadia Code", "Consolas", monospace;
}
.file-list {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.file-item {
  text-align: left;
  border: 1px solid rgba(34, 211, 238, 0.24);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(8, 47, 73, 0.28), rgba(15, 23, 42, 0.5));
  color: #bae6fd;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.file-item:hover {
  border-color: rgba(45, 212, 191, 0.6);
  color: #e0f2fe;
  transform: translateY(-1px);
}
.empty-text {
  color: rgba(148, 163, 184, 0.8);
  font-size: 12px;
}
.monitor-mode-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 2px;
}
.radio-item {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: rgba(191, 219, 254, 0.92);
}
.monitor-status-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 8px;
}
.status-chip {
  border: 1px solid rgba(56, 189, 248, 0.2);
  background: linear-gradient(135deg, rgba(6, 78, 59, 0.25), rgba(8, 47, 73, 0.24));
  color: #ccfbf1;
  font-size: 11px;
  border-radius: 999px;
  padding: 6px 10px;
  text-align: center;
}
.chart-box {
  width: 100%;
  height: 220px;
  background: linear-gradient(180deg, rgba(2, 6, 23, 0.78), rgba(5, 16, 32, 0.62));
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: 8px;
}
.chart-empty {
  border: 1px dashed rgba(148, 163, 184, 0.35);
  border-radius: 8px;
  padding: 22px 12px;
  text-align: center;
  color: rgba(148, 163, 184, 0.85);
  font-size: 12px;
}
/* ─── KPI 卡片行 ─── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 14px;
  margin-bottom: 16px;
}
.kpi-card {
  min-height: 120px;
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(2, 12, 28, 0.72), rgba(1, 8, 20, 0.74)),
    radial-gradient(circle at 100% 0%, rgba(45, 212, 191, 0.08), transparent 45%);
  border: 1px solid rgba(56, 189, 248, 0.12);
  box-shadow: 0 8px 22px rgba(2, 6, 23, 0.24);
}

/* ─── 主要内容网格布局 ─── */
.main-content-grid {
  display: grid;
  grid-template-columns: 3.5fr 1.2fr;
  gap: 16px;
  margin-bottom: 16px;
  border: 1px solid rgba(56, 189, 248, 0.14);
  border-radius: 12px;
  padding: 12px;
  background:
    linear-gradient(180deg, rgba(2, 12, 28, 0.65), rgba(1, 8, 20, 0.68)),
    radial-gradient(circle at 90% 12%, rgba(56, 189, 248, 0.06), transparent 45%);
}

/* 左侧功能区 */
.left-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 右侧监控区 */
.right-section {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 飞线图区域 */
.flyline-row {
  flex: 1;
  min-height: 220px;
}

/* 实时数据监控区域 */
.monitor-row {
  flex: 2;
  min-height: 300px;
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
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.25;
  }
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
.kpi-change--up {
  color: #34d399;
}
.kpi-change--down {
  color: #f87171;
}
.kpi-change--ai {
  color: #a78bfa;
}
.kpi-sub {
  font-size: 10.5px;
  color: rgba(148, 163, 184, 0.35);
  margin-top: 6px;
}

/* ─── 飞线图行 ─── */
.flyline-row {
  height: 260px;
  flex-shrink: 0;
}
.flyline-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  padding: 14px 18px;
  position: relative;
}
.flyline-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 8px;
  flex-shrink: 0;
}
.flyline-area {
  flex: 1;
  min-height: 0;
  overflow: hidden;
}
.flyline-area :deep(.dv-flyline-chart-enhanced) {
  position: absolute !important;
  inset: 0;
}

/* ─── Bento Grid 功能区 ─── */
.bento-row {
  flex: 1;
  min-height: 320px;
}

/* ─── 底部监控行 ─── */
.monitor-row {
  height: 220px;
  flex-shrink: 0;
}

/* 通用面板 */
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
  color: #dbeafe;
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

/* 左侧占位区 → 替换为 Bento Grid */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  grid-template-rows: 1fr 1fr;
  gap: 12px;
  height: 100%;
}
.bento-card--large {
  grid-row: 1 / 3;
  grid-column: 1 / 2;
}
.bento-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.2s;
  padding: 16px;
}
.bento-inner:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}
.bento-icon {
  width: 48px;
  height: 48px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12px;
}
.ai-icon {
  background: linear-gradient(
    135deg,
    rgba(139, 92, 246, 0.15),
    rgba(59, 130, 246, 0.15)
  );
  color: #a78bfa;
  width: 56px;
  height: 56px;
  border-radius: 16px;
  box-shadow: 0 0 24px rgba(139, 92, 246, 0.1);
}
.upload-icon {
  background: rgba(34, 211, 238, 0.08);
  color: #22d3ee;
}
.train-icon {
  background: rgba(251, 191, 36, 0.08);
  color: #fbbf24;
}
.monitor-icon {
  background: rgba(52, 211, 153, 0.08);
  color: #34d399;
}
.result-icon {
  background: rgba(248, 113, 113, 0.08);
  color: #f87171;
}
.bento-title {
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: 0.02em;
  margin-bottom: 4px;
}
.bento-desc {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.4);
  letter-spacing: 0.03em;
}
.bento-ai .bento-title {
  font-size: 20px;
  margin-bottom: 6px;
}
.bento-ai .bento-desc {
  font-size: 12px;
  margin-bottom: 20px;
}
.bento-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 10px 24px;
  border-radius: 10px;
  font-size: 13px;
  font-weight: 600;
  border: none;
  cursor: pointer;
  transition: all 0.25s;
  letter-spacing: 0.02em;
}
.bento-btn--primary {
  background: linear-gradient(135deg, #6366f1, #3b82f6);
  color: rgba(255, 255, 255, 0.95);
  box-shadow: 0 4px 20px rgba(99, 102, 241, 0.3);
}
.bento-btn--primary:hover {
  box-shadow: 0 6px 28px rgba(99, 102, 241, 0.45);
  transform: translateY(-1px);
}
.bento-status {
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.4);
  margin-bottom: 10px;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
}
.status-dot--idle {
  background: rgba(148, 163, 184, 0.3);
}
.mini-progress {
  width: 60%;
  height: 3px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 2px;
  overflow: hidden;
}
.mini-bar {
  height: 100%;
  background: linear-gradient(90deg, #34d399, #22d3ee);
  border-radius: 2px;
  transition: width 0.5s;
}
.result-preview {
  display: flex;
  gap: 12px;
  margin-top: 8px;
}
.rp-item {
  font-size: 10px;
  font-family: "SF Mono", "Cascadia Code", monospace;
  color: rgba(148, 163, 184, 0.35);
  background: rgba(255, 255, 255, 0.03);
  padding: 3px 8px;
  border-radius: 5px;
}
.bento-card--clickable .bento-inner:hover {
  opacity: 0.75;
}

/* 数据表格区 */
.data-table-area {
  flex: 1;
  min-height: 0;
  border: 1px solid rgba(56, 189, 248, 0.12);
  border-radius: 8px;
  padding: 6px;
  background: rgba(2, 6, 23, 0.35);
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
  .nav-stats {
    margin-left: 20px;
  }
  .stat-item {
    padding: 6px 10px;
  }
  .brand-sub {
    display: none;
  }
  .brand-sep {
    display: none;
  }
}

@media (max-width: 900px) {
  .heading-text {
    min-width: 260px;
  }
  .heading-title {
    font-size: 24px;
  }
  .heading-line::before,
  .heading-line::after {
    display: none;
  }
  .kpi-row {
    grid-template-columns: repeat(2, 1fr);
  }
  .bento-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto;
  }
  .bento-card--large {
    grid-row: auto;
    grid-column: auto;
  }
  .flyline-row {
    height: 200px;
  }
  .monitor-row {
    height: 180px;
  }
  .nav-stats {
    display: none;
  }
  .top-nav {
    padding: 0 16px;
  }
  .main-content {
    padding: 12px 16px 16px;
  }
}

@media (max-width: 600px) {
  .heading-lines {
    gap: 8px;
  }
  .heading-text {
    min-width: 0;
    width: 100%;
  }
  .heading-line {
    display: none;
  }
  .heading-title {
    font-size: 20px;
  }
  .heading-decoration {
    width: 220px;
  }
  .kpi-row {
    grid-template-columns: 1fr;
  }
  .search-box {
    min-width: 160px;
  }
  .search-kbd {
    display: none;
  }
  .user-name {
    display: none;
  }
}
</style>
