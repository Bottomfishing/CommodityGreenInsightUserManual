<template>
  <div class="introw-page">
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

    <main class="introw-main">
      <section class="welcome-block">
        <p class="line line-1">欢迎您使用我们的网站，</p>
        <p class="line line-2">希望我们的网站可以给您带来好的使用观感，</p>
        <p class="line line-3">祝您使用顺利。</p>
      </section>
      <button class="login-btn" @click="goLogin">进入登录</button>
    </main>

    <AuthModal
      v-model:visible="showAuth"
      @success="onAuthSuccess"
    />
  </div>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref } from "vue";
import { useRouter } from "vue-router";
import AuthModal from "@/components/AuthModal.vue";

const router = useRouter();
const particleRef = ref<HTMLCanvasElement | null>(null);
let rafId: number | null = null;
let particles: Array<{ x: number; y: number; vx: number; vy: number; r: number; a: number }> = [];
let removeResize: (() => void) | null = null;
let lastFrame = 0;
const showAuth = ref(false);

function initParticles() {
  const canvas = particleRef.value;
  if (!canvas) return;
  const ctx = canvas.getContext("2d");
  if (!ctx) return;

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    const count = Math.max(20, Math.floor((canvas.width * canvas.height) / 82000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.18,
      vy: (Math.random() - 0.5) * 0.18,
      r: Math.random() * 1.4 + 0.5,
      a: Math.random() * 0.28 + 0.1,
    }));
  };
  resize();
  window.addEventListener("resize", resize);
  removeResize = () => window.removeEventListener("resize", resize);

  const tick = (ts = 0) => {
    if (ts - lastFrame < 33) {
      rafId = requestAnimationFrame(tick);
      return;
    }
    lastFrame = ts;
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

function goLogin() {
  showAuth.value = true;
}

function onAuthSuccess() {
  router.push({ name: "Home" });
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
.introw-page {
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

.introw-main {
  position: relative;
  z-index: 1;
  min-height: 100vh;
  width: min(980px, 90vw);
  margin: 0 auto;
  display: grid;
  place-content: center;
  justify-items: center;
  gap: 18px;
}
.welcome-block { text-align: center; }
.line {
  margin: 0;
  font-family:
    "YouYuan",
    "STKaiti",
    "KaiTi",
    "STSong",
    "PingFang SC",
    "Microsoft YaHei",
    sans-serif;
  color: #dbeafe;
  font-weight: 800;
  letter-spacing: 0.05em;
  text-shadow: 0 0 10px rgba(56, 189, 248, 0.18), 0 0 20px rgba(99, 102, 241, 0.12);
  white-space: nowrap;
  opacity: 0;
  clip-path: inset(0 100% 0 0);
  will-change: clip-path, opacity;
  animation: typeReveal 1.9s cubic-bezier(.22,1,.36,1) forwards;
}
.line-1 { font-size: clamp(34px, 4.2vw, 54px); animation-delay: 0.2s; }
.line-2 { font-size: clamp(28px, 3.5vw, 42px); margin-top: 8px; animation-delay: 2.25s; }
.line-3 { font-size: clamp(28px, 3.5vw, 42px); margin-top: 8px; animation-delay: 4.3s; }

.login-btn {
  opacity: 0;
  transform: translateY(10px);
  border-radius: 14px;
  border: 1px solid rgba(56, 189, 248, 0.55);
  padding: 13px 26px;
  font-size: 16px;
  color: #ecfeff;
  font-weight: 700;
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.72), rgba(37, 99, 235, 0.62));
  box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3);
  cursor: pointer;
  animation: btnFadeIn 0.9s cubic-bezier(.22,1,.36,1) 6.0s forwards;
}
.login-btn:hover { transform: translateY(-1px); }

@media (max-width: 980px) {
  .line { white-space: normal; }
}

@keyframes typeReveal {
  0% { clip-path: inset(0 100% 0 0); opacity: 0; }
  8% { opacity: 1; }
  100% { clip-path: inset(0 0 0 0); opacity: 1; }
}
@keyframes btnFadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}
@keyframes auroraFloatA { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(6vw, 4vh, 0) scale(1.08); } }
@keyframes auroraFloatB { 0% { transform: translate3d(0, 0, 0) scale(1); } 100% { transform: translate3d(-5vw, -3vh, 0) scale(1.1); } }
@keyframes energySpin { 0% { transform: rotate(0deg) scale(1); } 50% { transform: rotate(180deg) scale(1.06); } 100% { transform: rotate(360deg) scale(1); } }
@keyframes scanlineMove { 0% { transform: translateY(0); } 100% { transform: translateY(16px); } }
@keyframes gridPulse { 0%, 100% { opacity: 0.2; } 50% { opacity: 0.34; } }
</style>

