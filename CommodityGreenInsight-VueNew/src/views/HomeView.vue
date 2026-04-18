<template>
  <div class="home-page">
    <div class="home-header">
      <h1>👋 欢迎，{{ username }}</h1>
      <p class="subtitle">大宗绿测 · 油价预测与绿色金融平台</p>
    </div>

    <div class="home-body">
      <div class="placeholder-card">
        <span class="placeholder-icon">🚀</span>
        <p>网站主页面正在建设中...</p>
        <button class="logout-btn" @click="handleLogout">退出登录</button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { clearToken } from '@/api/auth'

const router = useRouter()
const username = localStorage.getItem('username') || '用户'

function handleLogout() {
  clearToken()
  router.push({ name: 'Login' })
}
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  background: #0a0f1a;
  color: #f1f5f9;
}
.home-header {
  padding: 40px 32px 24px;
  background: rgba(255, 255, 255, 0.02);
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
}
.home-header h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
}
.subtitle {
  margin: 8px 0 0;
  font-size: 14px;
  color: rgba(148, 163, 184, 0.7);
}
.home-body {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: calc(100vh - 140px);
  padding: 32px;
}
.placeholder-card {
  text-align: center;
  padding: 60px 48px;
  border-radius: 20px;
  border: 1px dashed rgba(255, 255, 255, 0.12);
  background: rgba(255, 255, 255, 0.02);
}
.placeholder-icon {
  font-size: 48px;
  display: block;
  margin-bottom: 16px;
}
.placeholder-card p {
  font-size: 16px;
  color: rgba(148, 163, 184, 0.6);
  margin: 0 0 28px;
}
.logout-btn {
  padding: 10px 28px;
  border-radius: 10px;
  border: 1px solid rgba(239, 68, 68, 0.3);
  background: rgba(239, 68, 68, 0.08);
  color: #fca5a5;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.2s;
}
.logout-btn:hover {
  background: rgba(239, 68, 68, 0.15);
  border-color: rgba(239, 68, 68, 0.5);
}
</style>
