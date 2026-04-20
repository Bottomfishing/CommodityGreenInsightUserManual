<template>
  <Teleport to="body">
    <transition name="auth-fade">
      <div v-if="visible" class="auth-overlay" @click.self="handleClose">
        <div class="auth-card">
          <!-- 关闭 -->
          <button class="auth-close" @click="handleClose">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none"><path d="M12 4L4 12M4 4l8 8" stroke="currentColor" stroke-width="1.5" stroke-linecap="round"/></svg>
          </button>

          <!-- 品牌头部 -->
          <div class="auth-header">
            <div class="auth-logo"></div>
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
              <div class="field">
                <label for="login-password">密码</label>
                <div class="pw-wrap">
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
                <div v-if="error" class="err-msg">{{ error }}</div>
              </transition>

              <button type="submit" class="submit-btn" :disabled="loading">
                <span v-if="loading" class="spin"></span>
                <span v-else>登 录</span>
              </button>

              <p class="switch-hint">
                还没有账号？
                <a href="javascript:void(0)" @click.prevent="switchTo('register')">立即注册</a>
              </p>
            </form>

            <form v-else key="register" class="auth-form" @submit.prevent="handleSubmit">
              <div class="field">
                <label for="reg-username">用户名</label>
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
              <div class="field">
                <label for="reg-password">密码</label>
                <div class="pw-wrap">
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

              <transition name="msg-slide">
                <div v-if="error" class="err-msg">{{ error }}</div>
              </transition>

              <button type="submit" class="submit-btn" :disabled="loading">
                <span v-if="loading" class="spin"></span>
                <span v-else>注 册</span>
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
          </div>
        </div>
      </div>
    </transition>
  </Teleport>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'

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
    nextTick(() => { inputFocus.value?.focus() })
  }
})

function handleClose() { emit('update:visible', false) }

async function handleSubmit() {
  if (!username.value || !password.value) { error.value = '请输入用户名和密码'; return }
  if (password.value.length < 4) { error.value = '密码至少需要 4 位字符'; return }
  loading.value = true; error.value = ''
  try {
    const { login: apiLogin, register: apiRegister, fetchMe } = await import('@/api/auth')
    if (mode.value === 'login') {
      await apiLogin(username.value, password.value)
      const me = await fetchMe()
      localStorage.setItem('username', me.username || username.value)
      emit('update:visible', false); emit('success')
    } else {
      await apiRegister(username.value, password.value)
      switchTo('login') // 注册成功自动切回登录
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
  background: rgba(3, 7, 18, 0.65);
  backdrop-filter: blur(6px);
  -webkit-backdrop-filter: blur(6px);
}
.auth-overlay::before {
  content: '';
  position: absolute;
  top: -50%; left: -50%; width: 200%; height: 200%;
  background: radial-gradient(circle at center, rgba(52,211,153,.03), transparent 60%);
  pointer-events: none;
}

/* ═══ 卡片主体 ═══ */
.auth-card {
  position: relative;
  width: 400px;
  max-width: 92vw;
  padding: 40px 36px 28px;
  border-radius: 20px;
  background: #0f141e;
  border: 1px solid rgba(255,255,255,.06);
  box-shadow:
    0 32px 80px rgba(0,0,0,.45),
    0 0 1px rgba(255,255,255,.04) inset,
    0 1px 0 rgba(255,255,255,.03) inset;
}

/* 关闭按钮 — 精致圆形 */
.auth-close {
  position: absolute;
  top: 16px; right: 16px;
  width: 30px; height: 30px;
  border-radius: 50%;
  border: none;
  background: transparent;
  color: #64748b;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .2s;
}
.auth-close:hover {
  color: #cbd5e1;
  background: rgba(255,255,255,.06);
}

/* ═══ 头部 ═══ */
.auth-header {
  margin-bottom: 32px;
  text-align: center;
}
.auth-logo {
  width: 44px; height: 44px;
  margin: 0 auto 18px;
  border-radius: 13px;
  background: linear-gradient(135deg, #059669, #0891b2);
  opacity: .88;
}
.auth-heading {
  font-size: 22px;
  font-weight: 700;
  color: #f1f5f9;
  letter-spacing: -.3px;
  margin-bottom: 6px;
}
.auth-sub {
  font-size: 14px;
  color: #64748b;
  line-height: 1.5;
}

/* ═══ 表单字段 ═══ */
.auth-form .field {
  margin-bottom: 18px;
}
.auth-form label {
  display: block;
  font-size: 12.5px;
  font-weight: 600;
  color: #94a3b8;
  margin-bottom: 7px;
  letter-spacing: .3px;
}
.auth-form input[type="text"],
.auth-form input[type="password"] {
  width: 100%;
  height: 46px;
  padding: 0 14px;
  border: 1px solid rgba(255,255,255,.09);
  border-radius: 10px;
  background: rgba(255,255,255,.03);
  color: #e2e8f0;
  font-size: 15px;
  outline: none;
  transition: all .2s ease;
  box-sizing: border-box;
}
.auth-form input::placeholder { color: #475569; font-size: 14px; }
.auth-form input:focus {
  border-color: #059669;
  background: rgba(5,150,105,.04);
  box-shadow: 0 0 0 3px rgba(5,150,105,.1);
}
.auth-form input:disabled { opacity: .45; cursor: not-allowed; }

.pw-wrap { position: relative; }
.pw-wrap input { padding-right: 42px; }

.pw-toggle {
  position: absolute; right: 8px; top: 50%; transform: translateY(-50%);
  border: none; background: none;
  cursor: pointer; padding: 6px;
  color: #64748b; transition: color .15s;
  display: flex; align-items: center;
}
.pw-toggle:hover { color: #94a3b8; }

/* 错误 */
.err-msg {
  padding: 10px 14px;
  border-radius: 9px;
  background: rgba(220,38,38,.06);
  border: 1px solid rgba(220,38,38,.12);
  color: #fca5a5;
  font-size: 13px;
  margin-bottom: 16px;
}

/* ═══ 提交按钮 ═══ */
.submit-btn {
  width: 100%; height: 46px;
  border: none; border-radius: 10px;
  background: linear-gradient(135deg, #059669, #047857);
  color: #fff;
  font-size: 15px; font-weight: 600;
  letter-spacing: 2px;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  transition: all .25s;
  box-shadow: 0 4px 16px rgba(5,150,105,.22);
  margin-top: 4px;
}
.submit-btn:hover:not(:disabled) {
  filter: brightness(1.08);
  transform: translateY(-1px);
  box-shadow: 0 6px 24px rgba(5,150,105,.32);
}
.submit-btn:active:not(:disabled) { transform: translateY(0); }
.submit-btn:disabled { opacity: .55; cursor: not-allowed; }

.spin {
  width: 18px; height: 18px;
  border: 2.5px solid rgba(255,255,255,.25);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin .6s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

/* 切换提示 */
.switch-hint {
  text-align: center;
  margin-top: 20px;
  font-size: 13.5px;
  color: #64748b;
}
.switch-hint a {
  color: #34d399;
  text-decoration: none;
  font-weight: 600;
  margin-left: 3px;
  transition: color .15s;
}
.switch-hint a:hover { color: #6ee7b7; }

/* ═══ 底部 ═══ */
.auth-footer {
  display: flex; align-items: center; gap: 6px;
  justify-content: center;
  margin-top: 26px;
  padding-top: 20px;
  border-top: 1px solid rgba(255,255,255,.045);
  font-size: 11.5px;
  color: #475569;
  letter-spacing: .3px;
}
.auth-footer svg { flex-shrink: 0; opacity: .5; }

/* ═══ 过渡动画 ═══ */
.auth-fade-enter-active { transition: all .3s ease; }
.auth-fade-leave-active { transition: all .2s ease; }
.auth-fade-enter-from, .auth-fade-leave-to { opacity: 0; }
.auth-fade-enter-from .auth-card,
.auth-fade-leave-to .auth-card {
  transform: scale(.96) translateY(12px);
  opacity: 0;
}

/* 左右滑动 */
.slide-l-enter-active, .slide-l-leave-active,
.slide-r-enter-active, .slide-r-leave-active {
  transition: all .28s cubic-bezier(.4,0,.2,1);
}
.slide-l-enter-from { opacity: 0; transform: translateX(24px); }
.slide-l-leave-to   { opacity: 0; transform: translateX(-24px); }
.slide-r-enter-from { opacity: 0; transform: translateX(-24px); }
.slide-r-leave-to   { opacity: 0; transform: translateX(24px); }

.msg-slide-enter-active, .msg-slide-leave-active { transition: all .2s; }
.msg-slide-enter-from, .msg-slide-leave-to { opacity: 0; transform: translateY(-8px); }
</style>
