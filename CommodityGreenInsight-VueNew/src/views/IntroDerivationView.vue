<template>
  <div class="derive-page">
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

    <main class="derive-main">
      <section class="hero">
        <span class="kicker">GREEN FINTECH</span>
        <h1 class="hero-title">我们的推导过程严谨</h1>
        <p class="hero-sub">从特征筛选、序列分解到时序建模与绿色金融溢出推导，形成完整可解释链路。</p>
        <div class="action-row">
          <button class="btn-primary" @click="goNext">继续</button>
          <button class="btn-ghost" @click="router.push({ name: 'IntroGreenForecast' })">返回上一页</button>
        </div>
      </section>

      <section class="derive-content">
        <article
          class="derive-card derive-card--half"
          :style="cardStyles.rf"
          @mousemove="onCardMove($event, 'rf')"
          @mouseleave="onCardLeave('rf')"
        >
          <h2>随机森林（RF）</h2>
          <div class="formula-block" v-html="math.rfLoss"></div>
        </article>

        <article
          class="derive-card derive-card--half"
          :style="cardStyles.vmd"
          @mousemove="onCardMove($event, 'vmd')"
          @mouseleave="onCardLeave('vmd')"
        >
          <h2>VMD</h2>
          <div class="formula-block" v-html="math.vmdObj"></div>
        </article>

        <article
          class="derive-card"
          :style="cardStyles.gru"
          @mousemove="onCardMove($event, 'gru')"
          @mouseleave="onCardLeave('gru')"
        >
          <h2>GRU</h2>
          <div class="formula-block" v-html="math.gruEq"></div>
        </article>

        <article
          class="derive-card derive-card--green"
          :style="cardStyles.green"
          @mousemove="onCardMove($event, 'green')"
          @mouseleave="onCardLeave('green')"
        >
          <h2>绿色金融推导</h2>
          <div class="formula-grid-two">
            <div class="formula-block" v-html="math.rDef"></div>
            <div class="formula-block" v-html="math.rDecompose"></div>
            <div class="formula-block" v-html="math.epsAr"></div>
            <div class="formula-block" v-html="math.jumpVol"></div>
            <div class="formula-block" v-html="math.egarch"></div>
            <div class="formula-block" v-html="math.leverage"></div>
            <div class="formula-block" v-html="math.neReturn"></div>
            <div class="formula-block" v-html="math.neVol"></div>
            <div class="formula-block" v-html="math.factorMatrix"></div>
            <div class="formula-block" v-html="math.skewT"></div>
          </div>
        </article>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, reactive, ref } from "vue";
import { useRouter } from "vue-router";
import katex from "katex";
import "katex/dist/katex.min.css";

const router = useRouter();
const particleRef = ref<HTMLCanvasElement | null>(null);
const cardStyles = reactive<Record<"rf" | "vmd" | "gru" | "green", Record<string, string>>>({
  rf: {},
  vmd: {},
  gru: {},
  green: {},
});
let rafId: number | null = null;
let particles: Array<{ x: number; y: number; vx: number; vy: number; r: number; a: number }> = [];
let removeResize: (() => void) | null = null;

function renderMath(expr: string) {
  return katex.renderToString(expr, {
    throwOnError: false,
    displayMode: true,
    output: "html",
    strict: "ignore",
  });
}

const math = computed(() => ({
  rfLoss: renderMath(String.raw`\text{Imp}(x_j)=\frac{1}{B}\sum_{b=1}^{B}\sum_{t\in T_b}\Delta I_t(j)`),
  vmdObj: renderMath(String.raw`\min_{\{u_k\},\{\omega_k\}}\sum_{k=1}^{K}\left\|\partial_t\left[\left(\delta(t)+\frac{j}{\pi t}\right)\ast u_k(t)\right]e^{-j\omega_k t}\right\|_2^2,\ \text{s.t. }\sum_{k=1}^{K}u_k=f`),
  gruEq: renderMath(String.raw`\begin{aligned}
z_t&=\sigma(W_zx_t+U_zh_{t-1}+b_z),\quad r_t=\sigma(W_rx_t+U_rh_{t-1}+b_r)\\
\tilde h_t&=\tanh(W_hx_t+U_h(r_t\odot h_{t-1})+b_h),\quad
h_t=(1-z_t)\odot h_{t-1}+z_t\odot\tilde h_t
\end{aligned}`),
  rDef: renderMath(String.raw`R_{i,t}=100\times\ln\left(\frac{P_{i,t}}{P_{i,t-1}}\right)`),
  rDecompose: renderMath(String.raw`R_t=\underbrace{\alpha+\beta^\top X_t}_{\text{一层：可解释因子收益}}+\underbrace{a_t}_{\text{二层：异质扰动收益}}`),
  epsAr: renderMath(String.raw`a_t=\phi_0+\sum_{p=1}^{P}\phi_pa_{t-p}+\varepsilon_t,\qquad \varepsilon_t\sim(0,h_t)`),
  jumpVol: renderMath(String.raw`a_t=\mu_t+\sqrt{h_t}\,z_t+J_t,\qquad J_t\sim\sum_{m=1}^{M}\pi_m\mathcal N(\mu_m,\sigma_m^2)`),
  egarch: renderMath(String.raw`\ln h_t=\omega+\beta\ln h_{t-1}+\alpha\left(\frac{|\varepsilon_{t-1}|}{\sqrt{h_{t-1}}}-\mathbb E|z|\right)+\gamma\frac{\varepsilon_{t-1}}{\sqrt{h_{t-1}}}`),
  leverage: renderMath(String.raw`\gamma<0\Rightarrow \text{负向冲击对波动放大更强（杠杆效应）}`),
  neReturn: renderMath(String.raw`R^{NE}_t=\eta_0+\eta_1\widehat R^{Oil}_{t-\tau}+\eta_2R^{NE}_{t-1}+\eta_3^\top F_t+\xi_t`),
  neVol: renderMath(String.raw`\ln h^{NE}_t=\omega_{ne}+\beta_{ne}\ln h^{NE}_{t-1}+\theta_1\ln h^{Oil}_{t-1}+\theta_2\widehat R^{Oil}_{t-1}+\nu_t`),
  factorMatrix: renderMath(String.raw`\mathbf S_t=\begin{bmatrix}
\partial R^{NE}_t/\partial \widehat R^{Oil}_t & \partial R^{NE}_t/\partial h^{Oil}_t\\
\partial h^{NE}_t/\partial \widehat R^{Oil}_t & \partial h^{NE}_t/\partial h^{Oil}_t
\end{bmatrix}`),
  skewT: renderMath(String.raw`d\widehat R^{Oil}_t=\kappa(\mu-\widehat R^{Oil}_t)\,dt+\sigma_t\,dW_t,\qquad \varepsilon_t\sim\text{Skew-}t(\nu,\lambda)`),
}));

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

function onCardMove(event: MouseEvent, key: "rf" | "vmd" | "gru" | "green") {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const rx = ((y / rect.height) * 2 - 1) * -4.2;
  const ry = ((x / rect.width) * 2 - 1) * 4.8;
  cardStyles[key] = {
    transform: `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg)`,
  };
}

function onCardLeave(key: "rf" | "vmd" | "gru" | "green") {
  cardStyles[key] = {
    transition: "transform .5s cubic-bezier(.22,1,.36,1)",
    transform: "perspective(1000px) rotateX(0) rotateY(0)",
  };
}

function goNext() {
  router.push({ name: "IntroAI" });
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
.derive-page {
  position: relative;
  height: 100vh;
  overflow-x: hidden;
  overflow-y: hidden;
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
.bg-aurora { position: absolute; border-radius: 50%; pointer-events: none; filter: blur(60px); opacity: 0.22; }
.bg-aurora-a { width: 44vw; height: 44vw; left: -11vw; top: -10vh; background: radial-gradient(circle, rgba(56, 189, 248, 0.48), transparent 66%); animation: auroraFloatA 16s ease-in-out infinite alternate; }
.bg-aurora-b { width: 38vw; height: 38vw; right: -10vw; bottom: -11vh; background: radial-gradient(circle, rgba(99, 102, 241, 0.46), transparent 66%); animation: auroraFloatB 18s ease-in-out infinite alternate; }
.bg-grid {
  position: absolute; inset: 0;
  background-image: linear-gradient(rgba(148, 163, 184, 0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(148, 163, 184, 0.05) 1px, transparent 1px);
  background-size: 40px 40px; opacity: 0.2; animation: gridPulse 8s ease-in-out infinite;
}
.bg-scanline {
  position: absolute; inset: 0; pointer-events: none;
  background: repeating-linear-gradient(180deg, rgba(148, 163, 184, 0.045) 0px, rgba(148, 163, 184, 0.045) 1px, transparent 1px, transparent 4px);
  mix-blend-mode: soft-light; opacity: 0.12; animation: scanlineMove 7s linear infinite;
}
.bg-vignette { position: absolute; inset: 0; background: radial-gradient(circle at center, transparent 58%, rgba(2, 6, 23, 0.45) 100%); }
.particle-canvas { position: absolute; inset: 0; width: 100%; height: 100%; pointer-events: none; }

.derive-main {
  position: relative;
  z-index: 1;
  width: min(1280px, 95vw);
  margin: 0 auto;
  padding: 24px 0 32px;
  display: grid;
  gap: 18px;
}
.hero { display: flex; flex-direction: column; gap: 10px; animation: sceneEnter 0.9s cubic-bezier(.22, 1, .36, 1) both; }
.kicker {
  display: inline-flex; width: fit-content; border: 1px solid rgba(34, 211, 238, 0.3); border-radius: 999px; padding: 3px 10px; font-size: 10px; letter-spacing: 0.16em; color: #67e8f9; background: rgba(8, 145, 178, 0.16);
  animation: fadeUp 0.6s ease-out both, kickerGlow 2.8s ease-in-out 0.8s infinite;
}
.hero-title {
  margin: 0; font-size: clamp(32px, 3.8vw, 46px); line-height: 1.14; font-weight: 800;
  color: transparent; background: linear-gradient(92deg, #e0f2fe 0%, #67e8f9 38%, #60a5fa 70%, #c4b5fd 100%);
  -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  text-shadow: 0 0 6px rgba(56, 189, 248, 0.2), 0 0 12px rgba(99, 102, 241, 0.16);
  animation: fadeUp 0.6s ease-out 0.08s both, titlePulse 3.2s ease-in-out 1s infinite;
}
.hero-sub { margin: 0; color: rgba(191, 219, 254, 0.86); font-size: 14px; line-height: 1.8; animation: fadeUp 0.7s ease-out 0.2s both; }
.action-row { margin-top: 6px; display: flex; gap: 10px; }
.btn-primary, .btn-ghost { border-radius: 12px; padding: 11px 20px; font-size: 14px; cursor: pointer; }
.btn-primary {
  border: 1px solid rgba(56, 189, 248, 0.55); color: #ecfeff; font-weight: 700; background: linear-gradient(135deg, rgba(14, 116, 144, 0.72), rgba(37, 99, 235, 0.62));
  box-shadow: 0 8px 22px rgba(14, 116, 144, 0.3); animation: btnPulse 2.6s ease-in-out infinite;
}
.btn-ghost { border: 1px solid rgba(148, 163, 184, 0.24); background: rgba(15, 23, 42, 0.56); color: #cbd5e1; }
.btn-primary:hover, .btn-ghost:hover { transform: translateY(-1px); }

.derive-card {
  border: 1px solid rgba(56, 189, 248, 0.26);
  border-radius: 14px;
  background:
    radial-gradient(circle at 85% 10%, rgba(56, 189, 248, 0.09), transparent 45%),
    linear-gradient(180deg, rgba(6, 18, 42, 0.9), rgba(3, 10, 24, 0.9));
  box-shadow: 0 12px 28px rgba(2, 6, 23, 0.36), inset 0 0 20px rgba(56, 189, 248, 0.08);
  transform-style: preserve-3d;
  transition: transform 0.15s ease-out;
  opacity: 0;
  animation: cardFadeIn 0.7s cubic-bezier(.22,1,.36,1) forwards;
}

.derive-content {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
  margin-top: 50px;
}
.derive-card { padding: 14px; }
.derive-card h2 {
  margin: 0 0 8px;
  font-size: 18px;
  font-family:
    "YouYuan",
    "STKaiti",
    "KaiTi",
    "STSong",
    "PingFang SC",
    "Microsoft YaHei",
    sans-serif;
  font-weight: 800;
  letter-spacing: 0.08em;
  color: transparent;
  background: linear-gradient(92deg, #e0f2fe 0%, #67e8f9 38%, #60a5fa 70%, #c4b5fd 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 0 10px rgba(56, 189, 248, 0.18),
    0 0 18px rgba(99, 102, 241, 0.14);
}
.derive-card--half { min-height: 120px; }
.derive-content .derive-card:not(.derive-card--half) { grid-column: 1 / -1; }
.derive-card--green {
  padding-top: 10px;
  padding-bottom: 8px;
}
.formula-grid-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.derive-card--green .formula-grid-two {
  gap: 4px 8px;
}
.derive-card--green .formula-block {
  margin: 2px 0;
  padding: 0;
}
.derive-card--green .formula-block :deep(.katex) {
  font-size: clamp(0.82rem, 1.2vw, 0.92rem);
}

.formula-block {
  margin: 8px 0 10px;
  padding: 4px 2px;
  border: none;
  border-radius: 0;
  background: transparent;
  overflow-x: auto;
  opacity: 0;
  clip-path: inset(0 100% 0 0);
  animation: formulaWrite 0.95s cubic-bezier(.22,1,.36,1) forwards;
}
.formula-block :deep(.katex-display) {
  margin: 0;
  overflow-x: auto;
  overflow-y: hidden;
  padding-bottom: 2px;
}
.formula-block :deep(.katex) {
  font-size: clamp(0.9rem, 1.4vw, 1rem);
}

.derive-content > .derive-card:nth-child(1) { animation-delay: 0.1s; }
.derive-content > .derive-card:nth-child(2) { animation-delay: 0.2s; }
.derive-content > .derive-card:nth-child(3) { animation-delay: 0.3s; }
.derive-content > .derive-card:nth-child(4) { animation-delay: 0.4s; }

.derive-content > .derive-card:nth-child(1) .formula-block { animation-delay: 0.35s; }
.derive-content > .derive-card:nth-child(2) .formula-block { animation-delay: 0.45s; }
.derive-content > .derive-card:nth-child(3) .formula-block { animation-delay: 0.55s; }

.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(1) { animation-delay: 0.62s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(2) { animation-delay: 0.68s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(3) { animation-delay: 0.74s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(4) { animation-delay: 0.8s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(5) { animation-delay: 0.86s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(6) { animation-delay: 0.92s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(7) { animation-delay: 0.98s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(8) { animation-delay: 1.04s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(9) { animation-delay: 1.1s; }
.derive-content > .derive-card:nth-child(4) .formula-grid-two .formula-block:nth-child(10) { animation-delay: 1.16s; }

@media (max-width: 980px) {
  .derive-main { width: min(1280px, 96vw); }
  .derive-content { grid-template-columns: 1fr; }
  .derive-content .derive-card:not(.derive-card--half) { grid-column: auto; }
  .formula-grid-two { grid-template-columns: 1fr; }
}

@keyframes auroraFloatA {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(6vw, 4vh, 0) scale(1.08); }
}
@keyframes auroraFloatB {
  0% { transform: translate3d(0, 0, 0) scale(1); }
  100% { transform: translate3d(-5vw, -3vh, 0) scale(1.1); }
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
@keyframes cardFadeIn {
  from {
    opacity: 0;
    transform: translate3d(0, 12px, 0) scale(0.992);
  }
  to {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
  }
}
@keyframes formulaWrite {
  0% {
    opacity: 0;
    clip-path: inset(0 100% 0 0);
  }
  100% {
    opacity: 1;
    clip-path: inset(0 0 0 0);
  }
}
</style>
