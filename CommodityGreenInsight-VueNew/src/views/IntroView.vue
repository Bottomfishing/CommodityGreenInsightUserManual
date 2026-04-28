<template>
  <div class="intro-page">
    <AuthModal
      :visible="showAuth"
      @update:visible="showAuth = $event"
      @success="onAuthSuccess"
    />

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

    <main class="intro-main">
      <section class="left-col">
        <span class="kicker">GREEN FINTECH</span>
        <div class="intro-content-row">
          <h1 class="intro-title">
            <span>在这里您可以</span>
            <span>自己训练自己的</span>
            <span>金融模型</span>
          </h1>
          <div class="intro-copy">
            <p class="intro-desc">从数据接入到结果解释，完整构建你的金融建模与分析闭环。</p>
            <ul class="value-list">
              <li>您可以上传您自己更精准的数据训练</li>
              <li>如果你没有数据你也可以选用我们训练好的模型</li>
              <li>您可以看到精美的训练后的可视化</li>
            </ul>
          </div>
        </div>
        <div class="action-row">
          <button class="btn-primary" @click="goLogin">继续</button>
          <button class="btn-ghost" @click="router.push({ name: 'Landing' })">返回首页</button>
        </div>
      </section>

      <section class="right-col">
        <div class="right-main-row">
          <section
            class="right-block charts-block"
            :style="boardStyleCharts"
            @mousemove="(e) => onBlockMove(e, 'charts')"
            @mouseleave="() => onBlockLeave('charts')"
          >
            <div class="chart-stack">
            <article class="panel chart-panel">
              <div class="panel-head">
                <span class="tag">Loss 曲线（实时）</span>
                <span class="live"><i></i>ACTIVE</span>
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
                  <rect class="forecast-band" x="590" y="22" width="16" height="140" />
                  <path class="trend-line trend-line-a" d="M36,150 C78,144 88,36 110,112 C132,136 156,88 184,106 C216,124 242,98 270,114 C304,130 332,102 358,116 C390,128 418,104 448,116 C478,126 510,108 540,118 C574,128 606,112 638,120 C670,128 702,114 734,122 C766,130 800,116 832,124 C864,130 902,120 940,126 C958,128 970,130 980,128" />
                  <path class="trend-line trend-line-b" d="M36,156 C80,150 92,52 112,120 C136,142 162,98 188,114 C220,130 246,106 274,118 C308,134 336,110 362,120 C396,132 424,112 452,122 C482,132 514,116 544,124 C578,134 610,120 642,126 C674,134 706,122 738,128 C772,136 806,124 840,130 C874,136 910,128 944,132 C960,134 972,136 980,134" />
                  <circle class="trend-point trend-point-a" cx="980" cy="128" r="3.5" />
                  <circle class="trend-point trend-point-b" cx="980" cy="134" r="3.5" />
                </svg>
                <div class="chart-legend">
                  <span class="legend-item"><i class="legend-dot legend-dot-a"></i>train loss</span>
                  <span class="legend-item"><i class="legend-dot legend-dot-b"></i>valid loss</span>
                </div>
              </div>
            </article>

            <div class="chart-row-two">
              <article class="panel chart-panel chart-panel-half">
                <div class="panel-head">
                  <span class="tag">价格对比曲线（实时）</span>
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
                    <rect class="forecast-band" x="590" y="22" width="16" height="140" />
                    <path class="trend-line trend-line-c" d="M36,116 C72,118 104,112 136,102 C170,90 202,92 236,84 C270,76 304,84 338,78 C372,70 406,80 440,72 C474,64 508,74 542,70 C576,66 610,76 644,70 C678,64 712,74 746,68 C780,62 814,72 848,68 C882,64 914,72 946,68 C962,66 972,66 980,67" />
                    <path class="trend-line trend-line-d" d="M36,120 C72,122 104,116 136,106 C170,94 202,96 236,88 C270,80 304,88 338,82 C372,74 406,84 440,76 C474,68 508,78 542,74 C576,70 610,80 644,74 C678,68 712,78 746,72 C780,66 814,76 848,72 C882,68 914,76 946,72 C962,70 972,70 980,71" />
                    <circle class="trend-point trend-point-a" cx="980" cy="67" r="3.5" />
                    <circle class="trend-point trend-point-b" cx="980" cy="71" r="3.5" />
                  </svg>
                  <div class="chart-legend">
                    <span class="legend-item"><i class="legend-dot legend-dot-a"></i>actual price</span>
                    <span class="legend-item"><i class="legend-dot legend-dot-b"></i>pred price</span>
                  </div>
                </div>
              </article>

              <article class="panel chart-panel chart-panel-half">
                <div class="panel-head">
                  <span class="tag">收益率对比曲线（实时）</span>
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
                    <rect class="forecast-band" x="590" y="22" width="16" height="140" />
                    <path class="trend-line trend-line-e" d="M36,104 C52,118 70,132 86,104 C102,80 118,128 134,106 C150,82 166,132 182,108 C198,84 214,130 230,106 C246,82 262,132 278,108 C294,84 310,130 326,108 C342,86 358,132 374,110 C390,90 406,128 422,108 C438,90 454,132 470,108 C486,90 502,128 518,108 C534,90 550,132 566,110 C582,92 598,128 614,108 C630,92 646,132 662,110 C678,92 694,130 710,108 C726,92 742,132 758,110 C774,94 790,128 806,108 C822,94 838,132 854,110 C870,94 886,128 902,108 C918,96 934,132 950,110 C962,100 972,108 980,112" />
                    <path class="trend-line trend-line-f" d="M36,116 C52,100 70,90 86,118 C102,140 118,96 134,118 C150,142 166,98 182,120 C198,142 214,96 230,118 C246,140 262,98 278,120 C294,142 310,98 326,120 C342,140 358,96 374,118 C390,138 406,98 422,120 C438,140 454,98 470,120 C486,140 502,96 518,118 C534,138 550,98 566,120 C582,138 598,100 614,120 C630,140 646,98 662,120 C678,140 694,98 710,118 C726,138 742,100 758,120 C774,140 790,98 806,118 C822,138 838,100 854,120 C870,138 886,100 902,118 C918,136 934,100 950,118 C962,126 972,122 980,120" />
                    <circle class="trend-point trend-point-a" cx="980" cy="112" r="3.5" />
                    <circle class="trend-point trend-point-b" cx="980" cy="120" r="3.5" />
                  </svg>
                  <div class="chart-legend">
                    <span class="legend-item"><i class="legend-dot legend-dot-a"></i>actual return</span>
                    <span class="legend-item"><i class="legend-dot legend-dot-b"></i>pred return</span>
                  </div>
                </div>
              </article>
            </div>
            </div>
          </section>

          <section
            class="right-block demo-block"
            :style="boardStyleDemo"
            @mousemove="(e) => onBlockMove(e, 'demo')"
            @mouseleave="() => onBlockLeave('demo')"
          >
            <article class="feature-demo-panel">
              <div class="feature-demo-head">
                <p class="feature-demo-title">您可以通过以下板块进行自己金融模型的训练：</p>
              </div>
              <div class="demo-grid">
                <div class="demo-card">
                  <div class="demo-icon">TR</div>
                  <strong>开始训练</strong>
                  <span>GRU / LSTM 模型</span>
                </div>
                <div class="demo-card">
                  <div class="demo-icon">MO</div>
                  <strong>训练监控</strong>
                  <span>实时进度 / 日志</span>
                </div>
                <div class="demo-card">
                  <div class="demo-icon">AN</div>
                  <strong>结果分析</strong>
                  <span>点击查看详情</span>
                </div>
                <div class="demo-card">
                  <div class="demo-icon">EX</div>
                  <strong>下载导出</strong>
                  <span>报告 / 图表 / ZIP</span>
                </div>
              </div>
            </article>
          </section>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import AuthModal from "@/components/AuthModal.vue";

const router = useRouter();
const showAuth = ref(false);
const particleRef = ref<HTMLCanvasElement | null>(null);
const boardStyleCharts = ref<Record<string, string>>({});
const boardStyleDemo = ref<Record<string, string>>({});

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
    const count = Math.max(36, Math.floor((canvas.width * canvas.height) / 42000));
    particles = Array.from({ length: count }, () => ({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.24,
      vy: (Math.random() - 0.5) * 0.24,
      r: Math.random() * 1.8 + 0.6,
      a: Math.random() * 0.4 + 0.14,
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

function onBlockMove(event: MouseEvent, which: "charts" | "demo") {
  const el = event.currentTarget as HTMLElement;
  const rect = el.getBoundingClientRect();
  const x = event.clientX - rect.left;
  const y = event.clientY - rect.top;
  const rx = ((y / rect.height) * 2 - 1) * -4;
  const ry = ((x / rect.width) * 2 - 1) * 4.5;
  const style = { transform: `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg)` };
  if (which === "charts") boardStyleCharts.value = style;
  else boardStyleDemo.value = style;
}
function onBlockLeave(which: "charts" | "demo") {
  const style = {
    transition: "transform .5s cubic-bezier(.22,1,.36,1)",
    transform: "perspective(1000px) rotateX(0) rotateY(0)",
  };
  if (which === "charts") boardStyleCharts.value = style;
  else boardStyleDemo.value = style;
}

function goLogin() {
  router.push({ name: "IntroCharts" });
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
.intro-page {
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
  background:
    conic-gradient(
      from 0deg at 50% 50%,
      rgba(56, 189, 248, 0.18),
      rgba(99, 102, 241, 0.08),
      rgba(45, 212, 191, 0.12),
      rgba(56, 189, 248, 0.18)
    );
  opacity: 0.24;
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
  opacity: 0.24;
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
  opacity: 0.14;
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
.intro-main {
  position: relative;
  z-index: 1;
  width: min(1180px, 95vw);
  min-height: 100vh;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1fr;
  gap: 14px;
  align-items: start;
  padding: 24px 0 28px;
  animation: sceneEnter 0.9s cubic-bezier(.22, 1, .36, 1) both;
}
.left-col {
  display: flex;
  flex-direction: column;
  gap: 12px;
  max-width: 760px;
  width: 100%;
}
.intro-content-row {
  display: grid;
  grid-template-columns: minmax(0, 1.1fr) minmax(0, 0.9fr);
  gap: 22px;
  align-items: start;
}
.intro-copy {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding-top: 8px;
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
.intro-title {
  margin: 0;
  font-size: clamp(34px, 4.6vw, 56px);
  line-height: 1.13;
  font-weight: 800;
  letter-spacing: 0.025em;
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
.intro-title span {
  display: block;
}
.intro-desc {
  margin: 0;
  font-size: 15px;
  color: rgba(191, 219, 254, 0.86);
  line-height: 1.85;
  animation: fadeUp 0.7s ease-out 0.2s both;
}
.value-list {
  margin: 4px 0 0;
  padding-left: 18px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: rgba(186, 230, 253, 0.9);
  font-size: 13px;
  line-height: 1.65;
  animation: fadeUp 0.8s ease-out 0.3s both;
}
.value-list li::marker {
  color: rgba(34, 211, 238, 0.9);
}
.value-list li {
  animation: listReveal 0.6s ease both;
}
.value-list li:nth-child(1) { animation-delay: 0.34s; }
.value-list li:nth-child(2) { animation-delay: 0.42s; }
.value-list li:nth-child(3) { animation-delay: 0.5s; }
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
.right-col {
  border: none;
  border-radius: 0;
  background: transparent;
  box-shadow: none;
  padding: 0;
  transition: transform .2s ease;
  width: 100%;
}
.right-block {
  position: relative;
  border: 1px solid rgba(56, 189, 248, 0.22);
  border-radius: 16px;
  background:
    radial-gradient(circle at 90% 0%, rgba(56, 189, 248, 0.1), transparent 42%),
    linear-gradient(180deg, rgba(5, 16, 35, 0.86), rgba(3, 10, 24, 0.86));
  box-shadow:
    0 18px 40px rgba(2, 6, 23, 0.42),
    inset 0 0 24px rgba(56, 189, 248, 0.08);
  padding: 12px 14px;
  overflow: hidden;
  animation: boardGlow 5s ease-in-out infinite;
}
.right-block::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: 1px solid rgba(99, 102, 241, 0.14);
  pointer-events: none;
}
.charts-block {
  background:
    radial-gradient(circle at 85% 10%, rgba(56, 189, 248, 0.12), transparent 45%),
    linear-gradient(180deg, rgba(6, 18, 42, 0.86), rgba(3, 10, 24, 0.86));
}
.demo-block {
  background:
    radial-gradient(circle at 15% 12%, rgba(99, 102, 241, 0.12), transparent 48%),
    linear-gradient(180deg, rgba(6, 18, 42, 0.86), rgba(3, 10, 24, 0.86));
}
.charts-block .panel:first-child {
  margin-top: 0;
}
.demo-block {
  display: flex;
  flex-direction: column;
}
.panel {
  position: relative;
  border: 1px solid rgba(56, 189, 248, 0.15);
  border-radius: 10px;
  padding: 8px 10px 6px;
  background: rgba(2, 10, 24, 0.42);
  overflow: hidden;
}
.panel::after {
  content: "";
  position: absolute;
  inset: -1px;
  border-radius: inherit;
  background: linear-gradient(
    120deg,
    transparent 20%,
    rgba(56, 189, 248, 0.22) 48%,
    rgba(167, 139, 250, 0.2) 52%,
    transparent 80%
  );
  transform: translateX(-120%);
  animation: panelSweep 7.5s linear infinite;
  pointer-events: none;
}
.panel + .panel {
  margin-top: 8px;
}
.right-main-row {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(0, 1fr);
  gap: 16px;
  margin-top: 0;
  align-items: stretch;
}
.chart-stack {
  display: flex;
  flex-direction: column;
}
.chart-row-two {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
  margin-top: 8px;
}
.chart-panel {
  padding: 8px 10px 10px;
}
.chart-panel-half {
  margin-top: 0;
}
.chart-frame {
  height: 176px;
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
}
.chart-frame::after {
  content: "";
  position: absolute;
  top: 8px;
  bottom: 24px;
  width: 1px;
  background: linear-gradient(180deg, transparent, rgba(56, 189, 248, 0.7), transparent);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.5);
  animation: cursorSweep 5.2s linear infinite;
  pointer-events: none;
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
  animation: lineFloat 4.8s ease-in-out infinite;
}
.trend-line-a,
.trend-line-c,
.trend-line-e {
  stroke: #38bdf8;
}
.trend-line-b,
.trend-line-d,
.trend-line-f {
  stroke: #34d399;
  animation-delay: 0.25s;
  filter: drop-shadow(0 0 4px rgba(52, 211, 153, 0.35));
}
.trend-line-c,
.trend-line-d {
  animation-duration: 5.6s;
}
.trend-line-e,
.trend-line-f {
  animation-duration: 4.1s;
}
.chart-legend {
  height: 20px;
  margin-top: -1px;
  padding: 0 8px;
  display: flex;
  align-items: center;
  gap: 14px;
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
.trend-point {
  opacity: 0.95;
  animation: pointBlink 2.2s ease-in-out infinite;
}
.trend-point-a {
  fill: #38bdf8;
  filter: drop-shadow(0 0 6px rgba(56, 189, 248, 0.65));
}
.trend-point-b {
  fill: #34d399;
  filter: drop-shadow(0 0 6px rgba(52, 211, 153, 0.55));
  animation-delay: 0.2s;
}
.feature-demo-panel {
  margin: 0;
  padding: 0;
  height: 100%;
  display: flex;
  flex-direction: column;
}
.feature-demo-head {
  flex: 1 1 auto;
  display: flex;
  align-items: center;
}
.feature-demo-title {
  margin: 0;
font-size: clamp(20px, 2.1vw, 28px);
  font-weight: 800;
  line-height: 1.2;
  letter-spacing: 0.02em;
  color: transparent;
  background: linear-gradient(92deg, #e0f2fe 0%, #67e8f9 38%, #60a5fa 70%, #c4b5fd 100%);
  -webkit-background-clip: text;
  background-clip: text;
  -webkit-text-fill-color: transparent;
  text-shadow:
    0 0 14px rgba(56, 189, 248, 0.26),
    0 0 28px rgba(99, 102, 241, 0.2);
}
.demo-grid {
  margin-top: auto;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.demo-card {
  position: relative;
  min-height: 118px;
  padding: 12px 12px 10px;
  border: 1px solid rgba(56, 189, 248, 0.28);
  border-radius: 12px;
  background: linear-gradient(180deg, rgba(4, 14, 33, 0.8), rgba(2, 10, 24, 0.78));
  clip-path: polygon(8% 0%, 92% 0%, 100% 16%, 100% 100%, 0% 100%, 0% 12%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 6px;
  text-align: center;
}
.demo-card::before {
  content: "";
  position: absolute;
  inset: 0;
  border-radius: inherit;
  border: 1px solid rgba(96, 165, 250, 0.28);
  opacity: 0.7;
  pointer-events: none;
}
.demo-icon {
  width: 38px;
  height: 38px;
  border-radius: 12px;
  display: grid;
  place-items: center;
  font-size: 11px;
  font-weight: 700;
  letter-spacing: 0.08em;
  color: #7dd3fc;
  background: rgba(15, 23, 42, 0.9);
  border: 1px solid rgba(56, 189, 248, 0.45);
  box-shadow: 0 0 12px rgba(56, 189, 248, 0.25);
}
.demo-card strong {
  font-size: 15px;
  color: #e2e8f0;
}
.demo-card span {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.88);
}
.panel-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 6px;
}
.tiny-time {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.74);
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
.cap-list {
  margin-top: 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.cap-item {
  border: 1px solid rgba(56, 189, 248, 0.14);
  border-radius: 9px;
  padding: 8px 10px;
  background: rgba(2, 10, 24, 0.45);
}
.cap-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10px;
  margin-bottom: 6px;
}
.cap-row strong {
  font-size: 13px;
  color: #e2e8f0;
}
.cap-row span {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.82);
}
.cap-bar {
  height: 5px;
  border-radius: 999px;
  background: rgba(30, 41, 59, 0.82);
  overflow: hidden;
}
.cap-bar i {
  display: block;
  height: 100%;
  border-radius: inherit;
  background: linear-gradient(90deg, #22d3ee, #3b82f6);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.45);
}
.snap-grid {
  margin-top: 4px;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.snap-card {
  border: 1px solid rgba(56, 189, 248, 0.18);
  border-radius: 10px;
  padding: 8px 10px;
  background: rgba(2, 10, 24, 0.45);
}
.snap-card label {
  display: block;
  font-size: 10px;
  color: rgba(148, 163, 184, 0.8);
}
.snap-card strong {
  font-size: 16px;
  color: #e2e8f0;
}
.snap-card strong.ok {
  color: #34d399;
}
.progress-line {
  margin-top: 8px;
}
.flow-track {
  margin-top: 2px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
.flow-node {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.85);
  border: 1px solid rgba(148, 163, 184, 0.25);
  border-radius: 999px;
  padding: 5px 10px;
  background: rgba(30, 41, 59, 0.4);
}
.flow-node.done {
  color: #a7f3d0;
  border-color: rgba(52, 211, 153, 0.36);
  background: rgba(6, 95, 70, 0.28);
}
.flow-node.active {
  color: #e0f2fe;
  border-color: rgba(56, 189, 248, 0.55);
  background: rgba(8, 47, 73, 0.52);
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.22);
}
@media (max-width: 980px) {
  .intro-main {
    grid-template-columns: 1fr;
    padding: 28px 0;
  }
  .left-col {
    padding: 0;
  }
  .intro-content-row {
    grid-template-columns: 1fr;
    gap: 8px;
  }
  .intro-copy {
    padding-top: 0;
  }
  .right-col {
    width: 100%;
  }
  .right-main-row {
    grid-template-columns: 1fr;
  }
  .chart-row-two {
    grid-template-columns: 1fr;
  }
  .demo-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .snap-grid {
    grid-template-columns: 1fr;
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
@keyframes boardGlow {
  0%, 100% { box-shadow: 0 18px 40px rgba(2, 6, 23, 0.42), inset 0 0 24px rgba(56, 189, 248, 0.08); }
  50% { box-shadow: 0 22px 50px rgba(2, 6, 23, 0.5), inset 0 0 28px rgba(99, 102, 241, 0.18); }
}
@keyframes panelSweep {
  0% { transform: translateX(-120%); opacity: 0; }
  8% { opacity: 0.75; }
  22% { transform: translateX(120%); opacity: 0; }
  100% { transform: translateX(120%); opacity: 0; }
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
@keyframes titleFocusIn {
  0% {
    opacity: 0.55;
    transform: translate3d(0, 12px, 0) scale(0.985);
    filter: blur(7px);
  }
  60% {
    opacity: 0.95;
    transform: translate3d(0, 1px, 0) scale(1);
    filter: blur(1.5px);
  }
  100% {
    opacity: 1;
    transform: translate3d(0, 0, 0) scale(1);
    filter: blur(0);
  }
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
@keyframes titleUnderline {
  0%, 100% { opacity: 0; transform: scaleX(0.65); }
  35%, 55% { opacity: 0.9; transform: scaleX(1); }
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
@keyframes listReveal {
  from { opacity: 0; transform: translateX(-8px); }
  to { opacity: 1; transform: translateX(0); }
}
@keyframes lineFloat {
  0%, 100% { opacity: 0.86; }
  50% { opacity: 1; }
}
@keyframes pointBlink {
  0%, 100% { transform: scale(1); opacity: 0.9; }
  50% { transform: scale(1.08); opacity: 1; }
}
@keyframes cursorSweep {
  0% { left: 40px; opacity: 0; }
  10% { opacity: 1; }
  90% { opacity: 1; }
  100% { left: calc(100% - 18px); opacity: 0; }
}
</style>
