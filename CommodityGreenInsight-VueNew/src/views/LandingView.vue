<template>
  <div class="landing-page">
    <!-- 背景层 -->
    <div class="bg-layer">
      <!-- 动态网格 -->
      <div class="grid-lines">
        <div v-for="i in 12" :key="'h'+i" class="grid-h" :style="{top: (i * 8.33) + '%'}"></div>
        <div v-for="i in 16" :key="'v'+i" class="grid-v" :style="{left: (i * 6.25) + '%'}"></div>
      </div>

      <!-- 光球装饰 -->
      <div class="orb orb-1"></div>
      <div class="orb orb-2"></div>
      <div class="orb orb-3"></div>
      <div class="orb orb-4"></div>

      <!-- 粒子 -->
      <div v-for="(p, i) in particles" :key="i"
           :class="['particle', `particle-${(i % 3) + 1}`]"
           :style="{
             left: p.x + '%',
             top: p.y + '%',
             animationDelay: p.d + 's',
             animationDuration: (3 + (i % 4)) + 's'
           }"></div>

      <!-- 扫描线效果 -->
      <div class="scan-line"></div>
    </div>

    <!-- 主内容 -->
    <main class="main-content">
      <!-- 顶部导航条 -->
      <nav class="top-bar">
        <div class="logo-area">
          <span class="logo-icon">◆</span>
          <span class="logo-text">大宗绿测</span>
        </div>
      </nav>

      <!-- Hero 区域 -->
      <section class="hero-section">
        <!-- 副标题标签 -->
        <div class="hero-tag">
          <span class="tag-dot"></span> GREEN FINTECH PLATFORM
        </div>

        <!-- 主标题 -->
        <h1 class="hero-title">
          <span class="title-line">大宗绿测</span>
          <span class="title-sub">基于油价因子的绿色金融产品预测与风险分析</span>
        </h1>

        <!-- 特性列表 -->
        <div class="feature-list">
          <div class="feature-item">
            <span class="feat-num">01</span>
            <span class="feat-label">油价预测 · GRU 深度学习模型</span>
          </div>
          <div class="feature-item">
            <span class="feat-num">02</span>
            <span class="feat-label">新能源股票收益预测</span>
          </div>
          <div class="feature-item">
            <span class="feat-num">03</span>
            <span class="feat-label">绿色债券风险评估</span>
          </div>
          <div class="feature-item">
            <span class="feat-num">04</span>
            <span class="feat-label">AI 智能报告生成</span>
          </div>
        </div>

        <!-- CTA 按钮 -->
        <div class="cta-group">
          <button class="cta-primary" @click="showAuth = true">
            <span class="cta-glow"></span>
            <span class="cta-text">立即开始</span>
            <span class="cta-arrow">→</span>
          </button>
          <button class="cta-secondary" @click="openManual">
            <span class="cta-icon">📖</span>
            用户手册
          </button>
        </div>
      </section>

      <!-- 底部信息 -->
      <footer class="bottom-info">
        <span>© 2025 大宗绿测</span>
        <span class="divider">|</span>
        <span>Powered by Deep Learning</span>
        <span class="divider">|</span>
        <span>SECURE CONNECTION</span>
      </footer>
    </main>

    <!-- 登录/注册弹框 -->
    <AuthModal
      :visible="showAuth"
      @update:visible="showAuth = $event"
      @success="onAuthSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import AuthModal from '@/components/AuthModal.vue'
import { getToken } from '@/api/auth'

const router = useRouter()
const showAuth = ref(false)

// ── 粒子数据 ──
const particles = Array.from({ length: 20 }, (_, i) => ({
  x: Math.random() * 100,
  y: Math.random() * 100,
  d: Math.random() * 3,
}))

function openManual() {
  window.open('/用户手册.pdf', '_blank')
}

function onAuthSuccess() {
  router.push({ name: 'Home' })
}

// 已登录则直接跳转
onMounted(() => {
  if (getToken()) {
    router.replace({ name: 'Home' })
  }
})
</script>

<style scoped>
/* ═══ 页面容器 ═══ */
.landing-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #060b14;
}

/* ═══ 背景层 ═══ */
.bg-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
}
.grid-lines .grid-h,
.grid-lines .grid-v {
  position: absolute;
  background: rgba(16, 185, 129, 0.025);
}
.grid-lines .grid-h { width: 100%; height: 1px; left: 0; }
.grid-lines .grid-v { height: 100%; width: 1px; top: 0; }

.orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  animation: orb-float 25s ease-in-out infinite;
}
.orb-1 {
  width: 600px; height: 600px;
  top: -200px; right: -150px;
  background: radial-gradient(circle, rgba(16, 185, 129, 0.2), transparent 70%);
}
.orb-2 {
  width: 450px; height: 450px;
  bottom: -100px; left: -80px;
  background: radial-gradient(circle, rgba(8, 145, 178, 0.15), transparent 70%);
  animation-delay: -8s;
}
.orb-3 {
  width: 300px; height: 300px;
  top: 50%; left: 30%;
  transform: translate(-50%, -50%);
  background: radial-gradient(circle, rgba(6, 182, 212, 0.08), transparent 70%);
  animation-delay: -16s;
}
.orb-4 {
  width: 200px; height: 200px;
  bottom: 20%; right: 10%;
  background: radial-gradient(circle, rgba(139, 92, 246, 0.06), transparent 70%);
  animation-delay: -12s;
}
@keyframes orb-float {
  0%, 100% { transform: translate(0, 0) scale(1); }
  33% { transform: translate(40px, -30px) scale(1.05); }
  66% { transform: translate(-30px, 20px) scale(0.95); }
}

/* 粒子 */
.particle {
  position: absolute;
  border-radius: 50%;
  opacity: 0;
  animation: particle-drift infinite ease-in-out alternate;
}
.particle-1 {
  width: 3px; height: 3px;
  background: #34d399;
  box-shadow: 0 0 6px #34d399;
}
.particle-2 {
  width: 2px; height: 2px;
  background: #22d3ee;
  box-shadow: 0 0 4px #22d3ee;
}
.particle-3 {
  width: 4px; height: 4px;
  background: rgba(16, 185, 129, 0.5);
}
@keyframes particle-drift {
  0% { opacity: 0; transform: translateY(0); }
  20% { opacity: 0.6; }
  80% { opacity: 0.3; }
  100% { opacity: 0; transform: translateY(-40px) translateX(20px); }
}

/* 扫描线 */
.scan-line {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 2px;
  background: linear-gradient(90deg, transparent, rgba(16, 185, 129, 0.3), transparent);
  animation: scan-down 8s linear infinite;
}
@keyframes scan-down {
  0% { top: 0; opacity: 0; }
  5% { opacity: 1; }
  95% { opacity: 1; }
  100% { top: 100%; opacity: 0; }
}

/* ═══ 主内容区（相对定位在背景之上）═══ */
.main-content {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ═══ 顶部导航 ═══ */
.top-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24px 36px;
}
.logo-area {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo-icon {
  font-size: 18px;
  color: #34d399;
  text-shadow: 0 0 12px rgba(52, 211, 153, 0.5);
  letter-spacing: 2px;
}
.logo-text {
  font-size: 17px;
  font-weight: 700;
  color: #f0fdf4;
  letter-spacing: 3px;
}

/* ═══ Hero 区域 ═══ */
.hero-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px 24px 32px;
  text-align: center;
}

.hero-tag {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 7px 18px;
  border-radius: 100px;
  border: 1px solid rgba(16, 185, 129, 0.15);
  background: rgba(16, 185, 129, 0.05);
  margin-bottom: 28px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 3px;
  color: rgba(52, 211, 153, 0.7);
}
.tag-dot {
  width: 6px; height: 6px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 8px #34d399;
  animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}

.hero-title {
  margin-bottom: 36px;
}
.title-line {
  display: block;
  font-size: clamp(38px, 7vw, 64px);
  font-weight: 800;
  color: #ecfdf5;
  letter-spacing: 8px;
  line-height: 1.2;
  background: linear-gradient(135deg, #ecfdf5 0%, #a7f3d0 40%, #34d399 70%, #22d3ee 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.title-sub {
  display: block;
  margin-top: 14px;
  font-size: clamp(13px, 2vw, 17px);
  font-weight: 400;
  color: rgba(148, 163, 184, 0.55);
  letter-spacing: 3px;
}

.feature-list {
  display: flex;
  flex-wrap: wrap;
  justify-content: center;
  gap: 14px 32px;
  max-width: 650px;
  margin-bottom: 44px;
}
.feature-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 18px;
  border-radius: 10px;
  border: 1px solid rgba(255, 255, 255, 0.04);
  background: rgba(255, 255, 255, 0.015);
}
.feat-num {
  font-size: 11px;
  font-weight: 800;
  color: rgba(16, 185, 129, 0.45);
  letter-spacing: 1px;
}
.feat-label {
  font-size: 13px;
  color: rgba(203, 213, 225, 0.65);
  white-space: nowrap;
}

.cta-group {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

/* 主要按钮 */
.cta-primary {
  position: relative;
  overflow: hidden;
  padding: 16px 48px;
  border: 1px solid rgba(16, 185, 129, 0.3);
  border-radius: 14px;
  background: linear-gradient(135deg, rgba(16, 185, 129, 0.12), rgba(6, 182, 212, 0.08));
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 10px;
  transition: all 0.3s;
  box-shadow:
    0 0 30px rgba(16, 185, 129, 0.12),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);
}
.cta-glow {
  position: absolute;
  top: 0; left: -60%;
  width: 50%; height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.1), transparent);
  animation: cta-shine 4s infinite;
}
@keyframes cta-shine {
  to { left: 180%; }
}
.cta-text {
  font-size: 16px;
  font-weight: 800;
  letter-spacing: 4px;
  color: #34d399;
  text-shadow: 0 0 16px rgba(52, 211, 153, 0.4);
  position: relative;
  z-index: 1;
}
.cta-arrow {
  font-size: 18px;
  color: #34d399;
  transition: transform 0.3s;
  position: relative;
  z-index: 1;
}
.cta-primary:hover {
  border-color: rgba(16, 185, 129, 0.5);
  box-shadow:
    0 0 48px rgba(16, 185, 129, 0.2),
    inset 0 1px 0 rgba(255, 255, 255, 0.09);
  transform: translateY(-2px);
}
.cta-primary:hover .cta-arrow { transform: translateX(4px); }

/* 次要按钮 */
.cta-secondary {
  padding: 16px 32px;
  border: 1px solid rgba(255, 255, 255, 0.07);
  border-radius: 14px;
  background: rgba(255, 255, 255, 0.02);
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14.5px;
  font-weight: 600;
  color: rgba(148, 163, 184, 0.6);
  letter-spacing: 1px;
  transition: all 0.25s;
}
.cta-icon { font-size: 15px; }
.cta-secondary:hover {
  border-color: rgba(255, 255, 255, 0.14);
  background: rgba(255, 255, 255, 0.04);
  color: rgba(203, 213, 225, 0.85);
  transform: translateY(-1px);
}

/* 底部 */
.bottom-info {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 20px;
  font-size: 11px;
  letter-spacing: 1px;
  color: rgba(71, 85, 105, 0.4);
}
.divider { opacity: 0.3; }

/* ═══ 响应式 ═══ */
@media (max-width: 640px) {
  .top-bar { padding: 18px 20px; }
  .feature-list { flex-direction: column; align-items: stretch; gap: 8px; }
  .feature-item { justify-content: center; }
  .cta-group { flex-direction: column; width: 100%; max-width: 300px; }
  .cta-primary, .cta-secondary { width: 100%; justify-content: center; }
  .bottom-info { flex-direction: column; gap: 4px; }
  .divider { display: none; }
}
</style>
