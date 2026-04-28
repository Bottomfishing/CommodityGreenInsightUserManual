<template>
  <div class="intro2-page">
    <div class="bg-layer" aria-hidden="true">
      <div class="bg-base"></div>
      <div class="bg-energy"></div>
      <div class="bg-aurora bg-aurora-a"></div>
      <div class="bg-aurora bg-aurora-b"></div>
      <div class="bg-grid"></div>
      <div class="bg-scanline"></div>
      <div class="bg-vignette"></div>
      <canvas ref="particleRef" class="particle-canvas"></canvas>
    </div>

    <main class="intro2-main">
      <section class="hero">
        <span class="kicker">GREEN FINTECH</span>
        <h1 class="hero-title">您可以在本web看到精美的可视化图表</h1>
        <p class="hero-sub">实时监控 · 趋势洞察 · 多指标对比 · 结果可复盘</p>
        <div class="action-row">
          <button class="btn-primary" @click="goNext">继续</button>
          <button class="btn-ghost" @click="router.push({ name: 'Intro' })">返回上一页</button>
        </div>
      </section>

      <section class="showcase">
        <article
          class="panel chart-panel"
          :style="chartBoardStyle"
          @mousemove="onChartMove"
          @mouseleave="onChartLeave"
        >
          <div class="panel-head">
            <span class="tag">可视化预览（示例）</span>
            <span class="live"><i></i>LIVE</span>
          </div>
          <div class="chart-frame">
            <svg viewBox="0 0 1000 190" preserveAspectRatio="none" class="trend-svg">
              <g class="trend-gridline">
                <line x1="36" y1="26" x2="980" y2="26" />
                <line x1="36" y1="60" x2="980" y2="60" />
                <line x1="36" y1="94" x2="980" y2="94" />
                <line x1="36" y1="128" x2="980" y2="128" />
                <line x1="36" y1="162" x2="980" y2="162" />
              </g>
              <line class="trend-axis" x1="36" y1="162" x2="980" y2="162" />
              <line class="trend-axis" x1="36" y1="22" x2="36" y2="162" />
              <rect class="forecast-band" x="610" y="22" width="16" height="140" />
              <path
                class="trend-line trend-line-a"
                d="M36,124 C78,140 110,158 144,140 C180,120 212,88 246,72 C280,56 316,74 350,92 C388,112 424,98 460,86 C496,74 532,84 568,94 C604,104 640,90 676,78 C712,66 748,76 784,92 C820,108 856,92 892,84 C928,76 960,78 980,74"
              />
              <path
                class="trend-line trend-line-b"
                d="M36,132 C78,146 110,162 144,146 C178,128 212,96 246,80 C282,62 316,84 350,100 C388,120 424,108 460,96 C496,84 532,94 568,104 C604,114 640,100 676,88 C712,76 748,86 784,102 C820,116 856,104 892,96 C928,88 960,90 980,86"
              />
              <circle class="trend-point trend-point-a" cx="980" cy="74" r="4" />
              <circle class="trend-point trend-point-b" cx="980" cy="86" r="4" />
            </svg>
            <div class="chart-legend">
              <span class="legend-item"><i class="legend-dot legend-dot-a"></i>actual</span>
              <span class="legend-item"><i class="legend-dot legend-dot-b"></i>pred</span>
            </div>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const particleRef = ref<HTMLCanvasElement | null>(null);
const chartBoardStyle = ref<Record<string, string>>({});

let rafId: number | null = null;
let particles: Array<{ x: number; y: number; vx: number; vy: number; r: number; a: number }> = [];
let removeResize: (() => void) | null = null;

function initParticles() {
  const canvas = particleRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const count = Math.max(30, Math.floor((canvas.width * canvas.height) / 52000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.22,
      vy: (Math.random() - 0.5) * 0.22,
      r: Math.random() * 1.6 + 0.6,
      a: Math.random() * 0.35 + 0.12,
    }));
  };
  resize();
  window.addEventListener("resize", resize);
  removeResize = () => window.removeEventListener("resize", resize);

  const tick = () => {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    for (const p of particles) {
      p.x += p.vx;
      p.y += p.vy;
      if (p.x < -8) p.x = canvas.width + 8;
      if (p.x > canvas.width + 8) p.x = -8;
      if (p.y < -8) p.y = canvas.height + 8;
      if (p.y > canvas.height + 8) p.y = -8;
      ctx.beginPath();
      ctx.fillStyle = `rgba(125, 211, 252, ${p.a})`;
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fill();
    }
    rafId = requestAnimationFrame(tick);
  };
  tick();
}

function goNext() {
  router.push({ name: "IntroData" });
}

function onChartMove(event: MouseEvent) {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const rx = ((y / rect.height) * 2 - 1) * -4.2;
  const ry = ((x / rect.width) * 2 - 1) * 4.8;
  chartBoardStyle.value = {
    transform: `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg)`,
  };
}

function onChartLeave() {
  chartBoardStyle.value = {
    transition: "transform .5s cubic-bezier(.22,1,.36,1)",
    transform: "perspective(1000px) rotateX(0) rotateY(0)",
  };
}

onMounted(() => {
  initParticles();
});
onBeforeUnmount(() => {
  if (rafId != null) cancelAnimationFrame(rafId);
  removeResize?.();
});
</script>

<style scoped>
.intro2-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #e2e8f0;
}
.bg-layer {
  position: absolute;
  inset: 0;
}
.bg-base {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(circle at 18% 22%, rgba(14, 116, 144, 0.2), transparent 34%),
    radial-gradient(circle at 82% 18%, rgba(99, 102, 241, 0.2), transparent 36%),
    linear-gradient(145deg, #030712 0%, #06122a 48%, #071634 76%, #040a19 100%);
  animation: baseDrift 20s ease-in-out infinite alternate;
}
.bg-energy {
  position: absolute;
  inset: -25vh -15vw;
  pointer-events: none;
  background: conic-gradient(
    from 0deg at 50% 50%,
    rgba(56, 189, 248, 0.18),
    rgba(99, 102, 241, 0.08),
    rgba(45, 212, 191, 0.12),
    rgba(56, 189, 248, 0.18)
  );
  opacity: 0.22;
  filter: blur(64px) saturate(108%);
  animation: energySpin 26s linear infinite;
}
.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: 40px 40px;
  opacity: 0.2;
  animation: gridPulse 8s ease-in-out infinite;
}
.bg-aurora {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;
  filter: blur(60px);
  opacity: 0.22;
}
.bg-aurora-a {
  width: 44vw;
  height: 44vw;
  left: -11vw;
  top: -10vh;
  background: radial-gradient(circle, rgba(56, 189, 248, 0.48), transparent 66%);
  animation: auroraFloatA 16s ease-in-out infinite alternate;
}
.bg-aurora-b {
  width: 38vw;
  height: 38vw;
  right: -10vw;
  bottom: -11vh;
  background: radial-gradient(circle, rgba(99, 102, 241, 0.46), transparent 66%);
  animation: auroraFloatB 18s ease-in-out infinite alternate;
}
.bg-scanline {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: repeating-linear-gradient(
    180deg,
    rgba(148, 163, 184, 0.045) 0px,
    rgba(148, 163, 184, 0.045) 1px,
    transparent 1px,
    transparent 4px
  );
  mix-blend-mode: soft-light;
  opacity: 0.12;
  animation: scanlineMove 7s linear infinite;
}
.bg-vignette {
  position: absolute;
  inset: 0;
  pointer-events: none;
  background: radial-gradient(circle at center, transparent 58%, rgba(2, 6, 23, 0.45) 100%);
}
.particle-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
}

.intro2-main {
  position: relative;
  z-index: 1;
  width: min(1180px, 95vw);
  min-height: 100vh;
  margin: 0 auto;
  display: grid;
  grid-template-columns: minmax(0, 0.9fr) minmax(0, 1.1fr);
  gap: 18px;
  align-items: center;
  padding: 24px 0 28px;
}
.hero {
  display: flex;
  flex-direction: column;
  gap: 12px;
  animation: sceneEnter 0.9s cubic-bezier(.22, 1, .36, 1) both;
}
.kicker {
  display: inline-flex;
  width: fit-content;
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 10px;
  letter-spacing: 0.16em;
  color: #67e8f9;
  background: rgba(8, 145, 178, 0.16);
  animation:
    fadeUp 0.6s ease-out both,
    kickerGlow 2.8s ease-in-out 0.8s infinite;
}
.hero-title {
  margin: 0;
  font-size: clamp(34px, 4.4vw, 54px);
  font-weight: 800;
  letter-spacing: 0.02em;
  line-height: 1.12;
  color: transparent;
  background: linear-gradient(92deg, #e0f2fe 0%, #67e8f9 38%, #60a5fa 70%, #c4b5fd 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 0 6px rgba(56, 189, 248, 0.2),
    0 0 12px rgba(99, 102, 241, 0.16);
  animation:
    fadeUp 0.6s ease-out 0.08s both,
    titlePulse 3.2s ease-in-out 1s infinite;
  will-change: transform, opacity;
}
.hero-sub {
  margin: 0;
  color: rgba(191, 219, 254, 0.86);
  font-size: 14px;
  line-height: 1.8;
  animation: fadeUp 0.7s ease-out 0.2s both;
}
.action-row {
  margin-top: 6px;
  display: flex;
  gap: 10px;
  animation: fadeUp 0.8s ease-out 0.45s both;
}
.btn-primary,
.btn-ghost {
  border-radius: 12px;
  padding: 12px 22px;
  font-size: 15px;
  cursor: pointer;
}
.btn-primary {
  border: 1px solid rgba(56, 189, 248, 0.55);
  color: #ecfeff;
  font-weight: 700;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.72), rgba(37, 99, 235, 0.62));
  box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3);
  animation: btnPulse 2.6s ease-in-out infinite;
}
.btn-ghost {
  border: 1px solid rgba(148, 163, 184, 0.24);
  background: rgba(15, 23, 42, 0.56);
  color: #cbd5e1;
}
.btn-primary:hover,
.btn-ghost:hover {
  transform: translateY(-1px);
}

.showcase {
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 16px;
  background:
    radial-gradient(circle at 85% 10%, rgba(56, 189, 248, 0.12), transparent 45%),
    linear-gradient(180deg, rgba(6, 18, 42, 0.86), rgba(3, 10, 24, 0.86));
  box-shadow:
    0 18px 40px rgba(2, 6, 23, 0.42),
    inset 0 0 24px rgba(56, 189, 248, 0.08);
  padding: 12px 14px;
  overflow: hidden;
  animation: sceneEnter 0.95s cubic-bezier(.22, 1, .36, 1) 0.12s both;
}
.panel {
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: 10px;
  padding: 8px 10px 6px;
  background: rgba(2, 10, 24, 0.42);
  overflow: hidden;
  transform-style: preserve-3d;
  transition: transform 0.15s ease-out;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
  animation: fadeUp 0.65s ease-out 0.24s both;
}
.tag {
  font-size: 10px;
  letter-spacing: 0.14em;
  color: #67e8f9;
  border: 1px solid rgba(34, 211, 238, 0.32);
  border-radius: 999px;
  padding: 2px 8px;
  background: rgba(8, 145, 178, 0.16);
}
.live {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 11px;
  color: rgba(186, 230, 253, 0.86);
}
.live i {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #34d399;
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.45);
  animation: pulse 1.6s ease-in-out infinite;
}
.chart-frame {
  height: 260px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  border-radius: 10px;
  background:
    repeating-linear-gradient(
      0deg,
      rgba(148, 163, 184, 0.08) 0px,
      rgba(148, 163, 184, 0.08) 1px,
      transparent 1px,
      transparent 30px
    ),
    linear-gradient(180deg, rgba(2, 10, 24, 0.62), rgba(2, 10, 24, 0.82));
  overflow: hidden;
  position: relative;
  animation: fadeUp 0.75s ease-out 0.34s both;
}
.trend-svg {
  width: 100%;
  height: calc(100% - 20px);
}
.trend-gridline line {
  stroke: rgba(148, 163, 184, 0.2);
  stroke-width: 1;
}
.trend-axis {
  stroke: rgba(148, 163, 184, 0.45);
  stroke-width: 1.2;
}
.forecast-band {
  fill: rgba(56, 189, 248, 0.1);
  filter: blur(4px);
}
.trend-line {
  fill: none;
  stroke-linecap: round;
  stroke-linejoin: round;
  stroke-width: 3;
  filter: drop-shadow(0 0 5px rgba(56, 189, 248, 0.45));
}
.trend-line-a {
  stroke: #38bdf8;
}
.trend-line-b {
  stroke: #34d399;
  filter: drop-shadow(0 0 4px rgba(52, 211, 153, 0.35));
}
.trend-point-a {
  fill: #38bdf8;
  filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.65));
}
.trend-point-b {
  fill: #34d399;
  filter: drop-shadow(0 0 6px rgba(52, 211, 153, 0.55));
}
.chart-legend {
  height: 20px;
  margin-top: -1px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  gap: 14px;
  animation: fadeUp 0.7s ease-out 0.46s both;
}
.legend-item {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 10px;
  color: rgba(148, 163, 184, 0.9);
}
.legend-dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
}
.legend-dot-a {
  background: #38bdf8;
  box-shadow: 0 0 8px rgba(56, 189, 248, 0.5);
}
.legend-dot-b {
  background: #34d399;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.45);
}

@media (max-width: 980px) {
  .intro2-main {
    grid-template-columns: 1fr;
    align-items: start;
  }
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.35; }
}
@keyframes auroraFloatA {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(6vw, 4vh, 0) scale(1.08); }
}
@keyframes auroraFloatB {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(-5vw, -3vh, 0) scale(1.1); }
}
@keyframes baseDrift {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(-1.5vw, -1vh, 0) scale(1.02); }
}
@keyframes energySpin {
  0% { transform: rotate(0deg) scale(1); }
  50% { transform: rotate(180deg) scale(1.06); }
  100% { transform: rotate(360deg) scale(1); }
}
@keyframes scanlineMove {
  0% { transform: translateY(0); }
  100% { transform: translateY(16px); }
}
@keyframes gridPulse {
  0%, 100% { opacity: 0.2; }
  50% { opacity: 0.34; }
}
@keyframes sceneEnter {
  from { opacity: 0; transform: translate3d(0, 18px, 0) scale(0.992); }
  to { opacity: 1; transform: translate3d(0, 0, 0) scale(1); }
}
@keyframes fadeUp {
  from { opacity: 0; transform: translate3d(0, 14px, 0); }
  to { opacity: 1; transform: translate3d(0, 0, 0); }
}
@keyframes titlePulse {
  0%, 100% {
    text-shadow:
      0 0 6px rgba(56, 189, 248, 0.18),
      0 0 14px rgba(99, 102, 241, 0.14);
  }
  50% {
    text-shadow:
      0 0 10px rgba(56, 189, 248, 0.26),
      0 0 22px rgba(99, 102, 241, 0.2);
  }
}
@keyframes kickerGlow {
  0%, 100% {
    box-shadow: 0 0 0 rgba(34, 211, 238, 0);
    border-color: rgba(34, 211, 238, 0.3);
  }
  50% {
    box-shadow: 0 0 14px rgba(34, 211, 238, 0.28);
    border-color: rgba(34, 211, 238, 0.6);
  }
}
@keyframes btnPulse {
  0%, 100% { box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3); }
  50% { box-shadow: 0 12px 30px rgba(37, 99, 235, 0.42); }
}
</style>

