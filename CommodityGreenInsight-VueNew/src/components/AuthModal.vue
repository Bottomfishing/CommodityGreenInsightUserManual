<template>
  <Teleport to="body">
    <transition name="modal-fade">
      <div v-if="visible" class="auth-overlay" @click.self="handleClose">
        <!-- 背景网格 -->
        <div class="grid-bg"></div>

        <div class="auth-modal">
          <!-- 顶部关闭 -->
          <button class="close-btn" @click="handleClose">✕</button>

          <!-- 模式切换头部（科技风格） -->
          <div class="switch-header">
            <div class="switch-track">
              <div
                :class="['switch-indicator', { right: mode === 'register' }]"
              ></div>
              <button
                :class="['switch-btn', { active: mode === 'login' }]"
                @click="switchMode('login')"
              >
                <span class="btn-icon">🔐</span> 登录
              </button>
              <button
                :class="['switch-btn', { active: mode === 'register' }]"
                @click="switchMode('register')"
              >
                <span class="btn-icon">🚀</span> 注册
              </button>
            </div>
          </div>

          <!-- 内容区（左右滑动） -->
          <div class="form-container">
            <transition :name="slideDirection" mode="out-in">
              <form v-if="mode === 'login'" key="login" class="auth-form" @submit.prevent="handleSubmit">
                <p class="form-desc">欢迎回来，请输入您的账号信息</p>
                <div class="field-group">
                  <div class="field">
                    <label>用户名</label>
                    <div class="input-box">
                      <span class="box-icon">👤</span>
                      <input v-model="username" type="text" placeholder="输入用户名" autocomplete="username" :disabled="loading" />
                      <div class="input-line"></div>
                    </div>
                  </div>
                  <div class="field">
                    <label>密码</label>
                    <div class="input-box">
                      <span class="box-icon">🔒</span>
                      <input v-model="password" :type="showPwd ? 'text' : 'password'" placeholder="输入密码" autocomplete="current-password" :disabled="loading" />
                      <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁️' }}</button>
                      <div class="input-line"></div>
                    </div>
                  </div>
                </div>

                <transition name="err-fade">
                  <div v-if="error" class="error-bar">
                    <span class="error-dot"></span>{{ error }}
                  </div>
                </transition>

                <button type="submit" class="action-btn login-btn" :disabled="loading">
                  <span v-if="loading" class="spinner-mini"></span>
                  <template v-else>
                    <span class="btn-glow"></span> 登 录
                  </template>
                </button>
              </form>

              <form v-else key="register" class="auth-form" @submit.prevent="handleSubmit">
                <p class="form-desc">创建账号，开始您的绿色金融之旅</p>
                <div class="field-group">
                  <div class="field">
                    <label>用户名</label>
                    <div class="input-box">
                      <span class="box-icon">👤</span>
                      <input v-model="username" type="text" placeholder="设置用户名" autocomplete="username" :disabled="loading" />
                      <div class="input-line"></div>
                    </div>
                  </div>
                  <div class="field">
                    <label>密码</label>
                    <div class="input-box">
                      <span class="box-icon">🔒</span>
                      <input v-model="password" :type="showPwd ? 'text' : 'password'" placeholder="设置密码（至少4位）" autocomplete="new-password" :disabled="loading" />
                      <button type="button" class="pwd-toggle" @click="showPwd = !showPwd">{{ showPwd ? '🙈' : '👁️' }}</button>
                      <div class="input-line"></div>
                    </div>
                  </div>
                </div>

                <transition name="err-fade">
                  <div v-if="error" class="error-bar">
                    <span class="error-dot"></span>{{ error }}
                  </div>
                </transition>

                <button type="submit" class="action-btn reg-btn" :disabled="loading">
                  <span v-if="loading" class="spinner-mini"></span>
                  <template v-else>
                    <span class="btn-glow"></span> 注 册
                  </template>
                </button>
              </form>
            </transition>
          </div>

          <!-- 底部装饰线 -->
          <div class="bottom-deco">
            <div class="deco-line"></div>
            <span class="deco-text">SECURE CONNECTION</span>
            <div class="deco-line"></div>
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'

const props = defineProps<{
  visible: boolean
}>()

const emit = defineEmits<{
  (e: 'update:visible', val: boolean): void
  (e: 'success'): void
}>()

const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const showPwd = ref(false)
const loading = ref(false)
const error = ref('')
const slideDirection = ref('slide-left')

let prevMode = 'login'

function switchMode(m: 'login' | 'register') {
  if (m === mode.value) return
  // 判断滑动方向：register→login 是往右，login→register 是往左
  slideDirection.value = m === 'register' ? 'slide-left' : 'slide-right'
  mode.value = m
  error.value = ''
}

watch(() => props.visible, (val) => {
  if (val) {
    username.value = ''
    password.value = ''
    error.value = ''
    loading.value = false
    showPwd.value = false
    mode.value = 'login'
    slideDirection.value = 'slide-left'
  }
})

function handleClose() {
  emit('update:visible', false)
}

async function handleSubmit() {
  if (!username.value || !password.value) {
    error.value = '请填写完整信息'
    return
  }
  if (password.value.length < 4) {
    error.value = '密码至少需要 4 位字符'
    return
  }

  loading.value = true
  error.value = ''

  try {
    const { login: apiLogin, register: apiRegister, fetchMe } = await import('@/api/auth')

    if (mode.value === 'login') {
      await apiLogin(username.value, password.value)
      const me = await fetchMe()
      localStorage.setItem('username', me.username || username.value)
      emit('update:visible', false)
      emit('success')
    } else {
      await apiRegister(username.value, password.value)
      error.value = '' // 注册成功
      // 自动切到登录
      setTimeout(() => { switchMode('login') }, 600)
    }
  } catch (e: any) {
    error.value = e?.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ═══ 遮罩层 ═══ */
.auth-overlay {
  position: fixed;
  inset: 0;
  z-index: 9999;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: blur(8px);
}
.grid-bg {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(16, 185, 129, 0.04) 1px, transparent 1px),
    linear-gradient(90deg, rgba(16, 185, 129, 0.04) 1px, transparent 1px);
  background-size: 40px 40px;
  mask-image: radial-gradient(circle at center, black 30%, transparent 80%);
}

/* ═══ 弹框主体 ═══ */
.auth-modal {
  position: relative;
  z-index: 1;
  width: 440px;
  max-width: 92vw;
  padding: 32px 36px 24px;
  border-radius: 20px;
  background: rgba(10, 15, 26, 0.9);
  border: 1px solid rgba(16, 185, 129, 0.15);
  box-shadow:
    0 0 60px rgba(16, 185, 129, 0.08),
    0 25px 60px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.05);
}
.auth-modal::before {
  content: '';
  position: absolute;
  top: -1px; left: 20%; right: 20%;
  height: 2px;
  border-radius: 2px;
  background: linear-gradient(90deg, transparent, #059669, #06b6d4, #059669, transparent);
  animation: scanline 3s ease-in-out infinite;
}
@keyframes scanline {
  0%, 100% { opacity: 0.5; }
  50% { opacity: 1; }
}

/* 关闭按钮 */
.close-btn {
  position: absolute;
  top: 14px; right: 14px;
  width: 32px; height: 32px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 8px;
  background: rgba(255, 255, 255, 0.03);
  color: rgba(148, 163, 184, 0.5);
  font-size: 13px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all 0.2s;
}
.close-btn:hover {
  color: #fca5a5;
  border-color: rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
}

/* ═══ 切换头部 ═══ */
.switch-header {
  margin-bottom: 28px;
}
.switch-track {
  display: flex;
  position: relative;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 12px;
  padding: 4px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.switch-indicator {
  position: absolute;
  top: 4px; left: 4px;
  width: calc(50% - 4px);
  height: calc(100% - 8px);
  border-radius: 9px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.15), rgba(6, 182, 212, 0.15));
  border: 1px solid rgba(16, 185, 129, 0.25);
  transition: transform 0.35s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 0 12px rgba(16, 185, 129, 0.1);
}
.switch-indicator.right {
  transform: translateX(100%);
}
.switch-btn {
  flex: 1;
  position: relative;
  z-index: 1;
  padding: 10px 0;
  border: none;
  border-radius: 9px;
  background: transparent;
  font-size: 14px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center; gap: 6px;
  color: rgba(148, 163, 184, 0.55);
  transition: all 0.25s;
}
.switch-btn.active {
  color: #34d399;
  text-shadow: 0 0 12px rgba(52, 211, 153, 0.4);
}
.btn-icon { font-size: 15px; }

/* ═══ 表单容器 ═══ */
.form-container {
  min-height: 260px;
  overflow: hidden;
}
.auth-form { padding: 0; }

.form-desc {
  font-size: 13px;
  color: rgba(148, 163, 184, 0.5);
  margin-bottom: 22px;
  letter-spacing: 0.5px;
}
.field-group {
  display: flex;
  flex-direction: column;
  gap: 18px;
}
.field label {
  display: block;
  font-size: 11.5px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  color: rgba(52, 211, 153, 0.7);
  margin-bottom: 8px;
}
.input-box {
  position: relative;
}
.box-icon {
  position: absolute;
  left: 14px; top: 50%; transform: translateY(-50%);
  font-size: 14px;
  opacity: 0.45;
  pointer-events: none;
  z-index: 1;
}
.input-box input {
  width: 100%;
  padding: 14px 44px 14px 42px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.02);
  color: #f1f5f9;
  font-size: 15px;
  outline: none;
  transition: all 0.25s;
  box-sizing: border-box;
}
.input-box input::placeholder { color: rgba(71, 85, 105, 0.6); }
.input-box input:focus {
  border-color: rgba(16, 185, 129, 0.4);
  background: rgba(16, 185, 129, 0.03);
  box-shadow: 0 0 20px rgba(16, 185, 129, 0.08);
}
.input-box input:disabled { opacity: 0.45; cursor: not-allowed; }
.pwd-toggle {
  position: absolute;
  right: 10px; top: 50%; transform: translateY(-50%);
  border: none;
  background: none;
  cursor: pointer;
  font-size: 14px;
  padding: 4px;
  opacity: 0.4;
  transition: opacity 0.2s;
}
.pwd-toggle:hover { opacity: 0.75; }

/* 底部发光线条 */
.input-line {
  position: absolute;
  bottom: 0; left: 10%; right: 10%;
  height: 1px;
  background: linear-gradient(90deg, transparent, #059669, transparent);
  opacity: 0;
  transition: opacity 0.3s;
}
.input-box input:focus ~ .input-line { opacity: 0.6; }

/* 错误提示条 */
.error-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 14px;
  margin-top: 18px;
  border-radius: 8px;
  background: rgba(239, 68, 68, 0.06);
  border: 1px solid rgba(239, 68, 68, 0.15);
  font-size: 13px;
  color: #fca5a5;
}
.error-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #ef4444;
  box-shadow: 0 0 6px #ef4444;
  animation: pulse-dot 1.2s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

/* ═══ 提交按钮（赛博风格） ═══ */
.action-btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 10px;
  font-size: 15px;
  font-weight: 800;
  letter-spacing: 4px;
  cursor: pointer;
  position: relative;
  overflow: hidden;
  margin-top: 22px;
  display: flex; align-items: center; justify-content: center;
  gap: 8px;
  transition: all 0.3s;
}
.login-btn {
  background: linear-gradient(135deg, #059669 0%, #047857 100%);
  color: #ecfdf5;
  box-shadow: 0 0 24px rgba(16, 185, 129, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}
.reg-btn {
  background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%);
  color: #ecfeff;
  box-shadow: 0 0 24px rgba(8, 145, 178, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.1);
}
.action-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  filter: brightness(1.1);
}
.action-btn:active:not(:disabled) { transform: translateY(0); }
.action-btn:disabled { opacity: 0.5; cursor: not-allowed; }
.btn-glow {
  position: absolute;
  top: 0; left: -100%;
  width: 60%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.15), transparent);
  animation: btn-shine 3s infinite;
}
@keyframes btn-shine {
  to { left: 200%; }
}
.spinner-mini {
  width: 18px; height: 18px;
  border: 2.5px solid rgba(255, 255, 255, 0.25);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.65s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═══ 底部装饰 ═══ */
.bottom-deco {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-top: 22px;
  padding-top: 18px;
  border-top: 1px solid rgba(255, 255, 255, 0.04);
}
.deco-line {
  flex: 1;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.15), transparent);
}
.deco-text {
  font-size: 9.5px;
  letter-spacing: 3px;
  color: rgba(16, 185, 129, 0.25);
  white-space: nowrap;
}

/* ═══ 过渡动画 ═══ */
.modal-fade-enter-active,
.modal-fade-leave-active {
  transition: all 0.3s ease;
}
.modal-fade-enter-from,
.modal-fade-leave-to {
  opacity: 0;
}
.modal-fade-enter-from .auth-modal,
.modal-fade-leave-to .auth-modal {
  transform: scale(0.95) translateY(16px);
  opacity: 0;
}

/* 左右滑动 */
.slide-left-enter-active,
.slide-left-leave-active,
.slide-right-enter-active,
.slide-right-leave-active {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}
.slide-left-enter-from {
  opacity: 0;
  transform: translateX(36px);
}
.slide-left-leave-to {
  opacity: 0;
  transform: translateX(-36px);
}
.slide-right-enter-from {
  opacity: 0;
  transform: translateX(-36px);
}
.slide-right-leave-to {
  opacity: 0;
  transform: translateX(36px);
}

.err-fade-enter-active,
.err-fade-leave-active { transition: all 0.25s; }
.err-fade-enter-from,
.err-fade-leave-to { opacity: 0; transform: translateY(-6px); }
</style>
