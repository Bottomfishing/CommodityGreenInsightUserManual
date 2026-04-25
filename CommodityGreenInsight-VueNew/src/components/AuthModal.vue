<template>
  <Teleport to="body">
    <transition name="auth-fade">
      <div v-if="visible" class="auth-overlay" @click.self="handleClose" @mousemove="onOverlayMove">
        <!-- 背景跟随光晕 -->
        <div class="overlay-glow" :style="glowStyle"></div>

        <div class="auth-card">

          <!-- 关闭 -->
          <button class="auth-close" @click="handleClose">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M12 4L4 12M4 4l8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>

          <!-- 品牌头部 -->
          <div class="auth-header">
            <div class="auth-logo-wrap">
              <div class="auth-logo">
                <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                  <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                  <path d="M2 17l10 5 10-5"/>
                  <path d="M2 12l10 5 10-5"/>
                </svg>
              </div>
              <div class="logo-pulse"></div>
            </div>
            <h2 v-if="mode === 'login'" class="auth-heading">欢迎回来</h2>
            <h2 v-else class="auth-heading">创建账号</h2>
            <p v-if="mode === 'login'" class="auth-sub">登录以继续使用大宗绿测平台</p>
            <p v-else class="auth-sub">注册即可开始使用全部功能</p>
          </div>

          <!-- 表单 -->
          <transition :name="slideDir" mode="out-in">
            <form v-if="mode === 'login'" key="login" class="auth-form" @submit.prevent="handleSubmit">
              <div class="field">
                <label for="login-username">用户名</label>
                <div class="input-wrap">
                  <input
                    id="login-username"
                    ref="inputFocus"
                    v-model="username"
                    type="text"
                    placeholder="请输入用户名"
                    autocomplete="username"
                    :disabled="loading"
                  />
                </div>
              </div>
              <div class="field">
                <label for="login-password">密码</label>
                <div class="input-wrap pw-wrap">
                  <input
                    id="login-password"
                    v-model="password"
                    :type="showPwd ? 'text' : 'password'"
                    placeholder="请输入密码"
                    autocomplete="current-password"
                    :disabled="loading"
                  />
                  <button type="button" class="pw-toggle" tabindex="-1" @click="showPwd = !showPwd">
                    <svg v-if="!showPwd" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                    <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  </button>
                </div>
              </div>

              <!-- 错误提示 -->
              <transition name="msg-slide">
                <div v-if="error" class="err-msg">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                  {{ error }}
                </div>
              </transition>

              <!-- 登录成功状态 -->
              <transition name="success-pop">
                <div v-if="successState" class="success-state">
                  <div class="success-check">
                    <svg width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
                      <polyline points="20 6 9 17 4 12"/>
                    </svg>
                  </div>
                  <span class="success-text">登录成功</span>
                  <span class="success-sub">正在跳转...</span>
                </div>
              </transition>

              <button
                v-if="!successState"
                type="submit"
                class="submit-btn"
                :disabled="loading"
                @mouseenter="onBtnEnter"
                @mouseleave="onBtnLeave"
                @click="createRipple"
                ref="btnRef"
              >
                <span v-if="loading" class="spin"></span>
                <span v-else class="btn-text">登 录</span>
                <!-- 涟漪 -->
                <span v-for="r in ripples" :key="r.id" class="ripple" :style="r.style"></span>
                <!-- 扫光 -->
                <span class="btn-shine"></span>
              </button>

              <p v-if="!successState" class="switch-hint">
                还没有账号？
                <a href="javascript:void(0)" @click.prevent="switchTo('register')">立即注册</a>
              </p>
            </form>

            <form v-else key="register" class="auth-form" @submit.prevent="handleSubmit">
              <div class="field">
                <label for="reg-username">用户名</label>
                <div class="input-wrap">
                  <input
                    id="reg-username"
                    ref="inputFocus"
                    v-model="username"
                    type="text"
                    placeholder="设置用户名"
                    autocomplete="username"
                    :disabled="loading"
                  />
                </div>
              </div>
              <div class="field">
                <label for="reg-password">密码</label>
                <div class="input-wrap pw-wrap">
                  <input
                    id="reg-password"
                    v-model="password"
                    :type="showPwd ? 'text' : 'password'"
                    placeholder="至少 4 位字符"
                    autocomplete="new-password"
                    :disabled="loading"
                  />
                  <button type="button" class="pw-toggle" tabindex="-1" @click="showPwd = !showPwd">
                    <svg v-if="!showPwd" width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                      <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8S1 12 1 12z"/><circle cx="12" cy="12" r="3"/>
                    </svg>
                    <svg v-else width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6">
                      <path d="M17.94 17.94A10.07 10.07 0 0112 20c-7 0-11-8-11-8a18.45 18.45 0 015.06-5.94"/><path d="M9.9 4.24A9.12 9.12 0 0112 4c7 0 11 8 11 8a18.5 18.5 0 01-2.16 3.19"/><line x1="1" y1="1" x2="23" y2="23"/>
                    </svg>
                  </button>
                </div>
              </div>

              <!-- 密码强度指示器 -->
              <div v-if="password.length > 0 && mode === 'register'" class="pwd-strength">
                <div class="pwd-bars">
                  <div v-for="i in 3" :key="i" class="pwd-bar" :class="{ filled: pwdStrength >= i }" :style="pwdStrength >= i ? { background: pwdColor } : {}"></div>
                </div>
                <span class="pwd-label" :style="{ color: pwdColor }">{{ pwdLabel }}</span>
              </div>

              <transition name="msg-slide">
                <div v-if="error" class="err-msg">
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg>
                  {{ error }}
                </div>
              </transition>

              <button
                type="submit"
                class="submit-btn"
                :disabled="loading"
                @mouseenter="onBtnEnter"
                @mouseleave="onBtnLeave"
                @click="createRipple"
                ref="btnRef"
              >
                <span v-if="loading" class="spin"></span>
                <span v-else class="btn-text">注 册</span>
                <span v-for="r in ripples" :key="r.id" class="ripple" :style="r.style"></span>
                <span class="btn-shine"></span>
              </button>

              <p class="switch-hint">
                已有账号？
                <a href="javascript:void(0)" @click.prevent="switchTo('login')">返回登录</a>
              </p>
            </form>
          </transition>

          <!-- 底部安全标识 -->
          <div class="auth-footer">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
              <rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/>
            </svg>
            <span>安全连接 · 数据加密传输</span>
            <span class="footer-dot"></span>
            <span>SSL 256-bit</span>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, computed, watch, nextTick } from 'vue'

interface Props { visible: boolean }
const props = defineProps<Props>()

interface Emits {
  (e: 'update:visible', val: boolean): void
  (e: 'success'): void
}
const emit = defineEmits<Emits>()

type AuthMode = 'login' | 'register'
const mode = ref<AuthMode>('login')
const username = ref('')
const password = ref('')
const showPwd = ref(false)
const loading = ref(false)
const error = ref('')
const slideDir = ref<'slide-l' | 'slide-r'>('slide-l')
const inputFocus = ref<HTMLInputElement>()
const successState = ref(false)

// ===== 背景光晕跟随 =====
const glowStyle = ref<Record<string, string>>({})
function onOverlayMove(e: MouseEvent) {
  glowStyle.value = {
    background: `radial-gradient(circle 500px at ${e.clientX}px ${e.clientY}px, rgba(59,130,246,.04), transparent)`,
  }
}

// ===== 按钮涟漪效果 =====
const btnRef = ref<HTMLButtonElement | null>(null)
const ripples = ref<Array<{ id: number; style: Record<string, string> }>>([])
let rippleId = 0

function onBtnEnter() {
  // hover 时创建涟漪
}
function onBtnLeave() {}

// 按钮点击涟漪
function createRipple(e: MouseEvent) {
  const btn = btnRef.value
  if (!btn || loading.value) return
  const r = btn.getBoundingClientRect()
  const x = e.clientX - r.left
  const y = e.clientY - r.top
  const size = Math.max(r.width, r.height) * 2
  const id = ++rippleId
  const style: Record<string, string> = {
    width: size + 'px',
    height: size + 'px',
    left: x - size / 2 + 'px',
    top: y - size / 2 + 'px',
  }
  ripples.value.push({ id, style })
  setTimeout(() => {
    ripples.value = ripples.value.filter(r => r.id !== id)
  }, 700)
}

// ===== 密码强度 =====
const pwdStrength = computed(() => {
  const p = password.value
  if (!p) return 0
  let s = 0
  if (p.length >= 4) s++
  if (p.length >= 8) s++
  if (/[A-Z]/.test(p) && /[0-9]/.test(p)) s++
  return s
})
const pwdColor = computed(() => {
  if (pwdStrength.value <= 1) return '#f59e0b'
  if (pwdStrength.value === 2) return '#0d9488'
  return '#10b981'
})
const pwdLabel = computed(() => {
  if (pwdStrength.value <= 1) return '弱'
  if (pwdStrength.value === 2) return '中'
  return '强'
})

function switchTo(m: 'login' | 'register') {
  if (m === mode.value) return
  slideDir.value = m === 'register' ? 'slide-l' : 'slide-r'
  mode.value = m
  error.value = ''
  nextTick(() => { inputFocus.value?.focus() })
}

watch(() => props.visible, (val) => {
  if (val) {
    username.value = ''; password.value = ''; error.value = ''
    loading.value = false; showPwd.value = false
    mode.value = 'login'; slideDir.value = 'slide-l'
    successState.value = false
    nextTick(() => { inputFocus.value?.focus() })
  }
})

function handleClose() { emit('update:visible', false) }

async function handleSubmit() {
  if (!username.value || !password.value) { error.value = '请输入用户名和密码'; return }
  if (password.value.length < 4) { error.value = '密码至少需要 4 位字符'; return }
  loading.value = true; error.value = ''

  try {
    if (mode.value === 'login') {
      // 统一走后端真实登录，避免本地假 token 导致 401
      const { login: apiLogin, fetchMe } = await import('@/api/auth')
      await apiLogin(username.value, password.value)
      const me = await fetchMe()
      localStorage.setItem('username', me.username || username.value)
      successState.value = true
      setTimeout(() => {
        emit('update:visible', false)
        emit('success')
      }, 1200)
    } else {
      // 注册仍走后端
      const { register: apiRegister } = await import('@/api/auth')
      await apiRegister(username.value, password.value)
      switchTo('login')
    }
  } catch (e: any) {
    error.value = e?.message || '操作失败，请重试'
  } finally { loading.value = false }
}
</script>

<style scoped>
/* ═══ 遮罩 ═══ */
.auth-overlay {
  position: fixed; inset: 0;
  z-index: 10000;
  display: flex; align-items: center; justify-content: center;
  background: rgba(3, 7, 18, 0.7);
  backdrop-filter: blur(8px);
  -webkit-backdrop-filter: blur(8px);
  overflow: hidden;
}
/* 背景光晕跟随 */
.overlay-glow {
  position: fixed;
  inset: 0;
  pointer-events: none;
  transition: background .3s ease;
  z-index: 0;
}

/* ═══ 卡片主体 ═══ */
.auth-card {
  position: relative;
  width: 420px;
  max-width: 92vw;
  padding: 44px 38px 30px;
  border-radius: 22px;
  background: linear-gradient(
    165deg,
    rgba(59, 130, 246, 0.03) 0%,
    #0a1017 40%,
    #0c1219 100%
  );
  border: 1px solid rgba(59, 130, 246, 0.08);
  box-shadow:
    0 32px 80px rgba(0, 0, 0, 0.5),
    0 0 1px rgba(59, 130, 246, 0.12) inset,
    0 1px 0 rgba(255, 255, 255, 0.03) inset,
    0 0 120px -40px rgba(59, 130, 246, 0.06);
  z-index: 1;
  overflow: hidden;
}

/* 关闭按钮 */
.auth-close {
  position: absolute;
  top: 16px; right: 16px;
  width: 32px; height: 32px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  color: #4a5568;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .25s;
  z-index: 11;
}
.auth-close:hover {
  color: #94a3b8;
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(255, 255, 255, 0.06);
  transform: rotate(90deg);
}

/* ═══ 头部 ═══ */
.auth-header {
  margin-bottom: 32px;
  text-align: center;
  position: relative;
  z-index: 2;
}
.auth-logo-wrap {
  position: relative;
  display: inline-block;
  margin-bottom: 18px;
}
.auth-logo {
  width: 48px; height: 48px;
  border-radius: 14px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: rgba(255, 255, 255, 0.9);
  display: flex; align-items: center; justify-content: center;
  box-shadow:
    0 8px 24px rgba(59, 130, 246, 0.25),
    0 0 0 1px rgba(59, 130, 246, 0.15) inset;
  transition: transform .3s, box-shadow .3s;
}
.auth-logo-wrap:hover .auth-logo {
  transform: scale(1.05) translateY(-2px);
  box-shadow:
    0 12px 32px rgba(59, 130, 246, 0.35),
    0 0 0 1px rgba(59, 130, 246, 0.2) inset;
}
.logo-pulse {
  position: absolute;
  inset: -4px;
  border-radius: 18px;
  border: 1px solid rgba(59, 130, 246, 0.15);
  animation: logoPulse 3s ease-in-out infinite;
}
@keyframes logoPulse {
  0%, 100% { opacity: 0; transform: scale(1); }
  50% { opacity: 1; transform: scale(1.1); }
}
.auth-heading {
  font-size: 23px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: -.3px;
  margin-bottom: 7px;
}
.auth-sub {
  font-size: 14px;
  color: #5a6a7a;
  line-height: 1.5;
}

/* ═══ 表单 ═══ */
.auth-form {
  position: relative;
  z-index: 2;
}
.auth-form .field {
  margin-bottom: 18px;
}
.auth-form label {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  color: #7a8a9a;
  margin-bottom: 7px;
  letter-spacing: .3px;
}

.auth-form input[type="text"],
.auth-form input[type="password"] {
  width: 100%;
  height: 48px;
  padding: 0 14px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.025);
  color: #e2e8f0;
  font-size: 15px;
  outline: none;
  transition: all .25s ease;
  box-sizing: border-box;
}
.auth-form input::placeholder { color: #3a4a5a; font-size: 14px; }
.auth-form input:focus {
  border-color: rgba(59, 130, 246, 0.35);
  background: rgba(59, 130, 246, 0.03);
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.08);
}
.auth-form input:disabled { opacity: .4; cursor: not-allowed; }

.pw-wrap { position: relative; }
.pw-wrap input { padding-right: 42px; }
.pw-toggle {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  border: none; background: none;
  cursor: pointer; padding: 6px;
  color: #4a5a6a; transition: color .15s;
  display: flex; align-items: center;
  z-index: 2;
}
.pw-toggle:hover { color: #3b82f6; }

/* 密码强度 */
.pwd-strength {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 18px;
  margin-top: -8px;
}
.pwd-bars {
  display: flex;
  gap: 4px;
}
.pwd-bar {
  width: 32px;
  height: 3px;
  border-radius: 2px;
  background: rgba(255, 255, 255, 0.06);
  transition: background .3s;
}
.pwd-bar.filled {
  background: #3b82f6;
}
.pwd-label {
  font-size: 11px;
  font-weight: 600;
  letter-spacing: .5px;
}

/* 错误 */
.err-msg {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 11px 14px;
  border-radius: 10px;
  background: rgba(220, 38, 38, 0.06);
  border: 1px solid rgba(220, 38, 38, 0.1);
  color: #fca5a5;
  font-size: 13px;
  margin-bottom: 16px;
}
.err-msg svg { flex-shrink: 0; opacity: .7; }

/* ═══ 登录成功动画 ═══ */
.success-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 28px 0 12px;
  gap: 10px;
}
.success-check {
  width: 64px; height: 64px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.1);
  border: 2px solid rgba(59, 130, 246, 0.25);
  display: flex; align-items: center; justify-content: center;
  color: #60a5fa;
  animation: checkPop .5s cubic-bezier(.22,1,.36,1);
}
@keyframes checkPop {
  0% { transform: scale(0); opacity: 0; }
  50% { transform: scale(1.15); }
  100% { transform: scale(1); opacity: 1; }
}
.success-text {
  font-size: 18px;
  font-weight: 700;
  color: #e2e8f0;
  animation: fadeUp .4s ease .15s both;
}
.success-sub {
  font-size: 13px;
  color: #5a6a7a;
  animation: fadeUp .4s ease .25s both;
}
@keyframes fadeUp {
  from { opacity: 0; transform: translateY(8px); }
  to { opacity: 1; transform: none; }
}
.success-pop-enter-active { transition: all .35s cubic-bezier(.22,1,.36,1); }
.success-pop-leave-active { transition: all .2s ease; }
.success-pop-enter-from { opacity: 0; transform: scale(.9); }
.success-pop-leave-to { opacity: 0; transform: scale(.95); }

/* ═══ 提交按钮 ═══ */
.submit-btn {
  position: relative;
  width: 100%; height: 48px;
  border: none; border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  color: #fff;
  font-size: 15px; font-weight: 600;
  letter-spacing: 3px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .3s cubic-bezier(.22,1,.36,1);
  box-shadow:
    0 4px 20px rgba(59, 130, 246, 0.25),
    0 0 0 1px rgba(59, 130, 246, 0.1) inset,
    0 1px 0 rgba(255, 255, 255, 0.08) inset;
  margin-top: 6px;
  overflow: hidden;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow:
    0 8px 32px rgba(59, 130, 246, 0.35),
    0 0 0 1px rgba(59, 130, 246, 0.15) inset,
    0 1px 0 rgba(255, 255, 255, 0.1) inset;
  background: linear-gradient(135deg, #60a5fa, #3b82f6);
}
.submit-btn:active:not(:disabled) { transform: translateY(0); }
.submit-btn:disabled { opacity: .5; cursor: not-allowed; }

/* 涟漪 */
.ripple {
  position: absolute;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  transform: scale(0);
  animation: rippleOut .6s ease-out forwards;
  pointer-events: none;
}
@keyframes rippleOut {
  to { transform: scale(2.5); opacity: 0; }
}

/* 按钮扫光 */
.btn-shine {
  position: absolute;
  top: 0; left: -100%;
  width: 60%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.08), transparent);
  transform: skewX(-20deg);
  animation: btnShine 4s ease-in-out infinite;
  pointer-events: none;
}
@keyframes btnShine {
  0%, 100% { left: -100%; }
  50% { left: 140%; }
}

.spin {
  width: 18px; height: 18px;
  border: 2.5px solid rgba(255, 255, 255, 0.2);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 切换提示 */
.switch-hint {
  text-align: center;
  margin-top: 22px;
  font-size: 13.5px;
  color: #5a6a7a;
}
.switch-hint a {
  color: #60a5fa;
  text-decoration: none;
  font-weight: 600;
  margin-left: 3px;
  transition: all .2s;
  position: relative;
}
.switch-hint a::after {
  content: '';
  position: absolute;
  bottom: -2px; left: 0;
  width: 0; height: 1px;
  background: #60a5fa;
  transition: width .25s;
}
.switch-hint a:hover { color: #93c5fd; }
.switch-hint a:hover::after { width: 100%; }

/* ═══ 底部 ═══ */
.auth-footer {
  display: flex; align-items: center; gap: 6px;
  justify-content: center;
  margin-top: 28px;
  padding-top: 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
  font-size: 11px;
  color: #3a4a5a;
  letter-spacing: .3px;
  position: relative;
  z-index: 2;
}
.auth-footer svg { flex-shrink: 0; opacity: .4; }
.footer-dot {
  width: 3px; height: 3px;
  border-radius: 50%;
  background: rgba(59, 130, 246, 0.3);
}

/* ═══ 过渡动画 ═══ */
.auth-fade-enter-active { transition: all .35s ease; }
.auth-fade-leave-active { transition: all .25s ease; }
.auth-fade-enter-from, .auth-fade-leave-to { opacity: 0; }
.auth-fade-enter-from .auth-card,
.auth-fade-leave-to .auth-card {
  transform: scale(.92) translateY(16px);
  opacity: 0;
}

/* 左右滑动 */
.slide-l-enter-active, .slide-l-leave-active,
.slide-r-enter-active, .slide-r-leave-active {
  transition: all .28s cubic-bezier(.4,0,.2,1);
}
.slide-l-enter-from { opacity: 0; transform: translateX(28px); }
.slide-l-leave-to   { opacity: 0; transform: translateX(-28px); }
.slide-r-enter-from { opacity: 0; transform: translateX(-28px); }
.slide-r-leave-to   { opacity: 0; transform: translateX(28px); }

.msg-slide-enter-active, .msg-slide-leave-active { transition: all .25s; }
.msg-slide-enter-from, .msg-slide-leave-to { opacity: 0; transform: translateY(-8px); }

/* ═══ 响应式 ═══ */
@media (max-width: 480px) {
  .auth-card {
    padding: 36px 24px 24px;
    border-radius: 18px;
  }
  .auth-heading { font-size: 20px; }
  .auth-sub { font-size: 13px; }
}
</style>
