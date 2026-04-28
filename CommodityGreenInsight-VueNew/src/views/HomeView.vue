<template>
  <div class="home-page" :class="{ 'home-page--long-page': isLongContentPage }">
    <!-- ══════════════════════════════════════════════════
         顶部贯穿导航栏
         ══════════════════════════════════════════════════ -->
    <header class="top-nav">
      <!-- 左侧品牌 -->
      <div class="nav-brand">
        <div class="brand-icon">
          <img
            class="brand-icon-img"
            src="/brand-logo.png"
            alt="大宗绿测 logo"
          />
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
            ref="searchInputRef"
            v-model="searchQuery"
            type="text"
            placeholder="搜索功能、数据、报告..."
            @focus="searchFocused = true"
            @blur="searchFocused = false"
            @keydown.enter.prevent="handleSearchSubmit"
            @keydown.esc.prevent="clearSearch"
          />
          <kbd class="search-kbd">{{ searchShortcutLabel }}</kbd>
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
    <main
      ref="mainContentRef"
      class="main-content"
      :class="{ 'main-content--long-page': isLongContentPage }"
    >
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
          v-for="tab in filteredPageTabs"
          :key="tab.key"
          class="page-tab-btn"
          :class="{ active: activePage === tab.key }"
          @click="setActivePage(tab.key)"
        >
          {{ tab.label }}
        </button>
        <span v-if="searchQuery.trim() && !filteredPageTabs.length" class="page-tab-empty">无匹配功能</span>
      </nav>

      <template v-if="activePage === 'dashboard'">
      <!-- 核心指标行 -->
      <div class="kpi-row">
        <div class="kpi-card kpi--oil">
          <div class="box8-shell">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">Brent Crude</span>
                <span class="kpi-live"><i class="live-dot"></i> LIVE</span>
              </div>
              <div class="kpi-price">$78.42</div>
              <div class="kpi-change kpi-change--up">+2.34%</div>
              <div class="kpi-sub">Vol: 2.4M · $76.8 - $79.2</div>
            </div>
          </div>
        </div>

        <div class="kpi-card kpi--energy">
          <div class="box8-shell">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">CSI 新能源</span>
                <span class="kpi-badge kpi-badge--up">+1.4%</span>
              </div>
              <div class="kpi-price">3,847</div>
              <div class="kpi-change kpi-change--up">+1.82%</div>
              <div class="kpi-sub">光伏 4,126 · 新能源车 2,934</div>
            </div>
          </div>
        </div>

        <div class="kpi-card kpi--bond">
          <div class="box8-shell">
            <div class="kpi-inner">
              <div class="kpi-label-row">
                <span class="kpi-tag">10Y 国债</span>
                <span class="kpi-badge kpi-badge--stable">Stable</span>
              </div>
              <div class="kpi-price">2.34%</div>
              <div class="kpi-change kpi-change--down">-2bp</div>
              <div class="kpi-sub">SHIBOR 1.68% · LPR 3.45%</div>
            </div>
          </div>
        </div>

        <div class="kpi-card kpi--ai">
          <div class="box8-shell">
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
          </div>
        </div>
      </div>

      <!-- 主要内容区域：左侧功能区 + 右侧监控区 -->
      <div class="main-content-grid">
        <!-- 左侧：重构功能区 -->
        <div class="left-section">
          <div class="left-top-row">
            <div class="action-squares-row">
              <div class="bento-card action-square">
                <dv-border-box-13 style="width: 100%; height: 100%">
                  <div class="box8-shell">
                  <div class="bento-inner bento-train" @click="startTraining">
                    <div class="bento-icon train-icon">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2" />
                      </svg>
                    </div>
                    <div class="bento-title">开始训练</div>
                    <div class="bento-desc">GRU / LSTM 模型</div>
                  </div>
                  </div>
                </dv-border-box-13>
              </div>
              <div class="bento-card action-square">
                <dv-border-box-13 style="width: 100%; height: 100%">
                  <div class="box8-shell">
                  <div class="bento-inner bento-monitor" @click="goToMonitor">
                    <div class="bento-icon monitor-icon">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <rect x="2" y="3" width="20" height="14" rx="2" ry="2" />
                        <line x1="8" y1="21" x2="16" y2="21" />
                        <line x1="12" y1="17" x2="12" y2="21" />
                      </svg>
                    </div>
                    <div class="bento-title">训练监控</div>
                    <div class="bento-desc">实时进度 / 日志</div>
                  </div>
                  </div>
                </dv-border-box-13>
              </div>
              <div class="bento-card action-square bento-card--clickable" @click="goToResults">
                <dv-border-box-13 style="width: 100%; height: 100%">
                  <div class="box8-shell">
                  <div class="bento-inner bento-results">
                    <div class="bento-icon result-icon">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
                        <polyline points="14 2 14 8 20 8" />
                        <line x1="16" y1="13" x2="8" y2="13" />
                        <line x1="16" y1="17" x2="8" y2="17" />
                        <polyline points="10 9 9 9 8 9" />
                      </svg>
                    </div>
                    <div class="bento-title">结果分析</div>
                    <div class="bento-desc">点击查看详情</div>
                  </div>
                  </div>
                </dv-border-box-13>
              </div>
              <div class="bento-card action-square">
                <dv-border-box-13 style="width: 100%; height: 100%">
                  <div class="box8-shell">
                  <div class="bento-inner bento-upload" @click="goToDownload">
                    <div class="bento-icon upload-icon">
                      <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
                        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4" />
                        <polyline points="17 8 12 3 7 8" />
                        <line x1="12" y1="3" x2="12" y2="15" />
                      </svg>
                    </div>
                    <div class="bento-title">下载导出</div>
                    <div class="bento-desc">报告 / 图表 / ZIP</div>
                  </div>
                  </div>
                </dv-border-box-13>
              </div>
            </div>
          </div>
          <div class="left-candle-row">
            <div class="left-candle-square">
              <dv-border-box-1 style="width: 100%; height: 100%">
                <div class="panel-inner panel-inner--tight">
                  <div class="panel-head panel-head--stack">
                    <div class="panel-title-row">
                      <span class="panel-tag">WTI</span>
                      <span class="panel-title">近20周蜡烛图</span>
                    </div>
                    <div class="panel-subtitle panel-subtitle--small">
                      数据来源：FRED WTI 现货（MySQL）｜截止：{{ wtiCandleLatestDate || "暂无" }}
                    </div>
                  </div>
                  <div ref="wtiCandleChartRef" class="candle-chart-box"></div>
                </div>
              </dv-border-box-1>
            </div>
            <div class="ai-mini-card">
              <dv-border-box-1 style="width: 100%; height: 100%">
                <div class="bento-inner bento-ai-mini">
                  <div class="bento-icon ai-icon">
                    <img
                      class="ai-icon-img"
                      src="/assistant-avatar.png"
                      alt="新手助手小绿头像"
                    />
                  </div>
                  <div class="bento-title">新手助手小绿</div>
                  <button class="bento-btn bento-btn--primary bento-btn--mini" @click="openAIChat">对话</button>
                </div>
              </dv-border-box-1>
            </div>
          </div>
        </div>

        <!-- 中间：Globe -->
        <div class="center-section">
          <div class="center-globe-card">
            <div class="globe-shell">
              <ReactGlobePanel />
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

      </template>

      <section v-else class="feature-panel">
        <div class="feature-panel-frame">
          <div class="feature-panel-inner">
            <div class="feature-title-row">
              <h2 class="feature-title">{{ currentTabTitle }}</h2>
              <span v-if="latestModelTrainingRunning" class="feature-title-hint">
                您的模型正在训练中，可以先观看我们模型的可视化
              </span>
            </div>
            <p class="feature-desc">{{ currentTabDesc }}</p>

            <RunPanel
              v-if="activePage === 'run'"
              :run-form="runForm"
              :run-loading="runLoading"
              :selected-run-id="selectedRunId"
              @file-selected="onRunFileSelected"
              @submit="submitRun"
              @stop="stopCurrentRun"
            />

            <div v-else-if="activePage === 'monitor'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">MONITOR</span>
                <span class="module-head-title">训练监控面板</span>
              </div>
              <dv-decoration-3 class="module-head-line" />
              <div class="monitor-mode-row">
                <label class="radio-item"><input v-model="monitorMode" type="radio" value="default" /> 监控我们的模型</label>
                <label class="radio-item"><input v-model="monitorMode" type="radio" value="latest" /> 监控您最新训练的模型</label>
                <label class="radio-item"><input v-model="monitorMode" type="radio" value="history" /> 查看您的模型</label>
              </div>
              <div v-if="monitorMode === 'history'" class="form-grid">
                <label class="field">
                  <span>历史模型（Run）</span>
                  <select v-model="selectedRunId">
                    <option value="">请选择您的历史模型</option>
                    <option v-for="run in runList" :key="`history-${run.run_id}`" :value="run.run_id">
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
              <div class="monitor-progress">
                <div class="monitor-progress-head">
                  <span>训练进度</span>
                  <span>{{ monitorProgressLabel }}</span>
                </div>
                <div class="monitor-progress-track">
                  <div class="monitor-progress-fill" :style="{ width: `${monitorProgressPct}%` }"></div>
                </div>
              </div>
              <div class="data-block">
                <h3>Loss 曲线（实时）</h3>
                <div v-if="!hasLossSeries" class="chart-empty">暂无 Loss 数据</div>
                <div v-else ref="lossChartRef" class="chart-box"></div>
              </div>
              <div v-if="showMonitorCompletionCharts" class="data-block">
                <h3>价格对比曲线（训练完获得）</h3>
                <div v-if="!hasPriceSeries" class="chart-empty">暂无价格对比数据</div>
                <div v-else ref="priceChartRef" class="chart-box"></div>
              </div>
              <div v-if="showMonitorCompletionCharts" class="data-block">
                <h3>收益对比曲线（训练完获得）</h3>
                <div v-if="!hasReturnSeries" class="chart-empty">暂无收益对比数据</div>
                <div v-else ref="returnChartRef" class="chart-box"></div>
              </div>
              <div v-else class="chart-empty">
                您的模型训练中：价格对比曲线与收益对比曲线将在训练完成后自动生成并展示。
              </div>
              <div class="data-block">
                <h3>训练面板</h3>
                <div v-if="!dashboardData" class="chart-empty">暂无训练面板数据</div>
                <div v-else class="train-dashboard">
                  <div class="train-metrics">
                    <div class="train-metric-card">
                      <span class="train-metric-label">Run ID</span>
                      <strong class="train-metric-value train-metric-value--mono">{{ dashboardMeta.runId }}</strong>
                    </div>
                    <div class="train-metric-card">
                      <span class="train-metric-label">Epoch 数</span>
                      <strong class="train-metric-value">{{ dashboardMeta.totalEpochs }}</strong>
                    </div>
                    <div class="train-metric-card">
                      <span class="train-metric-label">最新 Loss</span>
                      <strong class="train-metric-value">{{ dashboardMeta.latestLoss }}</strong>
                    </div>
                    <div class="train-metric-card">
                      <span class="train-metric-label">最新 Val Loss</span>
                      <strong class="train-metric-value">{{ dashboardMeta.latestValLoss }}</strong>
                    </div>
                  </div>
                  <div v-if="dashboardLossRows.length" class="train-loss-table-wrap">
                    <table class="train-loss-table">
                      <thead>
                        <tr>
                          <th>Epoch</th>
                          <th>Loss</th>
                          <th>Val Loss</th>
                        </tr>
                      </thead>
                      <tbody>
                        <tr v-for="row in dashboardLossRows" :key="row.epoch">
                          <td>{{ row.epoch }}</td>
                          <td>{{ row.loss }}</td>
                          <td>{{ row.valLoss }}</td>
                        </tr>
                      </tbody>
                    </table>
                  </div>
                  <div v-else class="chart-empty">暂无 Loss 明细数据</div>
                </div>
              </div>
              <div class="data-block">
                <h3>运行日志</h3>
                <div v-if="!logText" class="chart-empty">暂无日志</div>
                <div v-else class="log-columns">
                  <pre class="log-terminal-pre">{{ logText }}</pre>
                </div>
              </div>
            </div>

            <ResultsPanel
              v-else-if="activePage === 'results'"
              :loading="resultsLoading"
              :selected-run-id="selectedRunId"
              :result-charts-data="resultChartsData"
              :overview-preview="overviewPreview"
              :analytics-preview="analyticsPreview"
              :ai-report-text="aiReportText"
              :training-hint="resultsTrainingHint"
              @refresh="refreshResults"
              @generate="generateReport"
            />

            <DownloadPanel
              v-else-if="activePage === 'download'"
              :loading="filesLoading"
              :selected-run-id="selectedRunId"
              :files="runFiles"
              @refresh="refreshFiles"
              @export="exportZip"
              @download="downloadFile"
            />

            <div v-else-if="activePage === 'greenStock'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">GREEN STOCK</span>
                <span class="module-head-title">绿色股票预测（新能源整合）</span>
              </div>
              <dv-decoration-3 class="module-head-line" />

              <div class="data-block">
                <h3>运行选择</h3>
                <label class="field">
                  <span>选择 oil run_id（需已生成 prediction_results.csv）</span>
                  <select v-model="selectedRunId">
                    <option value="">自动选择最新</option>
                    <option v-for="run in runList" :key="run.run_id" :value="run.run_id">
                      {{ run.run_id }}（{{ run.status || "unknown" }}）
                    </option>
                  </select>
                </label>
              </div>

              <div class="data-block">
                <h3>数据与参数</h3>
                <div class="form-grid">
                  <label class="field">
                    <span>新能源数据 ZIP（可选，不上传则使用默认绿色股票指数）</span>
                    <input type="file" accept=".zip" @change="onGreenStockZipSelected" />
                  </label>
                  <label class="field">
                    <span>置信水平</span>
                    <select v-model.number="greenStockConfig.confLevel">
                      <option :value="0.9">0.90</option>
                      <option :value="0.95">0.95</option>
                      <option :value="0.99">0.99</option>
                    </select>
                  </label>
                  <label class="field">
                    <span>油收益缩放（×）</span>
                    <input v-model.number="greenStockConfig.scaleOilReturn" type="number" step="1" min="1" max="1000" />
                  </label>
                </div>
                <div class="feature-actions">
                  <label class="checkbox-field checkbox-inline">
                    <input v-model="greenStockConfig.makeViz" type="checkbox" />
                    <span>生成可视化</span>
                  </label>
                  <label class="checkbox-field checkbox-inline">
                    <input v-model="greenStockConfig.rebuildReturns" type="checkbox" />
                    <span>重建收益序列</span>
                  </label>
                </div>
              </div>

              <div class="feature-actions">
                <button class="feature-btn feature-btn--primary" :disabled="greenStockLoading" @click="startGreenStockPredict">
                  {{ greenStockLoading ? "启动中..." : "启动绿色股票预测" }}
                </button>
                <button class="feature-btn" :disabled="greenStockLatestLoading" @click="refreshGreenStockLatest">
                  {{ greenStockLatestLoading ? "读取中..." : "查看最新结果" }}
                </button>
              </div>

              <div v-if="greenStockStartMsg" class="status-chip">{{ greenStockStartMsg }}</div>
              <div v-if="latestModelTrainingRunning" class="status-chip">
                您的模型正在训练中，可以线观看我们模型的可视化
              </div>

              <div class="data-block">
                <h3>最新结果预览</h3>
                <div v-if="!greenStockLatest" class="chart-empty">暂无数据，点击“查看最新结果”获取。</div>
                <template v-else>
                  <div class="data-block">
                    <h3>运行日志（tail）</h3>
                    <pre class="log-pre">{{ greenStockLatest.log_tail || greenStockLatest.error || "暂无日志" }}</pre>
                  </div>
                  <div class="data-block">
                    <h3>CSV 预览</h3>
                    <div v-if="!greenStockLatest.csv_preview?.exists" class="chart-empty">未发现输出 CSV</div>
                    <div v-else class="train-loss-table-wrap">
                      <table class="train-loss-table">
                        <thead>
                          <tr>
                            <th v-for="k in Object.keys((greenStockLatest.csv_preview.rows && greenStockLatest.csv_preview.rows[0]) || {})" :key="`ne-k-${k}`">
                              {{ k }}
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(r, idx) in (greenStockLatest.csv_preview.rows || []).slice(0, 20)" :key="`ne-r-${idx}`">
                            <td v-for="k in Object.keys((greenStockLatest.csv_preview.rows && greenStockLatest.csv_preview.rows[0]) || {})" :key="`ne-c-${idx}-${k}`">
                              {{ r[k] }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </template>
              </div>

              <div class="data-block">
                <h3>绿色股票预测图表</h3>
                <div
                  v-if="!greenStockLatest?.chart_csv_previews && !(greenStockLatest?.csv_preview?.rows?.length)"
                  class="chart-empty"
                >
                  暂无图表数据，请先“查看最新结果”。
                </div>
                <div v-else class="ne-chart-grid">
                  <div class="ne-chart-card">
                    <div class="chart-title">均值预测与置信区间</div>
                    <div ref="neCiChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">Sigma 与风险阈值</div>
                    <div ref="neSigmaChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">风险等级分布</div>
                    <div ref="neRiskChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">CI 宽度分布</div>
                    <div ref="neCiWidthChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">收益均值分布</div>
                    <div ref="neMeanHistChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">Lambda-Sigma 散点</div>
                    <div ref="neScatterChartRef" class="ne-chart-box"></div>
                  </div>
                </div>
              </div>
            </div>

            <div v-else-if="activePage === 'greenBond'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">GREEN BOND</span>
                <span class="module-head-title">绿色债券预测（Bond from GRU）</span>
              </div>
              <dv-decoration-3 class="module-head-line" />

              <div class="data-block">
                <h3>运行选择</h3>
                <label class="field">
                  <span>选择 oil run_id（需已生成 oil_pred.csv）</span>
                  <select v-model="selectedRunId">
                    <option value="">自动选择最新</option>
                    <option v-for="run in runList" :key="run.run_id" :value="run.run_id">
                      {{ run.run_id }}（{{ run.status || "unknown" }}）
                    </option>
                  </select>
                </label>
              </div>

              <div class="data-block">
                <h3>数据输入</h3>
                <label class="field">
                  <span>绿债数据 ZIP（可选，不上传则走默认数据）</span>
                  <input type="file" accept=".zip" @change="onGreenBondZipSelected" />
                </label>
              </div>

              <div class="feature-actions">
                <button class="feature-btn feature-btn--primary" :disabled="greenBondLoading" @click="startGreenBondPredict">
                  {{ greenBondLoading ? "启动中..." : "启动绿色债券预测" }}
                </button>
                <button class="feature-btn" :disabled="greenBondLatestLoading" @click="refreshGreenBondLatest">
                  {{ greenBondLatestLoading ? "读取中..." : "查看最新结果" }}
                </button>
              </div>

              <div v-if="greenBondStartMsg" class="status-chip">{{ greenBondStartMsg }}</div>
              <div v-if="latestModelTrainingRunning" class="status-chip">
                您的模型正在训练中，可以线观看我们模型的可视化
              </div>

              <div class="data-block">
                <h3>最新结果预览</h3>
                <div v-if="!greenBondLatest" class="chart-empty">暂无数据，点击“查看最新结果”获取。</div>
                <template v-else>
                  <div class="data-block">
                    <h3>运行日志（tail）</h3>
                    <pre class="log-pre">{{ greenBondLatest.log_tail || greenBondLatest.error || "暂无日志" }}</pre>
                  </div>
                  <div class="data-block">
                    <h3>CSV 预览</h3>
                    <div v-if="!greenBondLatest.csv_preview?.exists" class="chart-empty">
                      {{ greenBondLatest.error || "未发现输出 CSV" }}
                    </div>
                    <div v-else class="train-loss-table-wrap">
                      <table class="train-loss-table">
                        <thead>
                          <tr>
                            <th v-for="k in Object.keys((greenBondLatest.csv_preview.rows && greenBondLatest.csv_preview.rows[0]) || {})" :key="`bond-k-${k}`">
                              {{ k }}
                            </th>
                          </tr>
                        </thead>
                        <tbody>
                          <tr v-for="(r, idx) in (greenBondLatest.csv_preview.rows || []).slice(0, 20)" :key="`bond-r-${idx}`">
                            <td v-for="k in Object.keys((greenBondLatest.csv_preview.rows && greenBondLatest.csv_preview.rows[0]) || {})" :key="`bond-c-${idx}-${k}`">
                              {{ r[k] }}
                            </td>
                          </tr>
                        </tbody>
                      </table>
                    </div>
                  </div>
                </template>
              </div>

              <div class="data-block">
                <h3>绿色债券预测图表</h3>
                <div
                  v-if="!greenBondLatest?.chart_csv_previews && !(greenBondLatest?.csv_preview?.rows?.length)"
                  class="chart-empty"
                >
                  暂无图表数据，请先“查看最新结果”。
                </div>
                <div v-else class="ne-chart-grid">
                  <div class="ne-chart-card">
                    <div class="chart-title">均值预测与置信区间</div>
                    <div ref="bondCiChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">Sigma 与风险阈值</div>
                    <div ref="bondSigmaChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">风险等级分布</div>
                    <div ref="bondRiskChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">CI 宽度分布</div>
                    <div ref="bondCiWidthChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">收益均值分布</div>
                    <div ref="bondMeanHistChartRef" class="ne-chart-box"></div>
                  </div>
                  <div class="ne-chart-card">
                    <div class="chart-title">Lambda-Sigma 散点</div>
                    <div ref="bondScatterChartRef" class="ne-chart-box"></div>
                  </div>
                </div>
              </div>

            </div>

            <div v-else-if="activePage === 'live'" class="work-panel">
              <div class="module-head">
                <span class="module-head-tag">LIVE</span>
                <span class="module-head-title">实盘预测</span>
              </div>
              <dv-decoration-3 class="module-head-line" />
              <div class="form-grid">
                <label class="field">
                  <span>历史 Run</span>
                  <select v-model="liveWeightsRunId">
                    <option value="">默认权重（全局）</option>
                    <option v-for="run in runList" :key="`live-run-${run.run_id}`" :value="run.run_id">
                      {{ run.run_id }}（{{ run.status || "unknown" }}）
                    </option>
                  </select>
                </label>
                <label class="field">
                  <span>权重文件</span>
                  <select v-model="liveWeightsName" :disabled="!liveWeightsRunId || liveWeightsOptions.length === 0">
                    <option value="">自动选择（该 run 最新 .h5）</option>
                    <option v-for="name in liveWeightsOptions" :key="`live-weight-${name}`" :value="name">
                      {{ name }}
                    </option>
                  </select>
                </label>
              </div>
              <div class="feature-actions">
                <button class="feature-btn feature-btn--primary" :disabled="livePredictLoading" @click="runLivePredict">
                  <template v-if="livePredictLoading">
                    <span class="btn-loading">
                      <i class="btn-loading-spinner" aria-hidden="true"></i>
                      推理中...
                    </span>
                  </template>
                  <template v-else>开始实盘推理（仅推理）</template>
                </button>
                <button class="feature-btn" :disabled="livePredictLoading" @click="liveAdvancedOpen = !liveAdvancedOpen">
                  {{ liveAdvancedOpen ? "收起高级" : "高级实盘" }}
                </button>
              </div>
              <div v-if="liveAdvancedOpen" class="data-block">
                <h3>高级实盘（上传自定义数据集）</h3>
                <div class="form-grid">
                  <label class="field">
                    <span>数据集文件（csv/xlsx，需包含 close 列）</span>
                    <input type="file" accept=".csv,.xlsx,.xls" @change="onLiveDatasetSelected" />
                  </label>
                </div>
                <div class="feature-actions">
                  <button
                    class="feature-btn feature-btn--primary"
                    :disabled="livePredictLoading || !liveDatasetFile"
                    @click="runLivePredictAdvanced"
                  >
                    <template v-if="livePredictLoading">
                      <span class="btn-loading">
                        <i class="btn-loading-spinner" aria-hidden="true"></i>
                        推理中...
                      </span>
                    </template>
                    <template v-else>使用自定义数据集推理</template>
                  </button>
                  <span class="chart-empty" style="min-height: 40px; padding: 0 10px;">
                    {{ liveDatasetFile ? `已选择：${liveDatasetFile.name}` : "尚未选择文件" }}
                  </span>
                </div>
              </div>
              <div class="data-block">
                <h3>推理结果</h3>
                <div v-if="!livePredictResult" class="chart-empty">暂无结果，请点击“开始实盘推理（仅推理）”。</div>
                <div v-else-if="livePredictResult.error" class="chart-empty">{{ livePredictResult.error }}</div>
                <div v-else>
                  <div class="live-hero-card">
                    <div class="live-hero-label">明日预测价格</div>
                    <div class="live-hero-price">
                      ${{ Number(livePredictResult.pred_price || 0).toFixed(3) }}
                    </div>
                    <div class="live-hero-sub">
                      相比最新价 ${{ Number(livePredictResult.last_price || 0).toFixed(3) }}
                      · 预测收益 {{ Number(livePredictResult.pred_denoised_return || 0).toFixed(6) }}
                    </div>
                  </div>
                  <div class="live-metrics-grid">
                    <div class="live-metric-item"><span>上涨概率</span><strong>{{ livePredictResult.pred_prob_up ?? "--" }}</strong></div>
                    <div class="live-metric-item"><span>置信度</span><strong>{{ livePredictResult.true_vs_denoised_confidence }}</strong></div>
                    <div class="live-metric-item"><span>窗口长度</span><strong>{{ livePredictResult.window_len }}</strong></div>
                    <div class="live-metric-item"><span>模式</span><strong>{{ livePredictResult.mode }}</strong></div>
                  </div>
                  <div class="chart-empty" style="text-align:left; margin-top: 10px;">
                    权重：<span style="word-break: break-all">{{ livePredictResult.weights_file }}</span>
                  </div>
                </div>
              </div>
            </div>

            <div class="feature-actions">
              <button class="feature-btn" @click="activePage = 'dashboard'">返回总览</button>
            </div>
          </div>
        </div>
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
import ReactGlobePanel from "../components/home/ReactGlobePanel.vue";
import { useMonitorDashboard } from "../composables/useMonitorDashboard";
import RunPanel from "../components/home/RunPanel.vue";
import ResultsPanel from "../components/home/ResultsPanel.vue";
import DownloadPanel from "../components/home/DownloadPanel.vue";
import {
  createOilRun,
  fetchAnalytics,
  fetchDefaultResultCharts,
  fetchResultCharts,
  fetchFiles,
  fetchOverview,
  fetchRunList,
  fetchRunLog,
  fetchSystemStatus,
  fetchWtiSpotLast20,
  fetchLiveWtiPredict,
  fetchLiveWtiPredictAdvanced,
  fetchTrainingDashboard,
  generateAIReport,
  getZipExportUrl,
  downloadOilRunFile,
  startNewEnergy,
  fetchNewEnergyLatest,
  startBond,
  fetchBondLatest,
  resolveMonitor,
  sendAIChat,
  stopOilRun,
} from "../api/index";

const router = useRouter();
const username = localStorage.getItem("username") || "用户";
const activePage = ref<
  | "dashboard"
  | "run"
  | "monitor"
  | "results"
  | "download"
  | "greenStock"
  | "greenBond"
  | "live"
>("dashboard");
const pageTabs = [
  { key: "dashboard", label: "总览" },
  { key: "run", label: "训练您的模型" },
  { key: "monitor", label: "训练监控" },
  { key: "results", label: "结果预览" },
  { key: "download", label: "下载导出" },
  { key: "greenStock", label: "绿色股票预测" },
  { key: "greenBond", label: "绿色债券预测" },
  { key: "live", label: "实盘预测" },
] as const;
type PageTabKey = (typeof pageTabs)[number]["key"];
const pageMeta: Record<(typeof pageTabs)[number]["key"], { title: string; desc: string }> = {
  dashboard: { title: "总览大屏", desc: "核心行情、功能入口与实时数据监控。" },
  run: { title: "训练您的模型(时间可能较长)", desc: "配置数据上传、模型参数与任务启动流程。" },
  monitor: { title: "训练监控（因为是深度学习训练时间可能较长，您可以后台运行等待）", desc: "查看任务状态、训练进度与运行日志。" },
  results: { title: "结果预览", desc: "查看指标结果、图表表现与分析摘要。" },
  download: { title: "下载导出", desc: "导出报告、图表和模型输出文件。" },
  greenStock: { title: "绿色股票预测", desc: "基于油价因子与多维特征的绿色股票收益/风险预测。" },
  greenBond: { title: "绿色债券预测", desc: "基于油价因子与利率环境的绿色债券收益/风险预测。" },
  live: { title: "实盘预测", desc: "实时拉取行情并输出下一步预测与风险提示，可选择您的模型的权重文件，用您训练好的模型进行推理。" },
};
const currentTabTitle = computed(() => pageMeta[activePage.value].title);
const currentTabDesc = computed(() => pageMeta[activePage.value].desc);
const currentPath = computed(() => `/home/${activePage.value}`);
const isLongContentPage = computed(() =>
  ["monitor", "results", "greenStock", "greenBond"].includes(activePage.value),
);
const mainContentRef = ref<HTMLElement | null>(null);
const systemBusy = ref(false);
const runList = ref<any[]>([]);
const selectedRunId = ref("");

const runForm = reactive({
  modelName: "",
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
const resultChartsData = ref<any>(null);
const aiReportText = ref("");
const runFiles = ref<any[]>([]);
const livePredictLoading = ref(false);
const livePredictResult = ref<any>(null);
const liveWeightsRunId = ref("");
const liveWeightsName = ref("");
const liveWeightsOptions = ref<string[]>([]);
const liveAdvancedOpen = ref(false);
const liveDatasetFile = ref<File | null>(null);

// ===== 绿色股票（新能源整合预测）=====
const greenStockZipFile = ref<File | null>(null);
const greenStockLoading = ref(false);
const greenStockLatestLoading = ref(false);
const greenStockStartMsg = ref("");
const greenStockLatest = ref<any>(null);
const greenStockConfig = reactive({
  series: "new_energy",
  confLevel: 0.95,
  scaleOilReturn: 100.0,
  makeViz: true,
  rebuildReturns: false,
});
const neCiChartRef = ref<HTMLDivElement | null>(null);
const neSigmaChartRef = ref<HTMLDivElement | null>(null);
const neRiskChartRef = ref<HTMLDivElement | null>(null);
const neCiWidthChartRef = ref<HTMLDivElement | null>(null);
const neMeanHistChartRef = ref<HTMLDivElement | null>(null);
const neScatterChartRef = ref<HTMLDivElement | null>(null);
let neCiChart: any = null;
let neSigmaChart: any = null;
let neRiskChart: any = null;
let neCiWidthChart: any = null;
let neMeanHistChart: any = null;
let neScatterChart: any = null;
// ===== 绿色债券预测 =====
const greenBondZipFile = ref<File | null>(null);
const greenBondLoading = ref(false);
const greenBondLatestLoading = ref(false);
const greenBondStartMsg = ref("");
const greenBondLatest = ref<any>(null);
const bondCiChartRef = ref<HTMLDivElement | null>(null);
const bondSigmaChartRef = ref<HTMLDivElement | null>(null);
const bondRiskChartRef = ref<HTMLDivElement | null>(null);
const bondCiWidthChartRef = ref<HTMLDivElement | null>(null);
const bondMeanHistChartRef = ref<HTMLDivElement | null>(null);
const bondScatterChartRef = ref<HTMLDivElement | null>(null);
let bondCiChart: any = null;
let bondSigmaChart: any = null;
let bondRiskChart: any = null;
let bondCiWidthChart: any = null;
let bondMeanHistChart: any = null;
let bondScatterChart: any = null;
let refreshTimer: number | undefined;
const DEFAULT_MONITOR_RUN_ID = "默认数据";
const monitorMode = ref<"default" | "latest" | "history">("default");
const monitorAutoRefresh = ref(true);
const monitorRefreshSec = ref(3);
const latestTrainingWasRunning = ref(false);
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
      "你好，我是新手助手小绿。你可以让我解读当前训练状态、结果指标，我也可以跟你讲解怎么使用大宗绿测web。",
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
const wtiCandleChartRef = ref<HTMLDivElement | null>(null);
const wtiCandleData = ref<any[]>([]);
const wtiCandleSource = ref<string>("");
const wtiCandleLatestDate = ref<string>("");
let wtiCandleChart: any = null;

function buildDefaultMonitorPayload() {
  const dates = Array.from({ length: 24 }, (_, i) => `T${String(i + 1).padStart(2, "0")}`);
  const loss_series = dates.map((_, i) => ({
    epoch: i + 1,
    loss: Number((1.08 * Math.exp(-i / 10) + 0.035 * Math.sin(i / 2.2) + 0.06).toFixed(6)),
    val_loss: Number((1.16 * Math.exp(-i / 11) + 0.04 * Math.cos(i / 2.5) + 0.08).toFixed(6)),
  }));
  const price_series = dates.map((d, i) => {
    const base = 72 + i * 0.18 + Math.sin(i / 2.6) * 0.9;
    return {
      Date_target: d,
      Actual_P_t_plus_H: Number(base.toFixed(4)),
      GRU_Pred_P_t_plus_H: Number((base + Math.sin(i / 3.1) * 0.18).toFixed(4)),
    };
  });
  const return_series = price_series.map((r: any, i: number, arr: any[]) => {
    if (i === 0) return { Date_target: r.Date_target, Actual_Return: 0, GRU_Pred_Return: 0 };
    const prev = arr[i - 1].Actual_P_t_plus_H || 1;
    const predPrev = arr[i - 1].GRU_Pred_P_t_plus_H || 1;
    return {
      Date_target: r.Date_target,
      Actual_Return: Number((((r.Actual_P_t_plus_H - prev) / prev) * 100).toFixed(4)),
      GRU_Pred_Return: Number((((r.GRU_Pred_P_t_plus_H - predPrev) / predPrev) * 100).toFixed(4)),
    };
  });
  return {
    run_id: "default-preview",
    loss_series,
    price_series,
    return_series,
    run_log_tail: [
      "[default] monitor preview mode",
      "Epoch 24/24 - loss: 0.0623 - val_loss: 0.0819",
      "No active training task. Showing default dashboard.",
    ].join("\n"),
    is_log_active: false,
    is_recently_started: false,
  };
}

function buildDefaultResultChartsPayload() {
  const idx = Array.from({ length: 36 }, (_, i) => i + 1);
  const prices = idx.map((i) => 70 + i * 0.16 + Math.sin(i / 3) * 0.8);
  const predPrices = prices.map((v, i) => v + Math.cos(i / 4) * 0.22);
  const trainLoss = idx.slice(0, 24).map((i) => 1.06 * Math.exp(-i / 10) + 0.06);
  const valLoss = idx.slice(0, 24).map((i) => 1.12 * Math.exp(-i / 10.5) + 0.085);
  const returns = prices.map((v, i) => (i === 0 ? 0 : (v - prices[i - 1]) / prices[i - 1]));
  const predReturns = predPrices.map((v, i) => (i === 0 ? 0 : (v - predPrices[i - 1]) / predPrices[i - 1]));
  const residuals = returns.map((v, i) => v - predReturns[i]);
  return {
    run_id: "default-preview",
    charts: {
      test_predictions: {
        exists: true,
        file: "chart_test_predictions.csv",
        rows: idx.map((x, i) => ({
          test_index: x,
          actual_price: Number(prices[i].toFixed(4)),
          pred_price: Number(predPrices[i].toFixed(4)),
          actual_return: Number(returns[i].toFixed(6)),
          pred_return: Number(predReturns[i].toFixed(6)),
        })),
      },
      train_val_loss: {
        exists: true,
        file: "chart_train_val_loss.csv",
        rows: trainLoss.map((v, i) => ({
          epoch: i + 1,
          train_loss: Number(v.toFixed(6)),
          val_loss: Number(valLoss[i].toFixed(6)),
        })),
      },
      return_scatter: {
        exists: true,
        file: "chart_return_scatter.csv",
        rows: returns.slice(1).map((v, i) => ({
          y_true: Number(v.toFixed(6)),
          y_pred: Number(predReturns[i + 1].toFixed(6)),
        })),
      },
      residual_distribution: {
        exists: true,
        file: "chart_residual_distribution.csv",
        rows: residuals.slice(1).map((v, i) => ({
          sample_index: i + 1,
          residual: Number(v.toFixed(6)),
        })),
      },
      direction_prediction: {
        exists: true,
        file: "chart_direction_prediction.csv",
        rows: returns.slice(1).map((v, i) => ({
          sample_index: i + 1,
          true_direction: v >= 0 ? 1 : 0,
          pred_direction: predReturns[i + 1] >= 0 ? 1 : 0,
        })),
      },
      direction_confusion_matrix: {
        exists: true,
        file: "chart_direction_confusion_matrix.csv",
        rows: [
          { true_label: "down", pred_label: "down", count: 9 },
          { true_label: "down", pred_label: "up", count: 2 },
          { true_label: "up", pred_label: "down", count: 1 },
          { true_label: "up", pred_label: "up", count: 12 },
        ],
      },
      direction_prob_distribution: {
        exists: true,
        file: "chart_direction_prob_distribution.csv",
        rows: returns.slice(1).map((v, i) => ({
          sample_index: i + 1,
          prob_up: Number((0.5 + v * 12).toFixed(4)),
        })),
      },
      backtest_nav_curve: {
        exists: true,
        file: "chart_backtest_nav_curve.csv",
        rows: idx.map((x, i) => ({
          test_index: x,
          strategy_nav: Number((1 + i * 0.008 + Math.sin(i / 6) * 0.01).toFixed(6)),
          buy_hold_nav: Number((1 + i * 0.004 + Math.cos(i / 8) * 0.008).toFixed(6)),
        })),
      },
      vmd_before_after: {
        exists: true,
        file: "chart_vmd_before_after.csv",
        rows: idx.map((x, i) => ({
          sample_index: x,
          before: Number((returns[i] * 100).toFixed(6)),
          after: Number((predReturns[i] * 100).toFixed(6)),
        })),
      },
    },
  };
}

function withDefaultResultCharts(payload: any) {
  const fallback = buildDefaultResultChartsPayload();
  const source = payload && typeof payload === "object" ? payload : {};
  const sourceCharts = source.charts && typeof source.charts === "object" ? source.charts : {};
  const mergedCharts: Record<string, any> = { ...fallback.charts };
  for (const key of Object.keys(sourceCharts)) {
    const rows = Array.isArray(sourceCharts[key]?.rows) ? sourceCharts[key].rows : [];
    if (rows.length) mergedCharts[key] = sourceCharts[key];
  }
  return { ...fallback, ...source, charts: mergedCharts };
}

const overviewPreview = computed(() =>
  overviewData.value ? JSON.stringify(overviewData.value, null, 2) : "暂无概览数据",
);
const analyticsPreview = computed(() =>
  analyticsData.value ? JSON.stringify(analyticsData.value, null, 2) : "暂无分析数据",
);
function formatMetricNumber(value: unknown): string {
  if (typeof value !== "number" || Number.isNaN(value)) return "--";
  return Math.abs(value) >= 1 ? value.toFixed(4) : value.toFixed(6);
}
const dashboardMeta = computed(() => {
  const data = dashboardData.value || {};
  const lossSeries = Array.isArray(data.loss_series) ? data.loss_series : [];
  const last = lossSeries.length ? lossSeries[lossSeries.length - 1] : {};
  return {
    runId: data.run_id || activeMonitorRunId.value || "--",
    totalEpochs: lossSeries.length,
    latestLoss: formatMetricNumber(last?.loss),
    latestValLoss: formatMetricNumber(last?.val_loss),
  };
});
const dashboardLossRows = computed(() => {
  const series = Array.isArray(dashboardData.value?.loss_series)
    ? dashboardData.value.loss_series
    : [];
  return series.slice(-12).reverse().map((item: any, index: number) => ({
    epoch: item?.epoch ?? `#${index + 1}`,
    loss: formatMetricNumber(item?.loss),
    valLoss: formatMetricNumber(item?.val_loss),
  }));
});
const runCount = computed(() => runList.value.length);
const latestRunId = computed(() => String(runList.value?.[0]?.run_id || ""));
const latestRunStatus = computed(() => String(runList.value?.[0]?.status || "").toLowerCase());
const activeMonitorRunId = computed(() => {
  if (monitorMode.value === "default") return DEFAULT_MONITOR_RUN_ID;
  if (monitorMode.value === "latest") return runList.value?.[0]?.run_id || "";
  return selectedRunId.value || "";
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
const activeRunStatus = computed(() => {
  const rid = activeMonitorRunId.value;
  if (!rid) return "";
  const hit = runList.value.find((r: any) => String(r?.run_id || "") === rid);
  return String(hit?.status || "").toLowerCase();
});
const latestModelTrainingRunning = computed(
  () =>
    monitorMode.value === "latest" &&
    !!latestRunId.value &&
    (latestRunStatus.value === "running" || systemBusy.value),
);
const showMonitorCompletionCharts = computed(() => !latestModelTrainingRunning.value);
const resultsTrainingHint = computed(() =>
  latestModelTrainingRunning.value ? "您的模型正在训练中，可以线观看我们模型的可视化" : "",
);
const effectiveMonitorTargetEpochs = computed(() => {
  // 优先从日志解析“最终生效训练参数: epochs=xx”，避免 Optuna 覆盖后进度条显示 9/100 这种错觉。
  const text = String(logText.value || "");
  const m = text.match(/最终生效训练参数:\s*epochs\s*=\s*(\d+)/);
  if (m?.[1]) {
    const n = Number(m[1]);
    if (Number.isFinite(n) && n > 0) return n;
  }
  return Math.max(Number(runForm.epochs || 0), 1);
});
const monitorProgressPct = computed(() => {
  const trainedEpochs = Number(dashboardMeta.value.totalEpochs || 0);
  const targetEpochs = effectiveMonitorTargetEpochs.value;
  if (trainedEpochs <= 0) return 0;
  let pct = Math.round((trainedEpochs / targetEpochs) * 100);
  if (activeRunStatus.value === "running") {
    pct = Math.min(99, Math.max(1, pct));
  } else {
    pct = Math.min(100, Math.max(1, pct));
  }
  return pct;
});
const monitorProgressLabel = computed(() => {
  if (!hasLossSeries.value) return "暂无训练数据（如果您已经开启了训练，但此进度条不动，说明目前在进行特征工程阶段，等进入模型训练阶段进度条会动，在上栏可以查看您现在是否在运行）";
  const epochs = Number(dashboardMeta.value.totalEpochs || 0);
  const target = effectiveMonitorTargetEpochs.value;
  if (activeRunStatus.value === "running") {
    return `${epochs}/${target} · 训练中 ${monitorProgressPct.value}%`;
  }
  return `${epochs}/${target} · ${monitorProgressPct.value}%`;
});

// ===== 搜索 =====
const searchQuery = ref("");
const searchFocused = ref(false);
const searchInputRef = ref<HTMLInputElement | null>(null);
const searchShortcutLabel = /Mac|iPhone|iPad|iPod/i.test(navigator.platform) ? "⌘K" : "Ctrl+K";
const pageSearchKeywords: Record<PageTabKey, string[]> = {
  dashboard: ["总览", "大屏", "首页", "dashboard", "overview", "监控台"],
  run: ["运行", "配置", "上传", "训练参数", "run", "config", "zip"],
  monitor: ["监控", "日志", "训练", "loss", "monitor", "log"],
  results: ["结果", "预览", "图表", "报告", "results", "report", "chart"],
  download: ["下载", "导出", "文件", "zip", "download", "export"],
  greenStock: ["绿色股票", "新能源", "stock", "new energy"],
  greenBond: ["绿色债券", "bond", "国债", "利率"],
  live: ["实盘", "实时", "预测", "live", "wti"],
};
const filteredPageTabs = computed(() => {
  const keyword = searchQuery.value.trim().toLowerCase();
  if (!keyword) return pageTabs;
  return pageTabs.filter((tab) => {
    const meta = pageMeta[tab.key];
    const searchText = [
      tab.label,
      meta.title,
      meta.desc,
      ...(pageSearchKeywords[tab.key] || []),
    ]
      .join(" ")
      .toLowerCase();
    return searchText.includes(keyword);
  });
});

function focusSearchInput() {
  searchFocused.value = true;
  nextTick(() => {
    searchInputRef.value?.focus();
    searchInputRef.value?.select();
  });
}

function clearSearch() {
  if (searchQuery.value.trim()) {
    searchQuery.value = "";
    return;
  }
  searchFocused.value = false;
  searchInputRef.value?.blur();
}

function handleSearchSubmit() {
  const first = filteredPageTabs.value[0];
  if (!first) return;
  setActivePage(first.key);
}

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

function onRunFileSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  selectedRunFile.value = target.files?.[0] || null;
}

function onGreenStockZipSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  greenStockZipFile.value = target.files?.[0] || null;
}

async function startGreenStockPredict() {
  let runId = activeMonitorRunId.value || selectedRunId.value || "";
  if (!runId) {
    await refreshRuns();
    runId = activeMonitorRunId.value || selectedRunId.value || "";
  }
  if (!runId) {
    window.alert("请先选择一个 run_id");
    return;
  }
  greenStockLoading.value = true;
  greenStockStartMsg.value = "";
  try {
    const formData = new FormData();
    // 后端字段：ne_zip_file / series / conf_level / scale_oil_return / make_viz / rebuild_returns
    if (greenStockZipFile.value) {
      formData.append("ne_zip_file", greenStockZipFile.value);
    }
    formData.append("series", greenStockConfig.series);
    formData.append("conf_level", String(greenStockConfig.confLevel));
    formData.append("scale_oil_return", String(greenStockConfig.scaleOilReturn));
    formData.append("make_viz", String(greenStockConfig.makeViz));
    formData.append("rebuild_returns", String(greenStockConfig.rebuildReturns));

    const res = await startNewEnergy(runId, formData);
    greenStockStartMsg.value =
      typeof res?.message === "string"
        ? res.message
        : "新能源整合预测已启动（后端已接收任务）";
  } catch (err: any) {
    window.alert(`启动绿色股票预测失败：${err?.message || "未知错误"}`);
  } finally {
    greenStockLoading.value = false;
  }
}

async function refreshGreenStockLatest() {
  const forceDefault = monitorMode.value === "default" || latestModelTrainingRunning.value;
  if (forceDefault) {
    greenStockLatestLoading.value = true;
    try {
      // 默认展示：读取 web_runs/默认数据 下的真实产物
      const latest = await fetchNewEnergyLatest(DEFAULT_MONITOR_RUN_ID, 500);
      greenStockLatest.value = latest;
      await nextTick();
      await renderGreenStockCharts();
    } catch (err: any) {
      greenStockLatest.value = { error: err?.message || "读取默认绿色股票结果失败" };
    } finally {
      greenStockLatestLoading.value = false;
    }
    return;
  }
  let runId = activeMonitorRunId.value || selectedRunId.value || "";
  if (!runId) {
    await refreshRuns();
    runId = activeMonitorRunId.value || selectedRunId.value || "";
    if (!runId) return;
  }
  greenStockLatestLoading.value = true;
  try {
    const latest = await fetchNewEnergyLatest(runId, 80);
    greenStockLatest.value = latest;
    await nextTick();
    await renderGreenStockCharts();
  } catch (err: any) {
    greenStockLatest.value = { error: err?.message || "读取失败" };
  } finally {
    greenStockLatestLoading.value = false;
  }
}

function binToHist(values: number[], bins = 16) {
  if (!values.length) return [] as { x: string; y: number }[];
  const vmin = Math.min(...values);
  const vmax = Math.max(...values);
  if (vmax <= vmin) return [{ x: `${vmin.toFixed(4)}`, y: values.length }];
  const step = (vmax - vmin) / bins;
  const arr = Array.from({ length: bins }, (_, i) => ({ x0: vmin + i * step, x1: vmin + (i + 1) * step, c: 0 }));
  for (const v of values) {
    const idx = Math.min(bins - 1, Math.max(0, Math.floor((v - vmin) / step)));
    arr[idx].c += 1;
  }
  return arr.map((b) => ({ x: `${b.x0.toFixed(3)}~${b.x1.toFixed(3)}`, y: b.c }));
}

async function renderGreenStockCharts() {
  const csvs = greenStockLatest.value?.chart_csv_previews;
  const mainRows = greenStockLatest.value?.csv_preview?.rows || [];
  await ensureEchartsReady();
  const ec = (window as any).echarts;
  if (!ec) return;

  const pickRowsBySuffix = (suffix: string) => {
    if (!csvs || typeof csvs !== "object") return [] as any[];
    const hit = Object.entries(csvs).find(([k]) => k.endsWith(suffix));
    return (hit?.[1] as any)?.rows || [];
  };
  const prefer = (a: any[], b: any[]) => (Array.isArray(a) && a.length ? a : b);

  const ciRows = prefer(pickRowsBySuffix("_chart_ci_band"), mainRows.length ? mainRows : []);
  const sigmaRows = prefer(pickRowsBySuffix("_chart_sigma"), mainRows.length ? mainRows : []);
  const riskRows = prefer(
    pickRowsBySuffix("_chart_risk_distribution"),
    mainRows.length
      ? (() => {
          const map = new Map<string, number>();
          for (const r of mainRows) {
            const lv = String((r as any).RiskLevel || "");
            if (!lv) continue;
            map.set(lv, (map.get(lv) || 0) + 1);
          }
          return Array.from(map.entries()).map(([RiskLevel, Count]) => ({
            RiskLevel,
            Count,
          }));
        })()
      : [],
  );
  const ciwRows = prefer(
    pickRowsBySuffix("_chart_ci_width_hist"),
    mainRows.length
      ? mainRows.map((r: any) => ({
          CI_width: Number(r.CI_high) - Number(r.CI_low),
        }))
      : [],
  );
  const meanRows = prefer(
    pickRowsBySuffix("_chart_meanpred_hist"),
    mainRows.length
      ? mainRows.map((r: any) => ({ NewEnergy_MeanPred: Number(r.NewEnergy_MeanPred) }))
      : [],
  );
  const scatterRows = prefer(
    pickRowsBySuffix("_chart_lambda_sigma_scatter"),
    mainRows.length
      ? mainRows.map((r: any) => ({
          Lambda_t: Number(r.Lambda_t),
          NewEnergy_Sigma: Number(r.NewEnergy_Sigma),
        }))
      : [],
  );

  const mount = (holder: HTMLDivElement | null, old: any) => {
    if (!holder) return null;
    old?.dispose?.();
    return ec.init(holder);
  };

  neCiChart = mount(neCiChartRef.value, neCiChart);
  if (neCiChart && ciRows.length) {
    const x = ciRows.map((r: any) => r.Date_target);
    neCiChart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 35, right: 12, top: 20, bottom: 26 },
      xAxis: { type: "category", data: x, axisLabel: { color: "#94a3b8", fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      series: [
        { name: "CI_low", type: "line", data: ciRows.map((r: any) => Number(r.CI_low)), lineStyle: { opacity: 0 } },
        {
          name: "CI_high",
          type: "line",
          data: ciRows.map((r: any) => Number(r.CI_high)),
          areaStyle: { color: "rgba(34,211,238,0.15)" },
          lineStyle: { opacity: 0 },
        },
        { name: "MeanPred", type: "line", smooth: true, data: ciRows.map((r: any) => Number(r.NewEnergy_MeanPred)) },
      ],
    });
  }

  neSigmaChart = mount(neSigmaChartRef.value, neSigmaChart);
  if (neSigmaChart && sigmaRows.length) {
    neSigmaChart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 35, right: 12, top: 20, bottom: 26 },
      xAxis: { type: "category", data: sigmaRows.map((r: any) => r.Date_target), axisLabel: { color: "#94a3b8", fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      series: [
        { name: "Sigma", type: "line", smooth: true, data: sigmaRows.map((r: any) => Number(r.NewEnergy_Sigma)) },
        { name: "Q50", type: "line", data: sigmaRows.map((r: any) => Number(r.Q50)), lineStyle: { type: "dashed" } },
        { name: "Q80", type: "line", data: sigmaRows.map((r: any) => Number(r.Q80)), lineStyle: { type: "dashed" } },
      ],
    });
  }

  neRiskChart = mount(neRiskChartRef.value, neRiskChart);
  if (neRiskChart && riskRows.length) {
    neRiskChart.setOption({
      tooltip: {},
      grid: { left: 30, right: 10, top: 20, bottom: 24 },
      xAxis: { type: "category", data: riskRows.map((r: any) => r.RiskLevel), axisLabel: { color: "#94a3b8" } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8" } },
      series: [{ type: "bar", data: riskRows.map((r: any) => Number(r.Count)), itemStyle: { color: "#22c55e" } }],
    });
  }

  neCiWidthChart = mount(neCiWidthChartRef.value, neCiWidthChart);
  if (neCiWidthChart && ciwRows.length) {
    const hist = binToHist(ciwRows.map((r: any) => Number(r.CI_width)).filter((v: number) => Number.isFinite(v)));
    neCiWidthChart.setOption({
      tooltip: {},
      grid: { left: 30, right: 10, top: 20, bottom: 30 },
      xAxis: { type: "category", data: hist.map((h) => h.x), axisLabel: { color: "#94a3b8", rotate: 35, fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8" } },
      series: [{ type: "bar", data: hist.map((h) => h.y), itemStyle: { color: "#38bdf8" } }],
    });
  }

  neMeanHistChart = mount(neMeanHistChartRef.value, neMeanHistChart);
  if (neMeanHistChart && meanRows.length) {
    const hist = binToHist(
      meanRows.map((r: any) => Number(r.NewEnergy_MeanPred)).filter((v: number) => Number.isFinite(v)),
    );
    neMeanHistChart.setOption({
      tooltip: {},
      grid: { left: 30, right: 10, top: 20, bottom: 30 },
      xAxis: { type: "category", data: hist.map((h) => h.x), axisLabel: { color: "#94a3b8", rotate: 35, fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8" } },
      series: [{ type: "bar", data: hist.map((h) => h.y), itemStyle: { color: "#f59e0b" } }],
    });
  }

  neScatterChart = mount(neScatterChartRef.value, neScatterChart);
  if (neScatterChart && scatterRows.length) {
    neScatterChart.setOption({
      tooltip: { trigger: "item" },
      grid: { left: 36, right: 12, top: 20, bottom: 28 },
      xAxis: { type: "value", name: "Lambda", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      yAxis: { type: "value", name: "Sigma", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      series: [
        {
          type: "scatter",
          symbolSize: 6,
          data: scatterRows
            .map((r: any) => [Number(r.Lambda_t), Number(r.NewEnergy_Sigma)])
            .filter((v: number[]) => Number.isFinite(v[0]) && Number.isFinite(v[1])),
          itemStyle: { color: "#22d3ee" },
        },
      ],
    });
  }
}

function onGreenBondZipSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  greenBondZipFile.value = target.files?.[0] || null;
}

async function startGreenBondPredict() {
  let runId = activeMonitorRunId.value || selectedRunId.value || "";
  if (!runId) {
    await refreshRuns();
    runId = activeMonitorRunId.value || selectedRunId.value || "";
  }
  if (!runId) {
    window.alert("请先选择一个 run_id");
    return;
  }
  greenBondLoading.value = true;
  greenBondStartMsg.value = "";
  try {
    const formData = new FormData();
    if (greenBondZipFile.value) {
      // 可选字段：bond_zip_file
      formData.append("bond_zip_file", greenBondZipFile.value);
    }
    const res = await startBond(runId, formData);
    greenBondStartMsg.value =
      typeof res?.message === "string" ? res.message : "绿债预测已启动（后端已接收任务）";
  } catch (err: any) {
    window.alert(`启动绿色债券预测失败：${err?.message || "未知错误"}`);
  } finally {
    greenBondLoading.value = false;
  }
}

async function refreshGreenBondLatest() {
  const forceDefault = monitorMode.value === "default" || latestModelTrainingRunning.value;
  if (forceDefault) {
    greenBondLatestLoading.value = true;
    try {
      // 默认展示：读取 web_runs/默认数据 下的真实产物
      const latest = await fetchBondLatest(DEFAULT_MONITOR_RUN_ID, 500);
      greenBondLatest.value = latest;
      await nextTick();
      await renderGreenBondCharts();
    } catch (err: any) {
      greenBondLatest.value = { error: err?.message || "读取默认绿色债券结果失败" };
    } finally {
      greenBondLatestLoading.value = false;
    }
    return;
  }
  let runId = activeMonitorRunId.value || selectedRunId.value || "";
  if (!runId) {
    await refreshRuns();
    runId = activeMonitorRunId.value || selectedRunId.value || "";
    if (!runId) return;
  }
  greenBondLatestLoading.value = true;
  try {
    const latest = await fetchBondLatest(runId, 80);
    greenBondLatest.value = latest;
    await nextTick();
    await renderGreenBondCharts();
  } catch (err: any) {
    greenBondLatest.value = { error: err?.message || "读取失败" };
  } finally {
    greenBondLatestLoading.value = false;
  }
}

async function runLivePredict() {
  livePredictLoading.value = true;
  try {
    const res = await fetchLiveWtiPredict({
      run_id: liveWeightsRunId.value || undefined,
      weights_name: liveWeightsName.value || undefined,
    });
    livePredictResult.value = res;
  } catch (err: any) {
    livePredictResult.value = { error: err?.message || "实盘推理失败" };
  } finally {
    livePredictLoading.value = false;
  }
}

function onLiveDatasetSelected(event: Event) {
  const target = event.target as HTMLInputElement;
  liveDatasetFile.value = target.files?.[0] || null;
}

async function runLivePredictAdvanced() {
  if (!liveDatasetFile.value) {
    window.alert("请先选择数据集文件（csv/xlsx）");
    return;
  }
  livePredictLoading.value = true;
  try {
    const formData = new FormData();
    formData.append("live_file", liveDatasetFile.value);
    if (liveWeightsRunId.value) formData.append("run_id", liveWeightsRunId.value);
    if (liveWeightsName.value) formData.append("weights_name", liveWeightsName.value);
    const res = await fetchLiveWtiPredictAdvanced(formData);
    livePredictResult.value = res;
  } catch (err: any) {
    livePredictResult.value = { error: err?.message || "高级实盘推理失败" };
  } finally {
    livePredictLoading.value = false;
  }
}

async function refreshLiveWeightsOptions() {
  if (!liveWeightsRunId.value) {
    liveWeightsOptions.value = [];
    liveWeightsName.value = "";
    return;
  }
  try {
    const files = await fetchFiles(liveWeightsRunId.value);
    const items = Array.isArray(files) ? files : files?.items || [];
    const names = items
      .map((item: any) => String(item?.name || item || "").trim())
      .filter((name: string) => /\.(?:weights\.)?h5$/i.test(name))
      .sort((a: string, b: string) => b.localeCompare(a));
    liveWeightsOptions.value = names;
    if (liveWeightsName.value && !names.includes(liveWeightsName.value)) {
      liveWeightsName.value = "";
    }
  } catch {
    liveWeightsOptions.value = [];
    liveWeightsName.value = "";
  }
}

async function renderGreenBondCharts() {
  const csvs = greenBondLatest.value?.chart_csv_previews;
  const mainRows = greenBondLatest.value?.csv_preview?.rows || [];
  await ensureEchartsReady();
  const ec = (window as any).echarts;
  if (!ec) return;

  const pickRowsBySuffix = (suffix: string) => {
    if (!csvs || typeof csvs !== "object") return [] as any[];
    const hit = Object.entries(csvs).find(([k]) => k.endsWith(suffix));
    return (hit?.[1] as any)?.rows || [];
  };
  const prefer = (a: any[], b: any[]) => (Array.isArray(a) && a.length ? a : b);

  const ciRows = prefer(pickRowsBySuffix("_chart_ci_band"), mainRows.length ? mainRows : []);
  const sigmaRows = prefer(pickRowsBySuffix("_chart_sigma"), mainRows.length ? mainRows : []);
  const riskRows = prefer(
    pickRowsBySuffix("_chart_risk_distribution"),
    mainRows.length
      ? (() => {
          const map = new Map<string, number>();
          for (const r of mainRows) {
            const lv = String((r as any).RiskLevel || "");
            if (!lv) continue;
            map.set(lv, (map.get(lv) || 0) + 1);
          }
          return Array.from(map.entries()).map(([RiskLevel, Count]) => ({ RiskLevel, Count }));
        })()
      : [],
  );
  const ciwRows = prefer(
    pickRowsBySuffix("_chart_ci_width_hist"),
    mainRows.length
      ? mainRows.map((r: any) => ({ CI_width: Number(r.CI_high) - Number(r.CI_low) }))
      : [],
  );
  const meanRows = prefer(
    pickRowsBySuffix("_chart_meanpred_hist"),
    mainRows.length ? mainRows.map((r: any) => ({ NewEnergy_MeanPred: Number(r.NewEnergy_MeanPred) })) : [],
  );
  const scatterRows = prefer(
    pickRowsBySuffix("_chart_lambda_sigma_scatter"),
    mainRows.length
      ? mainRows.map((r: any) => ({ Lambda_t: Number(r.Oil_GRU_z_used), NewEnergy_Sigma: Number(r.NewEnergy_Sigma) }))
      : [],
  );

  const mount = (holder: HTMLDivElement | null, old: any) => {
    if (!holder) return null;
    old?.dispose?.();
    return ec.init(holder);
  };

  bondCiChart = mount(bondCiChartRef.value, bondCiChart);
  if (bondCiChart && ciRows.length) {
    const x = ciRows.map((r: any) => r.Date_target);
    bondCiChart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 35, right: 12, top: 20, bottom: 26 },
      xAxis: { type: "category", data: x, axisLabel: { color: "#94a3b8", fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      series: [
        { name: "CI_low", type: "line", data: ciRows.map((r: any) => Number(r.CI_low)), lineStyle: { opacity: 0 } },
        { name: "CI_high", type: "line", data: ciRows.map((r: any) => Number(r.CI_high)), lineStyle: { opacity: 0 }, areaStyle: { color: "rgba(34,211,238,0.15)" } },
        { name: "MeanPred", type: "line", smooth: true, data: ciRows.map((r: any) => Number(r.NewEnergy_MeanPred)) },
      ],
    });
  }

  bondSigmaChart = mount(bondSigmaChartRef.value, bondSigmaChart);
  if (bondSigmaChart && sigmaRows.length) {
    bondSigmaChart.setOption({
      tooltip: { trigger: "axis" },
      grid: { left: 35, right: 12, top: 20, bottom: 26 },
      xAxis: { type: "category", data: sigmaRows.map((r: any) => r.Date_target), axisLabel: { color: "#94a3b8", fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      series: [
        { name: "Sigma", type: "line", smooth: true, data: sigmaRows.map((r: any) => Number(r.NewEnergy_Sigma)) },
        { name: "Q50", type: "line", data: sigmaRows.map((r: any) => Number(r.Q50)), lineStyle: { type: "dashed" } },
        { name: "Q80", type: "line", data: sigmaRows.map((r: any) => Number(r.Q80)), lineStyle: { type: "dashed" } },
      ],
    });
  }

  bondRiskChart = mount(bondRiskChartRef.value, bondRiskChart);
  if (bondRiskChart && riskRows.length) {
    bondRiskChart.setOption({
      tooltip: {},
      grid: { left: 30, right: 10, top: 20, bottom: 24 },
      xAxis: { type: "category", data: riskRows.map((r: any) => r.RiskLevel), axisLabel: { color: "#94a3b8" } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8" } },
      series: [{ type: "bar", data: riskRows.map((r: any) => Number(r.Count)), itemStyle: { color: "#22c55e" } }],
    });
  }

  bondCiWidthChart = mount(bondCiWidthChartRef.value, bondCiWidthChart);
  if (bondCiWidthChart && ciwRows.length) {
    const hist = binToHist(ciwRows.map((r: any) => Number(r.CI_width)).filter((v: number) => Number.isFinite(v)));
    bondCiWidthChart.setOption({
      tooltip: {},
      grid: { left: 30, right: 10, top: 20, bottom: 30 },
      xAxis: { type: "category", data: hist.map((h) => h.x), axisLabel: { color: "#94a3b8", rotate: 35, fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8" } },
      series: [{ type: "bar", data: hist.map((h) => h.y), itemStyle: { color: "#38bdf8" } }],
    });
  }

  bondMeanHistChart = mount(bondMeanHistChartRef.value, bondMeanHistChart);
  if (bondMeanHistChart && meanRows.length) {
    const hist = binToHist(meanRows.map((r: any) => Number(r.NewEnergy_MeanPred)).filter((v: number) => Number.isFinite(v)));
    bondMeanHistChart.setOption({
      tooltip: {},
      grid: { left: 30, right: 10, top: 20, bottom: 30 },
      xAxis: { type: "category", data: hist.map((h) => h.x), axisLabel: { color: "#94a3b8", rotate: 35, fontSize: 9 } },
      yAxis: { type: "value", axisLabel: { color: "#94a3b8" } },
      series: [{ type: "bar", data: hist.map((h) => h.y), itemStyle: { color: "#f59e0b" } }],
    });
  }

  bondScatterChart = mount(bondScatterChartRef.value, bondScatterChart);
  if (bondScatterChart && scatterRows.length) {
    bondScatterChart.setOption({
      tooltip: { trigger: "item" },
      grid: { left: 36, right: 12, top: 20, bottom: 28 },
      xAxis: { type: "value", name: "OilPred/Lambda", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      yAxis: { type: "value", name: "Sigma", axisLabel: { color: "#94a3b8", fontSize: 9 } },
      series: [
        {
          type: "scatter",
          symbolSize: 6,
          data: scatterRows
            .map((r: any) => [Number(r.Lambda_t), Number(r.NewEnergy_Sigma)])
            .filter((v: number[]) => Number.isFinite(v[0]) && Number.isFinite(v[1])),
          itemStyle: { color: "#22d3ee" },
        },
      ],
    });
  }
}

async function refreshRuns() {
  try {
    const [status, runs] = await Promise.all([fetchSystemStatus(), fetchRunList()]);
    systemBusy.value = !!status?.global_busy;
    runList.value = Array.isArray(runs) ? runs : [];
    if (selectedRunId.value) {
      const exists = runList.value.some((r: any) => String(r?.run_id || "") === selectedRunId.value);
      if (!exists) selectedRunId.value = "";
    }
  } catch {
    systemBusy.value = false;
  }
}

async function refreshWtiCandles() {
  if (activePage.value !== "dashboard") return;
  try {
    await ensureEchartsReady();
    const ec = (window as any).echarts;
    if (!ec || !wtiCandleChartRef.value) return;
    // 仅使用 MySQL 里的 FRED 现货（真实数据），不再回退 CSV。
    let candleRows: any[] = [];
    try {
      const res = await fetchWtiSpotLast20();
      const spotRows = Array.isArray(res?.items) ? res.items : [];
      const spotCloseRows = spotRows
        .map((r: any) => ({ date: String(r?.date || ""), close: Number(r?.close) }))
        .filter((r: any) => r.date && Number.isFinite(r.close));
      if (spotCloseRows.length >= 2) {
        candleRows = spotCloseRows.map((r: any, i: number) => {
          const prevClose = i > 0 ? spotCloseRows[i - 1].close : r.close;
          const open = prevClose;
          const close = r.close;
          const high = Math.max(open, close);
          const low = Math.min(open, close);
          return { date: r.date, open, high, low, close, volume: 0 };
        });
        wtiCandleSource.value = "mysql:WTI_SPOT_FRED(close→OHLC)";
        wtiCandleLatestDate.value = spotCloseRows[spotCloseRows.length - 1]?.date || "";
      } else {
        const c = spotCloseRows.length;
        wtiCandleSource.value = `mysql:WTI_SPOT_FRED(不足2条:${c})`;
        wtiCandleLatestDate.value = spotCloseRows[spotCloseRows.length - 1]?.date || "";
      }
    } catch (e: any) {
      wtiCandleSource.value = `mysql:WTI_SPOT_FRED(失败:${e?.message || "error"})`;
      wtiCandleLatestDate.value = "";
      candleRows = [];
    }
    wtiCandleData.value = candleRows;
    if (!candleRows.length) return;

    const xData = candleRows.map((r: any) => r.date);
    const candleData = candleRows.map((r: any) => [r.open, r.close, r.low, r.high]);
    await nextTick();
    if (wtiCandleChart) {
      wtiCandleChart.dispose();
      wtiCandleChart = null;
    }
    wtiCandleChart = ec.init(wtiCandleChartRef.value);
    wtiCandleChart.setOption({
      backgroundColor: "transparent",
      animation: false,
      tooltip: { trigger: "axis" },
      grid: { left: 34, right: 10, top: 8, bottom: 22 },
      xAxis: {
        type: "category",
        data: xData,
        scale: true,
        axisLabel: { color: "#94a3b8", fontSize: 9, interval: "auto" },
        axisLine: { lineStyle: { color: "#334155" } },
        axisTick: { show: false },
      },
      yAxis: {
        scale: true,
        axisLabel: { color: "#94a3b8", fontSize: 9 },
        axisLine: { show: false },
        splitLine: { lineStyle: { color: "rgba(148,163,184,0.12)" } },
      },
      series: [
        {
          name: "WTI K线",
          type: "candlestick",
          data: candleData,
          itemStyle: {
            color: "#22c55e",
            color0: "#ef4444",
            borderColor: "#22c55e",
            borderColor0: "#ef4444",
          },
        },
      ],
    });
    wtiCandleChart.resize();
  } catch {
    // ignore dashboard candle chart errors
  }
}

async function submitRun() {
  if (runForm.topN < 5 || runForm.topN > 200) {
    window.alert("TopN 必须在 5~200 之间");
    return;
  }
  if (runForm.epochs < 1 || runForm.epochs > 2000) {
    window.alert("Epochs 必须在 1~2000 之间");
    return;
  }
  if (runForm.forecastSteps < 0 || runForm.forecastSteps > 90) {
    window.alert("预测步长必须在 0~90 之间");
    return;
  }
  runLoading.value = true;
  try {
    const formData = new FormData();
    if (selectedRunFile.value) formData.append("zip_file", selectedRunFile.value);
    if (runForm.modelName.trim()) formData.append("model_name", runForm.modelName.trim());
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
    dashboardData.value = buildDefaultMonitorPayload();
    logText.value = dashboardData.value.run_log_tail || "";
    fileStatuses.trainingLog = "默认展示";
    fileStatuses.predResults = "默认展示";
    fileStatuses.runLog = "默认展示";
    await nextTick();
    renderMonitorCharts();
    return;
  }

  try {
    const resolved = await resolveMonitor({
      mode: monitorMode.value === "history" ? "selected" : monitorMode.value,
      selected_run_id: monitorMode.value === "history" ? selectedRunId.value || undefined : undefined,
    });
    const resolvedRunId =
      resolved?.run_id ||
      (typeof resolved?.monitor_dir === "string" ? resolved.monitor_dir.split(/[/\\]/).pop() : "");
    if (resolvedRunId) {
      runId = resolvedRunId;
    }
  } catch {
    // 后端不支持 resolve 时回退到当前前端 runId
  }

  monitorLoading.value = true;
  try {
    const [dashboard, runLog] = await Promise.all([
      fetchTrainingDashboard(runId),
      fetchRunLog(runId, 300),
    ]);
    const normalizedDashboard = dashboard && typeof dashboard === "object" ? { ...dashboard } : {};
    let priceRows = Array.isArray(normalizedDashboard.price_series) ? normalizedDashboard.price_series : [];
    let returnRows = Array.isArray(normalizedDashboard.return_series) ? normalizedDashboard.return_series : [];

    // 兜底：若监控接口未返回价格/收益序列，则尝试从结果图表 CSV 聚合数据回填。
    if ((!priceRows.length || !returnRows.length) && runId && runId !== DEFAULT_MONITOR_RUN_ID) {
      try {
        const chartsPayload = await fetchResultCharts(runId);
        const chartRows = Array.isArray(chartsPayload?.charts?.test_predictions?.rows)
          ? chartsPayload.charts.test_predictions.rows
          : [];
        if (!priceRows.length) {
          priceRows = chartRows
            .filter((r: any) => r && r.actual_price != null && r.pred_price != null)
            .map((r: any) => ({
              Date_target: r.test_index ?? "",
              Actual_P_t_plus_H: r.actual_price,
              GRU_Pred_P_t_plus_H: r.pred_price,
            }));
        }
        if (!returnRows.length) {
          returnRows = chartRows
            .filter((r: any) => r && r.actual_return != null && r.pred_return != null)
            .map((r: any) => ({
              Date_target: r.test_index ?? "",
              Actual_Return: r.actual_return,
              GRU_Pred_Return: r.pred_return,
            }));
        }
      } catch {
        // ignore fallback failures
      }
    }

    normalizedDashboard.price_series = priceRows;
    normalizedDashboard.return_series = returnRows;
    dashboardData.value = normalizedDashboard;
    logText.value =
      typeof runLog === "string"
        ? runLog
        : typeof runLog?.log_tail === "string"
          ? runLog.log_tail
          : JSON.stringify(runLog, null, 2);
    const hasLoss = Array.isArray(normalizedDashboard?.loss_series) && normalizedDashboard.loss_series.length > 0;
    const hasPrice =
      (Array.isArray(normalizedDashboard?.price_series) && normalizedDashboard.price_series.length > 0) ||
      (Array.isArray(normalizedDashboard?.return_series) && normalizedDashboard.return_series.length > 0);
    const hasLog = !!logText.value;
    fileStatuses.trainingLog = hasLoss ? "已生成" : "未找到/为空";
    fileStatuses.predResults = hasPrice ? "已生成" : "未找到/为空";
    fileStatuses.runLog = hasLog ? "已生成" : "未找到/为空";
    await nextTick();
    try {
      await ensureEchartsReady();
      renderMonitorCharts();
    } catch (chartErr) {
      // 图表库加载失败不应阻断日志与监控数据刷新
      console.warn("monitor charts render skipped:", chartErr);
    }
  } catch (err: any) {
    dashboardData.value = buildDefaultMonitorPayload();
    logText.value = dashboardData.value.run_log_tail || `读取监控失败：${err?.message || "未知错误"}`;
    fileStatuses.trainingLog = "默认展示";
    fileStatuses.predResults = "默认展示";
    fileStatuses.runLog = "默认展示";
    await nextTick();
    renderMonitorCharts();
  } finally {
    monitorLoading.value = false;
  }
}

async function refreshResults() {
  const forceDefaultCharts = monitorMode.value === "default" || latestModelTrainingRunning.value;
  if (forceDefaultCharts || !selectedRunId.value) {
    aiReportText.value = "";
    try {
      const charts = await fetchDefaultResultCharts();
      resultChartsData.value = withDefaultResultCharts(charts);
    } catch (firstErr) {
      try {
        // 兼容后端未热更新到 default 接口时，直接走共享 run_id。
        const charts = await fetchResultCharts("默认数据");
        resultChartsData.value = withDefaultResultCharts(charts);
      } catch (secondErr: any) {
        console.error("load default result charts failed", firstErr, secondErr);
        resultChartsData.value = buildDefaultResultChartsPayload();
      }
    }
    return;
  }
  resultsLoading.value = true;
  try {
    const [overview, analytics, charts] = await Promise.all([
      fetchOverview(selectedRunId.value),
      fetchAnalytics(selectedRunId.value),
      fetchResultCharts(selectedRunId.value),
    ]);
    overviewData.value = overview;
    analyticsData.value = analytics;
    resultChartsData.value = withDefaultResultCharts(charts);
  } catch (err: any) {
    resultChartsData.value = buildDefaultResultChartsPayload();
  } finally {
    resultsLoading.value = false;
  }
}

async function generateReport() {
  if (!selectedRunId.value) return;
  resultsLoading.value = true;
  try {
    const data = await generateAIReport(selectedRunId.value, true);
    aiReportText.value = typeof data === "string" ? data : JSON.stringify(data, null, 2);
  } catch (err: any) {
    window.alert(`生成报告失败：${err?.message || "未知错误"}`);
  } finally {
    resultsLoading.value = false;
  }
}

async function refreshAllModelViewsAfterTrainingDone() {
  if (!latestRunId.value) return;
  selectedRunId.value = latestRunId.value;
  await refreshMonitor();
  await refreshResults();
  await generateReport();
  await refreshGreenStockLatest();
  await refreshGreenBondLatest();
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
  if (activePage.value === "dashboard") {
    await refreshWtiCandles();
  }
  if (activePage.value === "monitor") await refreshMonitor();
  if (activePage.value === "results") await refreshResults();
  if (activePage.value === "download") await refreshFiles();
  if (activePage.value === "greenStock") await refreshGreenStockLatest();
  if (activePage.value === "greenBond") await refreshGreenBondLatest();
  if (activePage.value === "live") {
    await refreshLiveWeightsOptions();
    await runLivePredict();
  }
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
  await refreshWtiCandles();
  await handlePageChange();
}

function handleWindowResize() {
  resizeCharts();
  wtiCandleChart?.resize?.();
  neCiChart?.resize?.();
  neSigmaChart?.resize?.();
  neRiskChart?.resize?.();
  neCiWidthChart?.resize?.();
  neMeanHistChart?.resize?.();
  neScatterChart?.resize?.();
  bondCiChart?.resize?.();
  bondSigmaChart?.resize?.();
  bondRiskChart?.resize?.();
  bondCiWidthChart?.resize?.();
  bondMeanHistChart?.resize?.();
  bondScatterChart?.resize?.();
}

function cleanupTimers() {
  if (refreshTimer) {
    clearInterval(refreshTimer);
    refreshTimer = undefined;
  }
}

function isScrollableY(el: HTMLElement) {
  const style = window.getComputedStyle(el);
  const overflowY = style.overflowY;
  const canScroll =
    (overflowY === "auto" || overflowY === "scroll" || overflowY === "overlay") &&
    el.scrollHeight > el.clientHeight + 1;
  return canScroll;
}

function hasScrollableAncestor(target: EventTarget | null) {
  let node = target instanceof HTMLElement ? target : null;
  while (node && node !== document.body) {
    if (isScrollableY(node)) return true;
    node = node.parentElement;
  }
  return false;
}

function isEditableTarget(target: EventTarget | null) {
  if (!(target instanceof HTMLElement)) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName;
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}

let wheelPendingY = 0;
let wheelRafId: number | null = null;
function normalizeWheelDeltaY(event: WheelEvent) {
  let dy = event.deltaY;
  // 0: pixel, 1: line, 2: page
  if (event.deltaMode === 1) dy *= 16;
  else if (event.deltaMode === 2) dy *= window.innerHeight;
  return dy;
}
function flushWheelScroll() {
  if (wheelPendingY !== 0) {
    window.scrollBy({ top: wheelPendingY, left: 0, behavior: "auto" });
    wheelPendingY = 0;
  }
  wheelRafId = null;
}

function handleGlobalWheel(event: WheelEvent) {
  if (!isLongContentPage.value) return;
  if (event.ctrlKey) return;
  if (Math.abs(event.deltaY) < Math.abs(event.deltaX)) return;
  if (isEditableTarget(event.target)) return;
  wheelPendingY += normalizeWheelDeltaY(event);
  if (wheelRafId == null) wheelRafId = window.requestAnimationFrame(flushWheelScroll);
  event.preventDefault();
}

function handleGlobalKeydown(event: KeyboardEvent) {
  if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "k") {
    event.preventDefault();
    focusSearchInput();
    return;
  }
  if (event.key === "Escape" && aiChatOpen.value) {
    aiChatOpen.value = false;
    return;
  }
  if (event.key === "Escape" && searchFocused.value) {
    event.preventDefault();
    clearSearch();
  }
}

function startTraining() {
  setActivePage("run");
}

function goToResults() {
  setActivePage("results");
}

function goToMonitor() {
  setActivePage("monitor");
}

function goToDownload() {
  setActivePage("download");
}

// ===== 生命周期 =====
onMounted(() => {
  updateClock();
  clockTimer = setInterval(updateClock, 1000);
  warmupData();
  setupAutoRefresh();
  window.addEventListener("resize", handleWindowResize);
  window.addEventListener("keydown", handleGlobalKeydown);
  window.addEventListener("wheel", handleGlobalWheel, {
    passive: false,
    capture: true,
  });
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

watch(liveWeightsRunId, () => {
  if (activePage.value === "live") {
    refreshLiveWeightsOptions();
  }
});

watch(monitorMode, () => {
  if (activePage.value === "monitor") refreshMonitor();
  if (activePage.value === "results") refreshResults();
  if (activePage.value === "greenStock") refreshGreenStockLatest();
  if (activePage.value === "greenBond") refreshGreenBondLatest();
});

watch(latestModelTrainingRunning, async (isRunning) => {
  if (isRunning) {
    latestTrainingWasRunning.value = true;
    return;
  }
  if (!latestTrainingWasRunning.value) return;
  if (monitorMode.value !== "latest") {
    latestTrainingWasRunning.value = false;
    return;
  }
  latestTrainingWasRunning.value = false;
  try {
    await refreshAllModelViewsAfterTrainingDone();
  } catch (err) {
    console.warn("auto refresh after training completion failed", err);
  }
});

watch([monitorAutoRefresh, monitorRefreshSec], () => {
  cleanupTimers();
  setupAutoRefresh();
});

onBeforeUnmount(() => {
  clearInterval(clockTimer);
  cleanupTimers();
  window.removeEventListener("resize", handleWindowResize);
  window.removeEventListener("keydown", handleGlobalKeydown);
  window.removeEventListener("wheel", handleGlobalWheel, true);
  if (wheelRafId != null) {
    window.cancelAnimationFrame(wheelRafId);
    wheelRafId = null;
    wheelPendingY = 0;
  }
  disposeMonitorCharts();
  wtiCandleChart?.dispose();
  wtiCandleChart = null;
  neCiChart?.dispose();
  neSigmaChart?.dispose();
  neRiskChart?.dispose();
  neCiWidthChart?.dispose();
  neMeanHistChart?.dispose();
  neScatterChart?.dispose();
  bondCiChart?.dispose();
  bondSigmaChart?.dispose();
  bondRiskChart?.dispose();
  bondCiWidthChart?.dispose();
  bondMeanHistChart?.dispose();
  bondScatterChart?.dispose();
  neCiChart = null;
  neSigmaChart = null;
  neRiskChart = null;
  neCiWidthChart = null;
  neMeanHistChart = null;
  neScatterChart = null;
  bondCiChart = null;
  bondSigmaChart = null;
  bondRiskChart = null;
  bondCiWidthChart = null;
  bondMeanHistChart = null;
  bondScatterChart = null;
});
</script>

<style scoped>
/* ================================================================
   HOME PAGE — 大宗绿测 · 数据大屏
   Style: DataV 深色科技风 · 顶部导航 + Bento 布局
   ================================================================ */
.home-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 18% 22%, rgba(14, 116, 144, 0.24), transparent 32%),
    radial-gradient(circle at 82% 18%, rgba(79, 70, 229, 0.22), transparent 34%),
    radial-gradient(circle at 50% 78%, rgba(34, 197, 94, 0.14), transparent 30%),
    linear-gradient(145deg, #040813 0%, #071228 45%, #061733 70%, #050d1f 100%);
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  overflow-x: hidden;
  overflow-y: hidden;
  position: relative;
}
.home-page--long-page {
  overflow-y: visible;
}
.home-page::before,
.home-page::after {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  z-index: 0;
}
.home-page::before {
  background:
    radial-gradient(circle at 30% 30%, rgba(56, 189, 248, 0.2), transparent 36%),
    radial-gradient(circle at 70% 65%, rgba(99, 102, 241, 0.16), transparent 38%);
  filter: blur(18px);
  animation: bgFlowA 14s ease-in-out infinite alternate;
}
.home-page::after {
  background:
    linear-gradient(120deg, rgba(34, 211, 238, 0.08), transparent 35%, rgba(99, 102, 241, 0.08) 68%, transparent 100%);
  mix-blend-mode: screen;
  animation: bgFlowB 18s linear infinite;
}
.home-page > * {
  position: relative;
  z-index: 1;
}

@keyframes bgFlowA {
  0% { transform: translate3d(-1.2%, -1%, 0) scale(1); }
  100% { transform: translate3d(1.2%, 1%, 0) scale(1.04); }
}

@keyframes bgFlowB {
  0% { opacity: 0.35; transform: translateX(-4%); }
  50% { opacity: 0.6; }
  100% { opacity: 0.35; transform: translateX(4%); }
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
  background: rgba(9, 20, 45, 0.85);
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px solid rgba(56, 189, 248, 0.28);
  box-shadow: 0 4px 16px rgba(56, 189, 248, 0.2);
  overflow: hidden;
}
.brand-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
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
  min-width: 0;
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
  max-width: 260px;
  overflow: hidden;
  text-overflow: ellipsis;
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
  padding: 12px 20px 16px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  overflow-x: hidden;
  overflow-y: hidden;
}
.main-content--long-page {
  overflow-y: visible;
}
.main-content--long-page .data-block pre {
  max-height: none;
  overflow: auto;
}
.main-content--long-page .log-columns pre {
  max-height: none;
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
.page-tab-empty {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.75);
  padding: 6px 4px;
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
  flex: none;
  width: 100%;
  min-height: 360px;
  overflow: visible;
}
.feature-panel-frame {
  width: 100%;
  border-radius: 14px;
  border: 1px solid rgba(56, 189, 248, 0.2);
  background:
    linear-gradient(180deg, rgba(2, 12, 28, 0.72), rgba(1, 8, 20, 0.76)),
    radial-gradient(circle at 92% 8%, rgba(56, 189, 248, 0.08), transparent 42%);
  box-shadow:
    inset 0 0 26px rgba(56, 189, 248, 0.06),
    0 10px 24px rgba(2, 6, 23, 0.24);
  overflow: visible;
}
.feature-panel-inner {
  height: auto;
  min-height: 100%;
  padding: 24px;
  display: flex;
  flex-direction: column;
  justify-content: flex-start;
  align-items: flex-start;
  gap: 12px;
  overflow: visible;
}
.feature-title-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  flex-wrap: wrap;
}
.feature-title {
  font-size: 24px;
  color: #f8fafc;
}
.feature-title-hint {
  font-size: 13px;
  color: rgba(186, 230, 253, 0.9);
  padding: 4px 10px;
  border-radius: 999px;
  border: 1px solid rgba(56, 189, 248, 0.24);
  background: rgba(7, 25, 52, 0.55);
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
.btn-loading {
  display: inline-flex;
  align-items: center;
  gap: 20px;
  font-weight: 700;
}
.btn-loading-spinner {
  width: 18px;
  height: 18px;
  border-radius: 50%;
  border: 3px solid rgba(224, 242, 254, 0.22);
  border-top-color: #e0f2fe;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.4);
  animation: btnSpinnerSpin 0.7s linear infinite;
}
@keyframes btnSpinnerSpin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
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
  max-height: none;
  overflow: auto;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(226, 232, 240, 0.9);
  font-family: "Cascadia Code", "Consolas", monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  max-width: 100%;
}
.log-columns {
  display: block;
}
.log-terminal-pre {
  margin: 0;
  max-height: 360px;
  overflow: auto;
  padding: 8px 10px;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: 8px;
  background: rgba(2, 6, 23, 0.38);
  font-size: 11px;
  line-height: 1.5;
  color: rgba(226, 232, 240, 0.92);
  font-family: "Cascadia Code", "Consolas", monospace;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
  word-break: break-word;
  max-width: 100%;
}
.train-dashboard {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.train-metrics {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.train-metric-card {
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 8px;
  padding: 8px 10px;
  background: linear-gradient(135deg, rgba(8, 47, 73, 0.32), rgba(15, 23, 42, 0.48));
}
.train-metric-label {
  display: block;
  font-size: 11px;
  color: rgba(148, 163, 184, 0.85);
  margin-bottom: 4px;
}
.train-metric-value {
  font-size: 15px;
  color: #e0f2fe;
}
.train-metric-value--mono {
  font-family: "Cascadia Code", "Consolas", monospace;
  font-size: 12px;
  color: #bae6fd;
  word-break: break-all;
}
.train-loss-table-wrap {
  border: 1px solid rgba(56, 189, 248, 0.16);
  border-radius: 8px;
  overflow: visible;
}
.train-loss-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 11px;
}
.train-loss-table thead {
  background: rgba(59, 130, 246, 0.16);
}
.train-loss-table th,
.train-loss-table td {
  padding: 7px 8px;
  text-align: left;
  border-bottom: 1px solid rgba(56, 189, 248, 0.12);
}
.train-loss-table th {
  color: #dbeafe;
  font-weight: 600;
}
.train-loss-table td {
  color: rgba(226, 232, 240, 0.9);
}
.train-loss-table tbody tr:nth-child(even) {
  background: rgba(255, 255, 255, 0.02);
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
.monitor-progress {
  width: 100%;
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: 8px;
  padding: 8px 10px;
  background: rgba(3, 10, 24, 0.5);
}
.monitor-progress-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  font-size: 12px;
  color: rgba(186, 230, 253, 0.9);
}
.monitor-progress-track {
  height: 8px;
  border-radius: 999px;
  background: rgba(30, 41, 59, 0.82);
  overflow: hidden;
}
.monitor-progress-fill {
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #22d3ee, #3b82f6);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.45);
  transition: width 0.35s ease;
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
.single-line-tip {
  white-space: nowrap;
}
.ne-chart-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.ne-chart-card {
  border: 1px solid rgba(56, 189, 248, 0.14);
  background: linear-gradient(180deg, rgba(2, 6, 23, 0.62), rgba(8, 22, 38, 0.58));
  border-radius: 8px;
  padding: 8px;
}
.ne-chart-box {
  width: 100%;
  height: 210px;
}
.live-hero-card {
  position: relative;
  margin: 2px auto 10px;
  width: min(720px, 96%);
  border-radius: 16px;
  padding: 18px 14px;
  text-align: center;
  border: 1px solid rgba(56, 189, 248, 0.35);
  background:
    radial-gradient(circle at 50% -20%, rgba(34, 211, 238, 0.24), transparent 58%),
    linear-gradient(180deg, rgba(8, 20, 44, 0.88), rgba(3, 10, 24, 0.86));
  box-shadow:
    inset 0 0 26px rgba(56, 189, 248, 0.12),
    0 0 24px rgba(14, 165, 233, 0.22);
  overflow: hidden;
}
.live-hero-card::after {
  content: "";
  position: absolute;
  top: -30%;
  left: -35%;
  width: 60%;
  height: 170%;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(125, 211, 252, 0.06) 35%,
    rgba(125, 211, 252, 0.35) 50%,
    rgba(125, 211, 252, 0.06) 65%,
    transparent 100%
  );
  filter: blur(6px);
  transform: rotate(14deg);
  animation: liveHeroSweep 3.8s linear infinite;
}
@keyframes liveHeroSweep {
  0% { transform: translateX(-25%) rotate(14deg); opacity: 0.65; }
  100% { transform: translateX(210%) rotate(14deg); opacity: 0.65; }
}
.live-hero-label {
  font-size: 12px;
  color: #7dd3fc;
  letter-spacing: 0.12em;
}
.live-hero-price {
  font-size: 46px;
  font-weight: 800;
  color: #e0f2fe;
  line-height: 1.12;
  text-shadow: 0 0 16px rgba(56, 189, 248, 0.35);
}
.live-hero-sub {
  font-size: 12px;
  color: rgba(186, 230, 253, 0.88);
}
.live-metrics-grid {
  margin-top: 8px;
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 8px;
}
.live-metric-item {
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 10px;
  background: rgba(2, 12, 28, 0.66);
  padding: 8px 10px;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.live-metric-item span {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.92);
}
.live-metric-item strong {
  font-size: 14px;
  color: #e0f2fe;
}
/* ─── KPI 卡片行 ─── */
.kpi-row {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 10px;
  margin-bottom: 10px;
}
.kpi-card {
  min-height: 102px;
  border-radius: 10px;
  background:
    linear-gradient(180deg, rgba(2, 12, 28, 0.72), rgba(1, 8, 20, 0.74)),
    radial-gradient(circle at 100% 0%, rgba(45, 212, 191, 0.08), transparent 45%);
  border: 1px solid rgba(56, 189, 248, 0.12);
  box-shadow: 0 8px 22px rgba(2, 6, 23, 0.24);
}
.box8-shell {
  width: 100%;
  height: 100%;
  border-radius: inherit;
}

/* ─── 主要内容网格布局 ─── */
.main-content-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.45fr) minmax(300px, 1.5fr) minmax(340px, 1fr);
  gap: 12px;
  margin-bottom: 10px;
  border: 1px solid rgba(56, 189, 248, 0.14);
  border-radius: 12px;
  padding: 10px;
  background:
    linear-gradient(180deg, rgba(2, 12, 28, 0.65), rgba(1, 8, 20, 0.68)),
    radial-gradient(circle at 90% 12%, rgba(56, 189, 248, 0.06), transparent 45%);
}
.main-content-grid > * {
  min-width: 0;
}

/* 左侧功能区 */
.left-section {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.center-section {
  display: flex;
  flex-direction: column;
}
.center-globe-card {
  flex: 1;
  min-height: 0;
}
.globe-shell {
  position: relative;
  width: 100%;
  height: 100%;
  border-radius: 12px;
  overflow: hidden;
  border: 1px solid rgba(56, 189, 248, 0.28);
  background:
    radial-gradient(circle at 50% 12%, rgba(56, 189, 248, 0.14), transparent 45%),
    radial-gradient(circle at 50% 100%, rgba(59, 130, 246, 0.12), transparent 52%),
    linear-gradient(180deg, rgba(2, 12, 30, 0.8), rgba(3, 14, 26, 0.78));
  box-shadow:
    inset 0 0 28px rgba(56, 189, 248, 0.08),
    0 0 18px rgba(37, 99, 235, 0.22);
}
.globe-shell::before {
  content: "";
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(
    120deg,
    rgba(34, 211, 238, 0.12),
    rgba(56, 189, 248, 0.7),
    rgba(125, 211, 252, 0.18),
    rgba(34, 211, 238, 0.12)
  );
  -webkit-mask:
    linear-gradient(#000 0 0) content-box,
    linear-gradient(#000 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  opacity: 0.95;
}
.globe-shell::after {
  content: "";
  position: absolute;
  top: -40%;
  left: -35%;
  width: 70%;
  height: 180%;
  pointer-events: none;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(56, 189, 248, 0.05) 35%,
    rgba(56, 189, 248, 0.26) 50%,
    rgba(56, 189, 248, 0.05) 65%,
    transparent 100%
  );
  filter: blur(8px);
  transform: rotate(16deg);
  animation: globeLightSweep 5s linear infinite;
}
@keyframes globeLightSweep {
  0% {
    transform: translateX(-18%) rotate(16deg);
    opacity: 0.7;
  }
  50% {
    opacity: 1;
  }
  100% {
    transform: translateX(168%) rotate(16deg);
    opacity: 0.7;
  }
}
.left-top-row {
  display: grid;
  height: 126px;
}
.action-squares-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(120px, 1fr));
  gap: 10px;
  height: 100%;
}
.action-square {
  width: 100%;
  height: 100%;
  min-height: 0;
}
.ai-mini-card {
  width: 100%;
  height: 100%;
}
/* 右侧监控区 */
.right-section {
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-width: 340px;
}

/* 飞线图区域 */
.flyline-row {
  flex: 1;
  min-height: 180px;
}

/* 实时数据监控区域 */
.monitor-row {
  flex: 2;
  min-height: 240px;
}
.left-candle-row {
  height: 248px;
  flex-shrink: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  align-items: stretch;
  gap: 10px;
  align-self: stretch;
  margin-top: 2px;
}
.left-candle-square {
  width: 100%;
  height: 100%;
}
.left-mini-monitor {
  width: 100%;
  min-width: 0;
}
.kpi-inner {
  padding: 14px 16px;
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
  font-size: 24px;
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
  height: 220px;
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
  height: 190px;
  flex-shrink: 0;
}
.candle-chart-box {
  width: 100%;
  height: 100%;
  min-height: 198px;
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
.panel-inner--tight {
  padding: 8px;
}
.left-mini-monitor .bento-inner {
  padding: 12px 10px;
}
.left-mini-monitor .bento-title {
  font-size: 18px;
}
.bento-ai-mini .bento-title {
  font-size: 18px;
  margin-bottom: 8px;
}
.bento-btn--mini {
  padding: 8px 16px;
  font-size: 13px;
}
.panel-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  flex-shrink: 0;
}
.panel-head--stack {
  flex-direction: column;
  align-items: flex-start;
  justify-content: flex-start;
  gap: 4px;
}
.panel-title-row {
  display: flex;
  align-items: center;
  gap: 10px;
}
.panel-subtitle--small {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.88);
  line-height: 1.35;
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
  grid-template-columns: 1.1fr 0.9fr;
  grid-template-rows: repeat(3, minmax(0, 1fr));
  grid-template-areas:
    "ai upload"
    "ai train"
    "ai result";
  gap: 10px;
  height: 248px;
}
.bento-card--large {
  grid-area: ai;
}
.bento-card--upload {
  grid-area: upload;
}
.bento-card--train {
  grid-area: train;
}
.bento-card--result {
  grid-area: result;
}
.bento-inner {
  height: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: opacity 0.2s;
  padding: 12px;
}
.bento-inner:hover {
  opacity: 0.9;
  transform: translateY(-2px);
}
.bento-icon {
  width: 42px;
  height: 42px;
  border-radius: 14px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 8px;
}
.ai-icon {
  background: transparent;
  width: 50px;
  height: 50px;
  border-radius: 16px;
  box-shadow: 0 0 20px rgba(74, 222, 128, 0.24);
  overflow: hidden;
  border: 1px solid rgba(134, 239, 172, 0.35);
}
.ai-icon-img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
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
  font-size: 14px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: 0.02em;
  margin-bottom: 4px;
}
.bento-desc {
  font-size: 10px;
  color: rgba(148, 163, 184, 0.4);
  letter-spacing: 0.03em;
}
.action-square .bento-title {
  font-size: 18px;
}
.action-square .bento-desc {
  font-size: 11px;
}
.bento-ai .bento-title {
  font-size: 18px;
  margin-bottom: 4px;
}
.bento-ai .bento-desc {
  font-size: 11px;
  margin-bottom: 12px;
}
.bento-btn {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 18px;
  border-radius: 10px;
  font-size: 12px;
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

/* ─── 全局柔化（降低硬边感） ─── */
.main-content-grid,
.kpi-card,
.work-panel,
.data-block,
.chart-box,
.ne-chart-card,
.globe-shell {
  border-radius: 14px;
  border-color: rgba(125, 211, 252, 0.14);
  box-shadow:
    inset 0 0 18px rgba(56, 189, 248, 0.04),
    0 8px 20px rgba(2, 6, 23, 0.2);
}
.status-chip,
.feature-btn,
.field input,
.field select,
.log-terminal-pre,
.train-metric-card,
.train-loss-table-wrap,
.file-item {
  border-color: rgba(125, 211, 252, 0.18);
  border-radius: 10px;
}

/* DataV 边框线条柔光化 */
.home-page :deep(.dv-border-box-1),
.home-page :deep(.dv-border-box-8) {
  border-radius: 14px;
  overflow: hidden;
}
.home-page :deep(.dv-border-box-1 svg),
.home-page :deep(.dv-border-box-8 svg) {
  opacity: 0.78;
  filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.18));
}
.home-page :deep(.dv-border-box-1 svg [stroke]),
.home-page :deep(.dv-border-box-8 svg [stroke]) {
  stroke: rgba(125, 211, 252, 0.66) !important;
}
/* 关闭 DataV 边框流动 LED 动效，改为静态柔光 */
.home-page :deep(.dv-border-box-1 svg *),
.home-page :deep(.dv-border-box-8 svg *) {
  animation: none !important;
  transition: none !important;
}

/* 数据表格区 */
.data-table-area {
  flex: 1;
  min-height: 0;
  overflow: hidden;
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
  .main-content-grid {
    grid-template-columns: 1fr;
  }
  .center-section {
    min-height: 220px;
  }
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
