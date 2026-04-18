<template>
  <div class="login-page">
    <!-- 背景装饰 -->
    <div class="bg-decoration">
      <div class="bg-orb bg-orb-1"></div>
      <div class="bg-orb bg-orb-2"></div>
      <div class="bg-orb bg-orb-3"></div>
    </div>

    <!-- 登录卡片 -->
    <div class="login-card">
      <!-- 品牌 Logo 区域 -->
      <div class="brand-area">
        <div class="brand-icon">
          <svg width="44" height="44" viewBox="0 0 48 48" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect width="48" height="48" rx="14" fill="url(#g1)"/>
            <path d="M16 30V18l8 6-8 6z" fill="#fff" opacity=".9"/>
            <path d="M24 30l8-6v12h-8V30z" fill="#fff" opacity=".5"/>
            <defs>
              <linearGradient id="g1" x1="0" y1="0" x2="48" y2="48">
                <stop stop-color="#10b981"/>
                <stop offset="1" stop-color="#059669"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h1 class="brand-title">大宗绿测</h1>
        <p class="brand-subtitle">油价预测与绿色金融平台</p>
      </div>

      <!-- 登录 / 注册 切换 -->
      <div class="mode-switch">
        <button
          :class="['mode-tab', { active: mode === 'login' }]"
          @click="switchMode('login')"
        >登录</button>
        <button
          :class="['mode-tab', { active: mode === 'register' }]"
          @click="switchMode('register')"
        >注册</button>
      </div>

      <!-- 表单 -->
      <form class="login-form" @submit.prevent="handleSubmit">
        <div class="field">
          <label for="username">用户名</label>
          <div class="input-wrap">
            <span class="input-icon">👤</span>
            <input
              id="username"
              v-model="username"
              type="text"
              placeholder="请输入用户名"
              autocomplete="username"
              :disabled="loading"
            />
          </div>
        </div>

        <div class="field">
          <label for="password">密码</label>
          <div class="input-wrap">
            <span class="input-icon">🔒</span>
            <input
              id="password"
              v-model="password"
              :type="showPwd ? 'text' : 'password'"
              placeholder="请输入密码"
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              :disabled="loading"
            />
            <button
              type="button"
              class="pwd-toggle"
              @click="showPwd = !showPwd"
              tabindex="-1"
            >
              {{ showPwd ? '🙈' : '👁️' }}
            </button>
          </div>
        </div>

        <!-- 错误提示 -->
        <transition name="fade">
          <div v-if="error" class="error-msg">{{ error }}</div>
        </transition>

        <!-- 提交按钮 -->
        <button type="submit" class="submit-btn" :disabled="loading">
          <span v-if="loading" class="spinner"></span>
          {{ loading ? '处理中...' : (mode === 'login' ? '登 录' : '注 册') }}
        </button>
      </form>

      <!-- 底部信息 -->
      <p class="footer-text">© 2025 大宗绿测 · 绿色金融预测平台</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { login as apiLogin, register as apiRegister, fetchMe } from '@/api/auth'

const router = useRouter()

// ── 状态 ──
const mode = ref<'login' | 'register'>('login')
const username = ref('')
const password = ref('')
const showPwd = ref(false)
const loading = ref(false)
const error = ref('')

function switchMode(m: 'login' | 'register') {
  mode.value = m
  error.value = ''
  username.value = ''
  password.value = ''
}

async function handleSubmit() {
  if (!username.value || !password.value) {
    error.value = '请输入用户名和密码'
    return
  }
  if (password.value.length < 4) {
    error.value = '密码至少 4 位字符'
    return
  }

  loading.value = true
  error.value = ''

  try {
    if (mode.value === 'login') {
      await apiLogin(username.value, password.value)
      const me = await fetchMe()
      localStorage.setItem('username', me.username || username.value)
      router.replace({ name: 'Home' })
    } else {
      await apiRegister(username.value, password.value)
      mode.value = 'login'
      error.value = '' // 注册成功后清空错误，不显示成功消息（保持简洁）
      // 自动切到登录模式，让用户直接登录
    }
  } catch (e: any) {
    error.value = e?.message || '操作失败，请重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ═══ 页面容器 ═══ */
.login-page {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #0a0f1a;
  overflow: hidden;
}

/* ═══ 背景装饰球体 ═══ */
.bg-decoration {
  position: absolute;
  inset: 0;
  pointer-events: none;
}
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(100px);
  opacity: 0.35;
  animation: float 20s ease-in-out infinite;
}
.bg-orb-1 {
  width: 500px; height: 500px;
  top: -120px; right: -80px;
  background: radial-gradient(circle, #059669 0%, transparent 70%);
  animation-delay: 0s;
}
.bg-orb-2 {
  width: 400px; height: 400px;
  bottom: -80px; left: -60px;
  background: radial-gradient(circle, #0891b2 0%, transparent 70%);
  animation-delay: -7s;
}
.bg-orb-3 {
  width: 300px; height: 300px;
  top: 40%; left: 50%; transform: translateX(-50%);
  background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
  opacity: 0.15;
  animation-delay: -14s;
}
@keyframes float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(30px, -20px) scale(1.05); }
  66% { transform: translate(-20px, 15px) scale(0.95); }
}

/* ═══ 登录卡片 ═══ */
.login-card {
  position: relative;
  z-index: 1;
  width: 420px;
  max-width: 90vw;
  padding: 42px 36px 32px;
  border-radius: 24px;
  background: rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(24px);
  -webkit-backdrop-filter: blur(24px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow:
    0 24px 80px rgba(0, 0, 0, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}
.login-card:hover {
  transform: translateY(-2px);
  box-shadow:
    0 28px 90px rgba(0, 0, 0, 0.5),
    inset 0 1px 0 rgba(255, 255, 255, 0.09);
}

/* ═══ 品牌区域 ═══ */
.brand-area {
  text-align: center;
  margin-bottom: 28px;
}
.brand-icon {
  display: inline-flex;
  margin-bottom: 14px;
  filter: drop-shadow(0 4px 16px rgba(16, 185, 129, 0.35));
}
.brand-title {
  font-size: 26px;
  font-weight: 700;
  color: #f0fdf4;
  letter-spacing: 3px;
  margin: 0 0 6px;
  text-shadow: 0 2px 12px rgba(16, 185, 129, 0.25);
}
.brand-subtitle {
  font-size: 13px;
  color: rgba(148, 163, 184, 0.7);
  margin: 0;
  letter-spacing: 1px;
}

/* ═══ 模式切换 ═══ */
.mode-switch {
  display: flex;
  gap: 0;
  margin-bottom: 28px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 12px;
  padding: 4px;
  border: 1px solid rgba(255, 255, 255, 0.06);
}
.mode-tab {
  flex: 1;
  padding: 9px 0;
  border: none;
  border-radius: 9px;
  background: transparent;
  color: rgba(148, 163, 184, 0.7);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s ease;
}
.mode-tab.active {
  background: linear-gradient(135deg, #059669, #0891b2);
  color: #fff;
  box-shadow: 0 2px 12px rgba(16, 185, 129, 0.3);
}
.mode-tab:not(.active):hover {
  color: #e2e8f0;
  background: rgba(255, 255, 255, 0.06);
}

/* ═══ 表单字段 ═══ */
.login-form .field {
  margin-bottom: 18px;
}
.login-form label {
  display: block;
  font-size: 13px;
  font-weight: 600;
  color: rgba(203, 213, 225, 0.7);
  margin-bottom: 7px;
  letter-spacing: 0.5px;
}
.input-wrap {
  position: relative;
  display: flex;
  align-items: center;
}
.input-icon {
  position: absolute;
  left: 14px;
  font-size: 15px;
  pointer-events: none;
  z-index: 1;
  opacity: 0.55;
}
.input-wrap input {
  width: 100%;
  padding: 13px 14px 13px 42px;
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 12px;
  background: rgba(255, 255, 255, 0.04);
  color: #f1f5f9;
  font-size: 15px;
  outline: none;
  transition: all 0.25s ease;
  box-sizing: border-box;
}
.input-wrap input::placeholder {
  color: rgba(100, 116, 139, 0.6);
}
.input-wrap input:focus {
  border-color: rgba(16, 185, 129, 0.5);
  background: rgba(255, 255, 255, 0.07);
  box-shadow: 0 0 0 3px rgba(16, 185, 129, 0.1);
}
.input-wrap input:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.pwd-toggle {
  position: absolute;
  right: 10px;
  border: none;
  background: none;
  cursor: pointer;
  font-size: 15px;
  padding: 4px;
  opacity: 0.5;
  transition: opacity 0.2s;
}
.pwd-toggle:hover {
  opacity: 0.85;
}

/* ═══ 错误提示 ═══ */
.error-msg {
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.2);
  color: #fca5a5;
  font-size: 13.5px;
  margin-bottom: 16px;
}
.fade-enter-active,
.fade-leave-active { transition: opacity 0.25s; }
.fade-enter-from,
.fade-leave-to { opacity: 0; }

/* ═══ 提交按钮 ═══ */
.submit-btn {
  width: 100%;
  padding: 14px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #059669 0%, #0891b2 100%);
  color: #fff;
  font-size: 16px;
  font-weight: 700;
  letter-spacing: 3px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(16, 185, 129, 0.3);
  margin-top: 6px;
}
.submit-btn:hover:not(:disabled) {
  transform: translateY(-1px);
  box-shadow: 0 6px 28px rgba(16, 185, 129, 0.4);
}
.submit-btn:active:not(:disabled) {
  transform: translateY(0);
}
.submit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

/* ═══ 加载动画 spinner ═══ */
.spinner {
  width: 18px;
  height: 18px;
  border: 2.5px solid rgba(255, 255, 255, 0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.65s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* ═══ 底部文字 ═══ */
.footer-text {
  text-align: center;
  font-size: 11.5px;
  color: rgba(71, 85, 105, 0.6);
  margin: 22px 0 0;
  letter-spacing: 0.5px;
}
</style>
