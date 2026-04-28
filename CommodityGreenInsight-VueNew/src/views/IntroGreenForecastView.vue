<template>
  <div class="intro6-page">
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

    <main class="intro6-main">
      <section class="hero">
        <span class="kicker">GREEN FINTECH</span>
        <h1 class="hero-title">您可以建立任何一段您预测过的油价序列其对应日期的绿色金融预测</h1>
        <p class="hero-sub">支持按日期对齐油价预测片段，生成对应绿色金融风险等级与分布洞察。</p>
        <div class="action-row">
          <button class="btn-primary" @click="goNext">继续</button>
          <button class="btn-ghost" @click="router.push({ name: 'IntroPredict' })">返回上一页</button>
        </div>
      </section>

      <section class="showcase">
        <article
          class="chart-panel"
          :style="cardStyle"
          @mousemove="onCardMove"
          @mouseleave="onCardLeave"
        >
          <header class="panel-head">风险等级分布</header>
          <div class="bar-chart">
            <div class="grid-line" v-for="n in 6" :key="`g-${n}`"></div>
            <div class="bars">
              <div class="bar-item">
                <div class="bar" style="height: 88%"></div>
                <span class="bar-label">LOW</span>
              </div>
              <div class="bar-item">
                <div class="bar" style="height: 56%"></div>
                <span class="bar-label">MEDIUM</span>
              </div>
              <div class="bar-item">
                <div class="bar" style="height: 38%"></div>
                <span class="bar-label">HIGH</span>
              </div>
            </div>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { onBeforeUnmount, onMounted, ref } from "vue";

const router = useRouter();
const particleRef = ref<HTMLCanvasElement | null>(null);
const cardStyle = ref<Record<string, string>>({});

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

function onCardMove(event: MouseEvent) {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const rx = ((y / rect.height) * 2 - 1) * -4.2;
  const ry = ((x / rect.width) * 2 - 1) * 4.8;
  cardStyle.value = {
    transform: `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg)`,
  };
}

function onCardLeave() {
  cardStyle.value = {
    transition: "transform .5s cubic-bezier(.22,1,.36,1)",
    transform: "perspective(1000px) rotateX(0) rotateY(0)",
  };
}

function goNext() {
  router.push({ name: "IntroDerivation" });
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
.intro6-page { position: relative; min-height: 100vh; overflow: hidden; font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif; color: #e2e8f0; }
.bg-layer { position: absolute; inset: 0; }
.bg-base {
  position: absolute; inset: 0;
  background:
    radial-gradient(circle at 18% 22%, rgba(14, 116, 144, 0.2), transparent 34%),
    radial-gradient(circle at 82% 18%, rgba(99, 102, 241, 0.2), transparent 36%),
    linear-gradient(145deg, #030712 0%, #06122a 48%, #071634 76%, #040a19 100%);
  animation: baseDrift 20s ease-in-out infinite alternate;
}
.bg-energy {
  position: absolute; inset: -25vh -15vw; pointer-events: none;
  background: conic-gradient(from 0deg at 50% 50%, rgba(56, 189, 248, 0.18), rgba(99, 102, 241, 0.08), rgba(45, 212, 191, 0.12), rgba(56, 189, 248, 0.18));
  opacity: 0.22; filter: blur(64px) saturate(108%); animation: energySpin 26s linear infinite;
}
.bg-grid {
  position: absolute; inset: 0;
  background-image: linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: 40px 40px; opacity: 0.2; animation: gridPulse 8s ease-in-out infinite;
}
.bg-aurora { position: absolute; border-radius: 50%; pointer-events: none; filter: blur(60px); opacity: 0.22; }
.bg-aurora-a { width: 44vw; height: 44vw; left: -11vw; top: -10vh; background: radial-gradient(circle, rgba(56, 189, 248, 0.48), transparent 66%); animation: auroraFloatA 16s ease-in-out infinite alternate; }
.bg-aurora-b { width: 38vw; height: 38vw; right: -10vw; bottom: -11vh; background: radial-gradient(circle, rgba(99, 102, 241, 0.46), transparent 66%); animation: auroraFloatB 18s ease-in-out infinite alternate; }
.bg-scanline {
  position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(180deg, rgba(148, 163, 184, 0.045) 0px, rgba(148, 163, 184, 0.045) 1px, transparent 1px, transparent 4px);
  mix-blend-mode: soft-light; opacity: 0.12; animation: scanlineMove 7s linear infinite;
}
.bg-vignette { position: absolute; inset: 0; background: radial-gradient(circle at center, transparent 58%, rgba(2, 6, 23, 0.45) 100%); }
.particle-canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }

.intro6-main {
  position: relative; z-index: 1; width: min(1280px, 95vw); min-height: 100vh; margin: 0 auto;
  display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; align-items: center; padding: 24px 0 28px;
}
.hero { display: flex; flex-direction: column; gap: 12px; animation: sceneEnter 0.9s cubic-bezier(.22, 1, .36, 1) both; }
.kicker {
  display: inline-flex; width: fit-content; border: 1px solid rgba(34, 211, 238, 0.3); border-radius: 999px; padding: 3px 10px;
  font-size: 10px; letter-spacing: 0.16em; color: #67e8f9; background: rgba(8, 145, 178, 0.16);
  animation: fadeUp 0.6s ease-out both, kickerGlow 2.8s ease-in-out 0.8s infinite;
}
.hero-title {
  margin: 0; font-size: clamp(34px, 4.1vw, 50px); line-height: 1.14; font-weight: 800;
  color: transparent; background: linear-gradient(92deg, #e0f2fe 0%, #67e8f9 38%, #60a5fa 70%, #c4b5fd 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  text-shadow: 0 0 6px rgba(56, 189, 248, 0.2), 0 0 12px rgba(99, 102, 241, 0.16);
  animation: fadeUp 0.6s ease-out 0.08s both, titlePulse 3.2s ease-in-out 1s infinite;
}
.hero-sub { margin: 0; color: rgba(191, 219, 254, 0.86); font-size: 14px; line-height: 1.8; animation: fadeUp 0.7s ease-out 0.2s both; }
.action-row { margin-top: 6px; display: flex; gap: 10px; }
.btn-primary, .btn-ghost { border-radius: 12px; padding: 12px 22px; font-size: 15px; cursor: pointer; }
.btn-primary {
  border: 1px solid rgba(56, 189, 248, 0.55); color: #ecfeff; font-weight: 700;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.72), rgba(37, 99, 235, 0.62));
  box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3); animation: btnPulse 2.6s ease-in-out infinite;
}
.btn-ghost { border: 1px solid rgba(148, 163, 184, 0.24); background: rgba(15, 23, 42, 0.56); color: #cbd5e1; }
.btn-primary:hover, .btn-ghost:hover { transform: translateY(-1px); }

.showcase { animation: sceneEnter 0.95s cubic-bezier(.22, 1, .36, 1) 0.12s both; }
.chart-panel {
  position: relative;
  border: 1px solid rgba(56, 189, 248, 0.3);
  border-radius: 20px;
  padding: 16px 16px 14px;
  min-height: 360px;
  background:
    radial-gradient(circle at 50% 50%, rgba(56, 189, 248, 0.08), rgba(2, 6, 23, 0.72) 62%),
    linear-gradient(180deg, rgba(6, 18, 42, 0.9), rgba(3, 10, 24, 0.9));
  box-shadow:
    0 18px 40px rgba(2, 6, 23, 0.42),
    inset 0 0 26px rgba(56, 189, 248, 0.12);
  transform-style: preserve-3d;
  transition: transform 0.15s ease-out;
  isolation: isolate;
  overflow: hidden;
}
.chart-panel::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  background: linear-gradient(
    110deg,
    transparent 18%,
    rgba(186, 230, 253, 0.06) 40%,
    rgba(224, 242, 254, 0.18) 50%,
    rgba(186, 230, 253, 0.06) 60%,
    transparent 82%
  );
  transform: translateX(-120%);
  animation: glossSweep 11.6s linear infinite;
  pointer-events: none;
  z-index: 1;
}
.panel-head { text-align: center; font-size: 20px; color: #e2e8f0; margin-bottom: 10px; }
.bar-chart {
  position: relative; z-index: 2;
  height: 330px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  border-radius: 12px;
  padding: 10px 12px 40px;
  overflow: hidden;
}
.grid-line { position: absolute; left: 12px; right: 12px; height: 1px; background: rgba(148, 163, 184, 0.24); }
.grid-line:nth-child(1) { top: 40px; }
.grid-line:nth-child(2) { top: 84px; }
.grid-line:nth-child(3) { top: 128px; }
.grid-line:nth-child(4) { top: 172px; }
.grid-line:nth-child(5) { top: 216px; }
.grid-line:nth-child(6) { top: 260px; }
.bars {
  position: absolute; left: 16px; right: 16px; bottom: 16px; top: 26px;
  display: grid; grid-template-columns: repeat(3, 1fr); align-items: end; gap: 28px;
}
.bar-item { display: flex; flex-direction: column; align-items: center; justify-content: flex-end; gap: 10px; height: 100%; }
.bar {
  width: min(120px, 85%);
  border-radius: 8px 8px 2px 2px;
  background: linear-gradient(180deg, rgba(52, 211, 153, 0.98), rgba(34, 197, 94, 0.9));
  box-shadow: 0 6px 20px rgba(34, 197, 94, 0.26);
  animation: barPulse 2.8s ease-in-out infinite;
}
.bar-label { font-size: 12px; color: #cbd5e1; letter-spacing: 0.04em; }

@media (max-width: 980px) {
  .intro6-main { grid-template-columns: 1fr; align-items: start; }
}

@keyframes auroraFloatA { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(6vw, 4vh, 0) scale(1.08); } }
@keyframes auroraFloatB { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(-5vw, -3vh, 0) scale(1.1); } }
@keyframes baseDrift { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(-1.5vw, -1vh, 0) scale(1.02); } }
@keyframes energySpin { 0% { transform: rotate(0deg) scale(1); } 50% { transform: rotate(180deg) scale(1.06); } 100% { transform: rotate(360deg) scale(1); } }
@keyframes scanlineMove { 0% { transform: translateY(0); } 100% { transform: translateY(16px); } }
@keyframes gridPulse { 0%, 100% { opacity: 0.2; } 50% { opacity: 0.34; } }
@keyframes sceneEnter { from { opacity: 0; transform: translate3d(0, 18px, 0) scale(0.992); } to { opacity: 1; transform: translate3d(0, 0, 0) scale(1); } }
@keyframes fadeUp { from { opacity: 0; transform: translate3d(0, 14px, 0); } to { opacity: 1; transform: translate3d(0, 0, 0); } }
@keyframes titlePulse {
  0%, 100% { text-shadow: 0 0 6px rgba(56, 189, 248, 0.18), 0 0 14px rgba(99, 102, 241, 0.14); }
  50% { text-shadow: 0 0 10px rgba(56, 189, 248, 0.26), 0 0 22px rgba(99, 102, 241, 0.2); }
}
@keyframes kickerGlow {
  0%, 100% { box-shadow: 0 0 0 rgba(34, 211, 238, 0); border-color: rgba(34, 211, 238, 0.3); }
  50% { box-shadow: 0 0 14px rgba(34, 211, 238, 0.28); border-color: rgba(34, 211, 238, 0.6); }
}
@keyframes btnPulse { 0%, 100% { box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3); } 50% { box-shadow: 0 12px 30px rgba(37, 99, 235, 0.42); } }
@keyframes glossSweep {
  0% { transform: translateX(-120%); opacity: 0; }
  20% { opacity: 0.9; }
  82% { transform: translateX(120%); opacity: 0; }
  100% { transform: translateX(120%); opacity: 0; }
}
@keyframes barPulse {
  0%, 100% { filter: brightness(0.95); }
  50% { filter: brightness(1.06); }
}
</style>
