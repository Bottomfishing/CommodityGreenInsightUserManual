<template>
  <div class="introai-page">
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

    <main class="introai-main">
      <section class="hero">
        <span class="kicker">GREEN FINTECH</span>
        <h1 class="hero-title">这里有您的专属 AI 小绿</h1>
        <p class="hero-sub">
          它可以回答一切有关于这个平台的问题，您的可视化她也能看到。
        </p>
        <div class="action-row">
          <button class="btn-primary" @click="goNext">继续</button>
          <button class="btn-ghost" @click="router.push({ name: 'IntroDerivation' })">返回上一页</button>
        </div>
      </section>

      <section class="showcase">
        <article
          class="panel avatar-panel"
          :style="panelStyle"
          @mousemove="onMove"
          @mouseleave="onLeave"
        >
          <div class="panel-head">
            <span class="tag">小绿</span>
            <span class="live"><i></i>ONLINE</span>
          </div>
          <div class="avatar-frame">
            <img class="avatar-img" src="/assistant-avatar.png" alt="AI 小绿" />
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();
const particleRef = ref<HTMLCanvasElement | null>(null);
const panelStyle = ref<Record<string, string>>({});

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

function onMove(event: MouseEvent) {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const rx = ((y / rect.height) * 2 - 1) * -4.2;
  const ry = ((x / rect.width) * 2 - 1) * 4.8;
  panelStyle.value = {
    transform: `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg)`,
  };
}
function onLeave() {
  panelStyle.value = {
    transition: "transform .5s cubic-bezier(.22,1,.36,1)",
    transform: "perspective(1000px) rotateX(0) rotateY(0)",
  };
}

function goNext() {
  router.push({ name: "IntroWelcome" });
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
.introai-page {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  color: #e2e8f0;
}
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
.bg-vignette { position: absolute; inset: 0; pointer-events: none; background: radial-gradient(circle at center, transparent 58%, rgba(2, 6, 23, 0.45) 100%); }
.particle-canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }

.introai-main {
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
.hero { display: flex; flex-direction: column; gap: 12px; animation: sceneEnter 0.9s cubic-bezier(.22, 1, .36, 1) both; }
.kicker {
  display: inline-flex; width: fit-content;
  border: 1px solid rgba(34, 211, 238, 0.3);
  border-radius: 999px;
  padding: 3px 10px;
  font-size: 10px;
  letter-spacing: 0.16em;
  color: #67e8f9;
  background: rgba(8, 145, 178, 0.16);
  animation: fadeUp 0.6s ease-out both, kickerGlow 2.8s ease-in-out 0.8s infinite;
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
  text-shadow: 0 0 6px rgba(56, 189, 248, 0.2), 0 0 12px rgba(99, 102, 241, 0.16);
  animation: fadeUp 0.6s ease-out 0.08s both, titlePulse 3.2s ease-in-out 1s infinite;
}
.hero-sub { margin: 0; color: rgba(191, 219, 254, 0.86); font-size: 14px; line-height: 1.8; animation: fadeUp 0.7s ease-out 0.2s both; }
.action-row { margin-top: 6px; display: flex; gap: 10px; animation: fadeUp 0.8s ease-out 0.45s both; }
.btn-primary, .btn-ghost { border-radius: 12px; padding: 12px 22px; font-size: 15px; cursor: pointer; }
.btn-primary {
  border: 1px solid rgba(56, 189, 248, 0.55);
  color: #ecfeff;
  font-weight: 700;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.72), rgba(37, 99, 235, 0.62));
  box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3);
  animation: btnPulse 2.6s ease-in-out infinite;
}
.btn-ghost { border: 1px solid rgba(148, 163, 184, 0.24); background: rgba(15, 23, 42, 0.56); color: #cbd5e1; }
.btn-primary:hover, .btn-ghost:hover { transform: translateY(-1px); }

.showcase {
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 16px;
  background:
    radial-gradient(circle at 85% 10%, rgba(56, 189, 248, 0.12), transparent 45%),
    linear-gradient(180deg, rgba(6, 18, 42, 0.86), rgba(3, 10, 24, 0.86));
  box-shadow: 0 18px 40px rgba(2, 6, 23, 0.42), inset 0 0 24px rgba(56, 189, 248, 0.08);
  padding: 12px 14px;
  overflow: hidden;
  animation: sceneEnter 0.95s cubic-bezier(.22, 1, .36, 1) 0.12s both;
}
.panel {
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: 10px;
  padding: 8px 10px 10px;
  background: rgba(2, 10, 24, 0.42);
  overflow: hidden;
  transform-style: preserve-3d;
  transition: transform 0.15s ease-out;
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
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
.avatar-frame {
  height: 340px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  border-radius: 10px;
  background: linear-gradient(180deg, rgba(2, 10, 24, 0.62), rgba(2, 10, 24, 0.82));
  overflow: hidden;
  display: flex;
  align-items: center;
  justify-content: center;
}
.avatar-img {
  width: min(320px, 80%);
  height: auto;
  object-fit: contain;
  filter: drop-shadow(0 18px 44px rgba(2, 6, 23, 0.55));
}

@media (max-width: 980px) {
  .introai-main { grid-template-columns: 1fr; align-items: start; }
  .avatar-frame { height: 300px; }
}

@keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.35; } }
@keyframes auroraFloatA { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(6vw, 4vh, 0) scale(1.08); } }
@keyframes auroraFloatB { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(-5vw, -3vh, 0) scale(1.1); } }
@keyframes baseDrift { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(-1.5vw, -1vh, 0) scale(1.02); } }
@keyframes energySpin { 0% { transform: rotate(0deg) scale(1); } 50% { transform: rotate(180deg) scale(1.06); } 100% { transform: rotate(360deg) scale(1); } }
@keyframes scanlineMove { 0% { transform: translateY(0); } 100% { transform: translateY(16px); } }
@keyframes gridPulse { 0%, 100% { opacity: 0.2; } 50% { opacity: 0.34; } }
@keyframes sceneEnter { from { opacity: 0; transform: translate3d(0, 18px, 0) scale(0.992); } to { opacity: 1; transform: translate3d(0, 0, 0) scale(1); } }
@keyframes fadeUp { from { opacity: 0; transform: translate3d(0, 14px, 0); } to { opacity: 1; transform: translate3d(0, 0, 0); } }
@keyframes titlePulse { 0%, 100% { text-shadow: 0 0 6px rgba(56, 189, 248, 0.18), 0 0 14px rgba(99, 102, 241, 0.14); } 50% { text-shadow: 0 0 10px rgba(56, 189, 248, 0.26), 0 0 22px rgba(99, 102, 241, 0.2); } }
@keyframes kickerGlow { 0%, 100% { box-shadow: 0 0 0 rgba(34, 211, 238, 0); border-color: rgba(34, 211, 238, 0.3); } 50% { box-shadow: 0 0 14px rgba(34, 211, 238, 0.28); border-color: rgba(34, 211, 238, 0.6); } }
@keyframes btnPulse { 0%, 100% { box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3); } 50% { box-shadow: 0 12px 30px rgba(37, 99, 235, 0.42); } }
</style>

