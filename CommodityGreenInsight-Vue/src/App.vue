<template>
  <div id="app" :data-theme="theme">
    <!-- ─── 侧边栏 ─── -->
    <aside
      :class="['sidebar', { collapsed: sidebarCollapsed }]"
      :style="sidebarCollapsed ? {} : { width: sidebarWidth + 'px' }"
    >

      <!-- ══ 展开状态内容 ══ -->
      <template v-if="!sidebarCollapsed">
        <!-- 品牌区 -->
        <div class="sidebar-brand">
          <div class="sidebar-brand-logo">
            <div class="sidebar-logo-icon">
              <img src="/logo_zrld.png" alt="大宗绿测图标" />
            </div>
            <div class="sidebar-brand-text">
              <div class="sidebar-brand-name">大宗绿测</div>
              <div class="sidebar-brand-sub">油价预测与绿色金融平台</div>
            </div>
          </div>
          <button class="sidebar-collapse-btn" @click="sidebarCollapsed = true" title="收起侧边栏">
            <span>‹</span>
          </button>
        </div>

        <!-- 状态卡片 -->
        <div class="sidebar-status">
          <div class="sidebar-status-row">
            <div :class="['status-dot', systemStatus.dot]"></div>
            <div class="status-lbl">任务状态</div>
            <div :class="['status-val', systemStatus.valCls]">{{ systemStatus.text }}</div>
          </div>
          <div class="sidebar-status-row">
            <div class="status-dot off"></div>
            <div class="status-lbl">累计运行</div>
            <div class="status-val">{{ runCount }} 次</div>
          </div>
        </div>

        <!-- 历史运行选择 -->
        <p class="sidebar-section-label">历史运行</p>
        <select class="sidebar-select" v-model="selectedRunId" @change="onRunSelect">
          <option value="">（本次运行后自动出现）</option>
          <option v-for="run in runList" :key="run.run_id" :value="run.run_id">
            {{ run.status === 'done' ? '已生成 ' : '处理中 ' }}{{ run.run_id }}
          </option>
        </select>

        <!-- 用户手册 -->
        <a class="sidebar-btn" href="/用户手册.pdf" target="_blank">📖 用户手册</a>

        <!-- 新手助手小绿 -->
        <details class="sidebar-expander">
            <summary>🤖 AI 助手</summary>
          <div class="sidebar-chat-messages" ref="sidebarRef">
            <div v-for="(msg, i) in sidebarMsgs" :key="i"
              :class="['sidebar-chat-msg', msg.role === 'user' ? 'user' : 'bot']">
              {{ msg.content }}
            </div>
            <div v-if="sidebarLoading" class="sidebar-chat-msg bot">
              <span class="spinner"></span> 思考中…
            </div>
          </div>
          <div class="sidebar-chat-input-row">
            <input
              class="sidebar-chat-input"
              type="text"
              v-model="sidebarInput"
              placeholder="问点什么..."
              @keydown.enter="sendSidebarChat"
            />
            <button class="sidebar-chat-btn" :disabled="sidebarLoading" @click="sendSidebarChat">发送</button>
          </div>
          <button class="sidebar-chat-clear" @click="clearSidebarChat">清空对话</button>
        </details>
      </template>

      <!-- ══ 收起状态：极简版 ══ -->
      <template v-else>
        <div class="sidebar-collapsed-brand">
          <button class="sidebar-collapse-btn" @click="sidebarCollapsed = false" title="展开侧边栏">
            <span>‹</span>
          </button>
          <div class="sidebar-collapsed-brand-name">大宗绿测</div>
        </div>

        <!-- 状态点（居中显示） -->
        <div class="sidebar-collapsed-section" style="padding: 0.6rem 0;">
          <div :class="['status-dot', systemStatus.dot]" style="margin: 0 auto;"></div>
          <div style="text-align:center; font-size:0.58rem; color:var(--text-muted); margin-top:5px;">{{ systemStatus.text }}</div>
        </div>

        <!-- 分隔线 -->
        <div class="sidebar-collapsed-divider"></div>

        <!-- 用户手册按钮 -->
        <div class="sidebar-collapsed-section" style="padding: 0.4rem 0;">
          <a class="sidebar-btn sidebar-btn-mini" href="/用户手册.pdf" target="_blank" title="用户手册">📖</a>
        </div>

        <!-- AI 助手按钮（点击弹出浮动面板） -->
        <div class="sidebar-collapsed-section" style="padding: 0.4rem 0;">
          <button class="sidebar-btn sidebar-btn-mini" @click="sidebarChatOpen = true" title="AI 助手">🤖</button>
        </div>

        <!-- AI 助手浮动面板 -->
        <Teleport to="body">
          <div v-if="sidebarChatOpen" class="ai-float-overlay" @click.self="sidebarChatOpen = false">
            <div class="ai-float-panel">
              <div class="ai-float-header">
                <span>🤖 AI 助手</span>
                <button class="ai-float-close" @click="sidebarChatOpen = false">✕</button>
              </div>
              <div class="sidebar-chat-messages ai-float-messages" ref="sidebarRef">
                <div v-for="(msg, i) in sidebarMsgs" :key="i"
                  :class="['sidebar-chat-msg', msg.role === 'user' ? 'user' : 'bot']">
                  {{ msg.content }}
                </div>
                <div v-if="sidebarLoading" class="sidebar-chat-msg bot">
                  <span class="spinner"></span> 思考中…
                </div>
              </div>
              <div class="sidebar-chat-input-row">
                <input class="sidebar-chat-input" type="text" v-model="sidebarInput"
                  placeholder="问点什么..." @keydown.enter="sendSidebarChat" />
                <button class="sidebar-chat-btn" :disabled="sidebarLoading" @click="sendSidebarChat">发送</button>
              </div>
              <button class="sidebar-chat-clear" @click="clearSidebarChat">清空对话</button>
            </div>
          </div>
        </Teleport>
      </template>

    </aside>

    <!-- ─── 主内容区（用 margin-left 推开侧边栏 + 拖拽把手） ─── -->
    <div
      class="main-content"
      :style="mainContentStyle"
    >
      <!-- Tab 导航栏（tabs 左 + 工具按钮右，同一行） -->
      <nav class="tab-bar">
        <!-- 左：Tab 按钮组 -->
        <div class="tab-bar-tabs">
          <button
            v-for="tab in tabs"
            :key="tab.key"
            :class="['tab-btn', { active: currentTab === tab.key }]"
            @click="currentTab = tab.key"
          >
            {{ tab.label }}
          </button>
        </div>

        <!-- 右：状态文字 + 三点菜单 -->
        <div class="tab-bar-tools">
          <!-- 状态指示 -->
          <span :class="['tabbar-status-dot', systemStatus.dot]"></span>
          <span class="tabbar-status-text">{{ systemStatus.label }}</span>
          <!-- 三点菜单按钮 -->
          <button class="tabbar-dots-btn" @click.stop="topbarMenuOpen = !topbarMenuOpen">
            <svg width="16" height="16" viewBox="0 0 18 18" fill="currentColor">
              <circle cx="9" cy="3" r="1.5"/>
              <circle cx="9" cy="9" r="1.5"/>
              <circle cx="9" cy="15" r="1.5"/>
            </svg>
          </button>
          <!-- 下拉菜单 -->
          <div v-if="topbarMenuOpen" class="tabbar-dropdown">
            <button class="tabbar-dropdown-item" @click="toggleTheme(); topbarMenuOpen = false">
              <span>{{ theme === 'dark' ? '☀️' : '🌙' }}</span>
              <span>{{ theme === 'dark' ? '切换亮色主题' : '切换暗色主题' }}</span>
            </button>
            <a class="tabbar-dropdown-item" href="/用户手册.pdf" target="_blank" @click="topbarMenuOpen = false">
              <span>📖</span>
              <span>用户手册</span>
            </a>
            <div class="tabbar-dropdown-divider"></div>
            <button class="tabbar-dropdown-item" @click="openLogin(); topbarMenuOpen = false">
              <span>{{ isLoggedIn ? '🔓' : '🔐' }}</span>
              <span>{{ isLoggedIn ? '账号 (' + currentUser + ')' : '登录' }}</span>
            </button>
            <button v-if="isLoggedIn" class="tabbar-dropdown-item" @click="handleLogout">
              <span>🚪</span>
              <span>退出登录</span>
            </button>
            <div class="tabbar-dropdown-divider"></div>
            <button class="tabbar-dropdown-item" @click="aboutOpen = true; topbarMenuOpen = false">
              <span>ℹ️</span>
              <span>关于大宗绿测</span>
            </button>
          </div>
        </div>
      </nav>

      <!-- 关于弹窗 -->
      <div v-if="aboutOpen" class="about-overlay" @click.self="aboutOpen = false">
        <div class="about-modal">
          <div class="about-header">
            <div class="about-logo-icon">
              <img src="/logo_zrld.png" alt="logo" />
            </div>
            <div class="about-title-group">
              <h2 class="about-title">大宗绿测</h2>
              <p class="about-subtitle">油价预测与绿色金融平台 · v2.0</p>
            </div>
            <button class="about-close" @click="aboutOpen = false">✕</button>
          </div>
          <div class="about-body">
            <p class="about-desc">
              大宗绿测是一款面向绿色金融领域的智能化预测分析平台，基于深度学习技术，对油价、新能源股票、绿色债券等大宗商品与金融资产进行建模预测，助力投资者与金融机构洞察市场趋势、规避风险。
            </p>
            <div class="about-features">
              <div class="about-feature-item">
                <span class="about-feature-icon">🛢️</span>
                <div>
                  <strong>油价预测（GRU）</strong>
                  <p>基于门控循环单元深度学习模型，结合多因子分析，预测国际油价走势</p>
                </div>
              </div>
              <div class="about-feature-item">
                <span class="about-feature-icon">📈</span>
                <div>
                  <strong>新能源股票预测</strong>
                  <p>整合新能源产业链数据，预测相关股票收益与波动趋势</p>
                </div>
              </div>
              <div class="about-feature-item">
                <span class="about-feature-icon">🌱</span>
                <div>
                  <strong>绿债预测</strong>
                  <p>基于新能源发展因子，预测绿色债券收益率与风险区间</p>
                </div>
              </div>
              <div class="about-feature-item">
                <span class="about-feature-icon">🤖</span>
                <div>
                  <strong>AI 报告解读</strong>
                  <p>大语言模型自动生成企业银行团队分析报告，解读预测结果</p>
                </div>
              </div>
            </div>
            <div class="about-footer">
              <p>© 2025 大宗绿测 · 油价预测与绿色金融平台</p>
            </div>
          </div>
        </div>
      </div>

      <!-- ─── 登录弹窗 ─── -->
      <div v-if="loginOpen" class="about-overlay" @click.self="loginOpen = false">
        <div class="login-modal">
          <div class="about-header">
            <div style="font-size:1.4rem;">🔐</div>
            <div class="about-title-group">
              <h2 class="about-title" style="font-size:1.05rem;">{{ loginMode === 'login' ? '登录账号' : '注册账号' }}</h2>
              <p class="about-subtitle">大宗绿测 · 油价预测与绿色金融平台</p>
            </div>
            <button class="about-close" @click="loginOpen = false">✕</button>
          </div>
          <div class="about-body">
            <div class="login-error" v-if="loginError">{{ loginError }}</div>
            <div class="login-field">
              <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:0.3rem;">用户名</label>
              <input class="sidebar-chat-input" style="width:100%;" v-model="loginUsername" placeholder="请输入用户名" />
            </div>
            <div class="login-field" style="margin-top:0.8rem;">
              <label style="font-size:0.8rem; color:var(--text-muted); display:block; margin-bottom:0.3rem;">密码</label>
              <input class="sidebar-chat-input" style="width:100%;" type="password" v-model="loginPassword" placeholder="请输入密码" @keydown.enter="handleLogin" />
            </div>
            <div style="display:flex; gap:0.6rem; margin-top:1rem;">
              <button class="btn btn-primary" style="flex:1;" @click="handleLogin" :disabled="loginLoading">
                <span v-if="loginLoading" class="spinner" style="width:14px;height:14px;border-width:2px;"></span>
                <span>{{ loginLoading ? '处理中...' : (loginMode === 'login' ? '登录' : '注册') }}</span>
              </button>
            </div>
            <button class="sidebar-chat-clear" style="margin-top:0.5rem;" @click="loginMode = loginMode === 'login' ? 'register' : 'login'">
              {{ loginMode === 'login' ? '没有账号？去注册' : '已有账号？去登录' }}
            </button>
          </div>
        </div>
      </div>

      <!-- Tab 内容面板 -->
      <div class="tab-panel">
        <RunView
          v-if="currentTab === 'run'"
          :system-status="systemStatus"
          :run-count="runCount"
          :selected-run-id="selectedRunId"
          @run-started="onRunStarted"
          @tab-change="currentTab = $event"
        />
        <MonitorView
          v-else-if="currentTab === 'monitor'"
          :selected-run-id="selectedRunId"
          :run-list="runList"
        />
        <ResultsView
          v-else-if="currentTab === 'results'"
          :selected-run-id="selectedRunId"
        />
        <DownloadView
          v-else-if="currentTab === 'download'"
          :selected-run-id="selectedRunId"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, onBeforeUnmount, nextTick, watch } from 'vue'
import RunView from './views/RunView.vue'
import MonitorView from './views/MonitorView.vue'
import ResultsView from './views/ResultsView.vue'
import DownloadView from './views/DownloadView.vue'
import { fetchSystemStatus, fetchRunList, sendAIChat, login, register, fetchMe, getToken, logout } from './api/index.js'

// ── 登录 ──
const loginOpen = ref(false)
const loginMode = ref('login')   // 'login' | 'register'
const loginUsername = ref('')
const loginPassword = ref('')
const loginLoading = ref(false)
const loginError = ref('')
const isLoggedIn = ref(!!getToken())
const currentUser = ref(localStorage.getItem('username') || '')

async function openLogin() {
  loginOpen.value = true
  loginError.value = ''
  loginUsername.value = ''
  loginPassword.value = ''
}

async function handleLogin() {
  if (!loginUsername.value || !loginPassword.value) {
    loginError.value = '请输入用户名和密码'
    return
  }
  loginLoading.value = true
  loginError.value = ''
  try {
    if (loginMode.value === 'login') {
      await login({ username: loginUsername.value, password: loginPassword.value })
      const me = await fetchMe()
      currentUser.value = me.username || loginUsername.value
      localStorage.setItem('username', currentUser.value)
      isLoggedIn.value = true
      loginOpen.value = false
    } else {
      await register({ username: loginUsername.value, password: loginPassword.value })
      loginMode.value = 'login'
      loginError.value = '注册成功，请登录'
    }
  } catch (e) {
    loginError.value = e.message || '操作失败，请重试'
  } finally {
    loginLoading.value = false
  }
}

function handleLogout() {
  logout()
  isLoggedIn.value = false
  currentUser.value = ''
  loginOpen.value = false
  topbarMenuOpen.value = false
}

// ── 主题 ──
const theme = ref(localStorage.getItem('theme') || 'light')
function toggleTheme() {
  theme.value = theme.value === 'dark' ? 'light' : 'dark'
  localStorage.setItem('theme', theme.value)
  document.documentElement.setAttribute('data-theme', theme.value)
}
// 初始化主题到 html 上
document.documentElement.setAttribute('data-theme', theme.value)

// ── 侧边栏折叠 ──
const sidebarCollapsed = ref(localStorage.getItem('sidebarCollapsed') === 'true')
watch(sidebarCollapsed, (val) => localStorage.setItem('sidebarCollapsed', val))

// ── 侧边栏宽度拖拽 ──
const sidebarWidth = ref(parseInt(localStorage.getItem('sidebarWidth')) || 280)
const isResizing = ref(false)

const sidebarW = computed(() => (sidebarCollapsed.value ? 64 : sidebarWidth.value))
const mainContentStyle = computed(() => ({
  marginLeft: sidebarW.value + 'px',
  width: `calc(100vw - ${sidebarW.value}px)`,
}))

function startResize(e) {
  isResizing.value = true
  document.addEventListener('mousemove', onResizeMove)
  document.addEventListener('mouseup', stopResize)
  document.body.style.cursor = 'col-resize'
  document.body.style.userSelect = 'none'
}

function onResizeMove(e) {
  if (!isResizing.value) return
  const newW = Math.min(Math.max(e.clientX, 200), 480)
  sidebarWidth.value = newW
  localStorage.setItem('sidebarWidth', newW)
}

function stopResize() {
  isResizing.value = false
  document.removeEventListener('mousemove', onResizeMove)
  document.removeEventListener('mouseup', stopResize)
  document.body.style.cursor = ''
  document.body.style.userSelect = ''
}

// ── 标签页 ──
const tabs = [
  { key: 'run',      label: '运行',    icon: '▶' },
  { key: 'monitor',  label: '训练监控', icon: '📊' },
  { key: 'results',  label: '结果预览', icon: '📈' },
  { key: 'download', label: '下载/导出', icon: '⬇' },
]
const currentTab = ref('run')

// ── 状态数据 ──
const runList = ref([])
const selectedRunId = ref('')
const rawStatus = ref(null)

const systemStatus = computed(() => {
  const s = rawStatus.value
  if (!s) return { dot: 'idle', label: '空闲', text: '空闲', valCls: 'amber' }
  if (s.global_busy) {
    return { dot: 'active', label: '运行中', text: '运行中…', valCls: 'green' }
  }
  return { dot: 'done', label: '空闲', text: '空闲', valCls: 'amber' }
})

const runCount = computed(() => Math.max(runList.value.length - 1, 0))

// ── 轮询 ──
let pollTimer = null

async function refresh() {
  try {
    const [status, runs] = await Promise.all([
      fetchSystemStatus(),
      fetchRunList(),
    ])
    rawStatus.value = status
    runList.value = runs || []
    // 如果有运行中的任务，自动选中最新
    if (status.global_busy && status.current_run_id && !selectedRunId.value) {
      selectedRunId.value = status.current_run_id
    }
  } catch (e) {
    // 静默失败
  }
}

function onRunSelect() {
  // 选择历史 run 后不做额外操作，各子页面监听 selectedRunId
}

function onRunStarted(runId) {
  selectedRunId.value = runId
  currentTab.value = 'monitor'
  refresh()
}

// ── 侧边栏 AI 助手聊天 ──
const sidebarChatOpen = ref(false)

const sidebarMsgs = ref([
  {
    role: 'bot',
    content: '你好！你可以直接问我：\n（1）我的 zip 里哪些文件是必须的？\n（2）点「开始运行」后，结果分别在哪个 tab 看？\n（3）`prediction_results.csv` / `gru_returns.png` 怎么解读？',
  }
])
const sidebarInput = ref('')
const sidebarLoading = ref(false)
const sidebarRef = ref(null)

// ── 顶部工具栏菜单 ──
const topbarMenuOpen = ref(false)
const aboutOpen = ref(false)

function closeTopbarMenu(e) {
  if (!e.target.closest('.topbar-actions')) {
    topbarMenuOpen.value = false
  }
}
onMounted(() => document.addEventListener('click', closeTopbarMenu))
onBeforeUnmount(() => document.removeEventListener('click', closeTopbarMenu))

async function sendSidebarChat() {
  if (!sidebarInput.value.trim() || sidebarLoading.value) return
  if (!isLoggedIn.value) {
    sidebarMsgs.value.push({ role: 'bot', content: '请先在右上角菜单登录后再使用 AI 助手。' })
    return
  }
  const q = sidebarInput.value.trim()
  sidebarInput.value = ''
  sidebarMsgs.value.push({ role: 'user', content: q })
  sidebarLoading.value = true
  await nextTick()
  if (sidebarRef.value) sidebarRef.value.scrollTop = sidebarRef.value.scrollHeight
  try {
    const r = await sendAIChat({ mode: 'oil', prompt: q, run_id: selectedRunId.value || undefined })
    sidebarMsgs.value.push({ role: 'bot', content: r?.answer || '（无回复）' })
  } catch(e) {
    const msg = e?.message || '网络错误'
    if (msg.includes('401') || msg.includes('unauthorized')) {
      sidebarMsgs.value.push({ role: 'bot', content: '登录已过期，请在右上角菜单重新登录。' })
      isLoggedIn.value = false
    } else {
      sidebarMsgs.value.push({ role: 'bot', content: '请求失败：' + msg })
    }
  } finally {
    sidebarLoading.value = false
    await nextTick()
    if (sidebarRef.value) sidebarRef.value.scrollTop = sidebarRef.value.scrollHeight
  }
}

function clearSidebarChat() {
  sidebarMsgs.value = [{
    role: 'bot',
    content: '你好！你可以直接问我：\n（1）我的 zip 里哪些文件是必须的？\n（2）点「开始运行」后，结果分别在哪个 tab 看？\n（3）`prediction_results.csv` / `gru_returns.png` 怎么解读？',
  }]
  sidebarInput.value = ''
}

onMounted(() => {
  refresh()
  pollTimer = setInterval(refresh, 5000)
})

onUnmounted(() => {
  clearInterval(pollTimer)
})
</script>
