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
          <span class="stat-val">运行中</span>
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
          <span class="stat-label">运行测试</span>
          <span class="stat-val stat-val--success">PASSED</span>
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
      <dv-decoration-5 style="width: 100%; height: 3px; margin-bottom: 4px" />

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
      <dv-decoration-5 style="width: 100%; height: 3px; margin-top: 8px" />
      </template>

      <section v-else class="feature-panel">
        <dv-border-box-1 style="width: 100%; height: 100%">
          <div class="feature-panel-inner">
            <h2 class="feature-title">{{ currentTabTitle }}</h2>
            <p class="feature-desc">{{ currentTabDesc }}</p>
            <div class="feature-actions">
              <button class="feature-btn" @click="activePage = 'dashboard'">
                返回总览
              </button>
              <button
                v-if="activePage === 'results'"
                class="feature-btn feature-btn--primary"
                @click="goToResults"
              >
                刷新结果
              </button>
            </div>
          </div>
        </dv-border-box-1>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount, computed } from "vue";
import { useRouter } from "vue-router";
import { clearToken } from "@/api/auth";

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
  bgImgSrc: "@/assets/世界.png",
  curvature: 5,
  relative: true,
});

// ===== 滚动表格数据 =====
const scrollConfig = reactive({
  header: ["标的", "最新价", "涨跌幅", "成交量", "状态"],
  data: [
    ["Brent 原油", "$78.42", "+2.34%", "2.4M", "📈 买入"],
    ["WTI 原油", "$74.56", "+1.87%", "1.8M", "📈 买入"],
    ["CSI 新能源", "3,847", "+1.82%", "862亿", "📈 买入"],
    ["光伏产业", "4,126", "+0.95%", "423亿", "📊 持有"],
    ["新能源车", "2,934", "-0.42%", "312亿", "📉 观望"],
    ["10Y 国债", "2.34%", "-2bp", "1.2万亿", "📊 持有"],
    ["SHIBOR", "1.68%", "0bp", "-", "📊 持有"],
    ["LPR 1Y", "3.45%", "-5bp", "-", "📉 下降"],
  ],
  rowNum: 7,
  headerBGC: "rgba(59,130,246,0.08)",
  oddRowBGC: "transparent",
  evenRowBGC: "rgba(255,255,255,0.015)",
  headerHeight: 36,
  rowHeight: 32,
  align: ["left", "right", "right", "right", "center"],
  headerFontSize: 12,
  fontSize: 12,
  color: "rgba(148,163,184,0.7)",
});

// ===== 退出 =====
function handleLogout() {
  clearToken();
  router.push({ name: "Landing" });
}

// ===== Bento 功能 =====
function openAIChat() {
  activePage.value = "run";
}

function handleUpload() {
  const input = document.createElement("input");
  input.type = "file";
  input.accept = ".csv,.xlsx,.xls,.json";
  input.onchange = () => {
    if (input.files?.length) {
      console.log("upload:", input.files[0].name);
    }
  };
  input.click();
}

function startTraining() {
  activePage.value = "monitor";
}

function goToResults() {
  activePage.value = "results";
}

// ===== 生命周期 =====
onMounted(() => {
  updateClock();
  clockTimer = setInterval(updateClock, 1000);
});

onBeforeUnmount(() => {
  clearInterval(clockTimer);
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
  width: 300px;
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
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: rgba(15, 23, 42, 0.55);
  color: #cbd5e1;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
}
.feature-btn--primary {
  border-color: rgba(59, 130, 246, 0.55);
  background: rgba(59, 130, 246, 0.2);
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
}

/* ─── 主要内容网格布局 ─── */
.main-content-grid {
  display: grid;
  grid-template-columns: 4fr 1fr;
  gap: 16px;
  margin-bottom: 16px;
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
  opacity: 0.85;
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
