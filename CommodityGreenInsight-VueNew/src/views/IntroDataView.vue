<template>
  <div class="intro3-page">
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

    <main class="intro3-main">
      <section class="hero">
        <span class="kicker">GREEN FINTECH</span>
        <h1 class="hero-title">您可以在本web获得全球各地的金融数据</h1>
        <p class="hero-sub">多市场覆盖 · 实时更新 · 结构化汇聚 · 便于建模</p>
        <div class="action-row">
          <button class="btn-primary" @click="router.push({ name: 'IntroGlobe' })">继续</button>
          <button class="btn-ghost" @click="router.push({ name: 'IntroCharts' })">返回上一页</button>
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
            <span class="tag">全球数据行情（蜡烛图）</span>
            <span class="live"><i></i>LIVE</span>
          </div>
          <div class="chart-frame">
            <div class="candle-stack">
            <svg viewBox="0 0 1000 230" preserveAspectRatio="xMinYMin meet" class="trend-svg">
              <g class="trend-gridline">
                <line x1="36" y1="30" x2="980" y2="30" />
                <line x1="36" y1="70" x2="980" y2="70" />
                <line x1="36" y1="110" x2="980" y2="110" />
                <line x1="36" y1="150" x2="980" y2="150" />
                <line x1="36" y1="190" x2="980" y2="190" />
              </g>
              <line class="trend-axis" x1="36" y1="190" x2="980" y2="190" />
              <line class="trend-axis" x1="36" y1="24" x2="36" y2="190" />
              <text class="axis-label" x="24" y="34">120</text>
              <text class="axis-label" x="24" y="74">110</text>
              <text class="axis-label" x="24" y="114">100</text>
              <text class="axis-label" x="24" y="154">90</text>
              <text class="axis-label" x="24" y="194">80</text>

              <line class="wick wick-up" x1="72" y1="170" x2="72" y2="146" />
              <rect class="candle candle-up" x="64" y="152" width="16" height="14" />
              <line class="wick wick-up" x1="105" y1="162" x2="105" y2="128" />
              <rect class="candle candle-up" x="97" y="136" width="16" height="20" />
              <line class="wick wick-down" x1="138" y1="124" x2="138" y2="144" />
              <rect class="candle candle-down" x="130" y="130" width="16" height="12" />
              <line class="wick wick-down" x1="171" y1="128" x2="171" y2="148" />
              <rect class="candle candle-down" x="163" y="136" width="16" height="10" />
              <line class="wick wick-up" x1="204" y1="84" x2="204" y2="122" />
              <rect class="candle candle-up" x="196" y="90" width="16" height="30" />
              <line class="wick wick-down" x1="237" y1="92" x2="237" y2="108" />
              <rect class="candle candle-down" x="229" y="96" width="16" height="8" />
              <line class="wick wick-down" x1="270" y1="82" x2="270" y2="96" />
              <rect class="candle candle-down" x="262" y="84" width="16" height="10" />
              <line class="wick wick-down" x1="303" y1="100" x2="303" y2="146" />
              <rect class="candle candle-down" x="295" y="102" width="16" height="36" />
              <line class="wick wick-up" x1="336" y1="122" x2="336" y2="134" />
              <rect class="candle candle-up" x="328" y="124" width="16" height="8" />
              <line class="wick wick-down" x1="369" y1="112" x2="369" y2="126" />
              <rect class="candle candle-down" x="361" y="114" width="16" height="10" />
              <line class="wick wick-down" x1="402" y1="102" x2="402" y2="116" />
              <rect class="candle candle-down" x="394" y="104" width="16" height="10" />
              <line class="wick wick-down" x1="435" y1="112" x2="435" y2="156" />
              <rect class="candle candle-down" x="427" y="114" width="16" height="28" />
              <line class="wick wick-down" x1="468" y1="142" x2="468" y2="160" />
              <rect class="candle candle-down" x="460" y="144" width="16" height="8" />
              <line class="wick wick-up" x1="501" y1="124" x2="501" y2="142" />
              <rect class="candle candle-up" x="493" y="126" width="16" height="12" />
              <line class="wick wick-down" x1="534" y1="156" x2="534" y2="190" />
              <rect class="candle candle-down" x="526" y="158" width="16" height="20" />
              <line class="wick wick-up" x1="567" y1="144" x2="567" y2="166" />
              <rect class="candle candle-up" x="559" y="148" width="16" height="14" />
              <line class="wick wick-up" x1="600" y1="136" x2="600" y2="166" />
              <rect class="candle candle-up" x="592" y="142" width="16" height="18" />
              <line class="wick wick-up" x1="633" y1="142" x2="633" y2="162" />
              <rect class="candle candle-up" x="625" y="146" width="16" height="12" />
              <line class="wick wick-down" x1="666" y1="132" x2="666" y2="184" />
              <rect class="candle candle-down" x="658" y="138" width="16" height="24" />
              <line class="wick wick-up" x1="699" y1="104" x2="699" y2="166" />
              <rect class="candle candle-up" x="691" y="122" width="16" height="26" />
              <line class="wick wick-up" x1="732" y1="128" x2="732" y2="150" />
              <rect class="candle candle-up" x="724" y="130" width="16" height="10" />
              <line class="wick wick-down" x1="765" y1="108" x2="765" y2="160" />
              <rect class="candle candle-down" x="757" y="122" width="16" height="26" />
              <line class="wick wick-up" x1="798" y1="96" x2="798" y2="164" />
              <rect class="candle candle-up" x="790" y="114" width="16" height="24" />
              <line class="wick wick-up" x1="831" y1="102" x2="831" y2="150" />
              <rect class="candle candle-up" x="823" y="118" width="16" height="22" />
              <line class="wick wick-down" x1="864" y1="110" x2="864" y2="174" />
              <rect class="candle candle-down" x="856" y="124" width="16" height="24" />
              <line class="wick wick-up" x1="897" y1="98" x2="897" y2="166" />
              <rect class="candle candle-up" x="889" y="116" width="16" height="24" />
              <line class="wick wick-down" x1="930" y1="106" x2="930" y2="170" />
              <rect class="candle candle-down" x="922" y="120" width="16" height="24" />
              <line class="wick wick-up" x1="963" y1="110" x2="963" y2="140" />
              <rect class="candle candle-up" x="955" y="113" width="16" height="15" />

              <text class="date-label" x="64" y="214">2026-03-26</text>
              <text class="date-label" x="205" y="214">2026-04-06</text>
              <text class="date-label" x="402" y="214">2026-04-14</text>
              <text class="date-label" x="620" y="214">2026-04-22</text>
              <text class="date-label" x="832" y="214">2026-04-30</text>
            </svg>

            <svg viewBox="0 0 1000 230" preserveAspectRatio="xMinYMin meet" class="trend-svg">
              <g class="trend-gridline">
                <line x1="36" y1="30" x2="980" y2="30" />
                <line x1="36" y1="70" x2="980" y2="70" />
                <line x1="36" y1="110" x2="980" y2="110" />
                <line x1="36" y1="150" x2="980" y2="150" />
                <line x1="36" y1="190" x2="980" y2="190" />
              </g>
              <line class="trend-axis" x1="36" y1="190" x2="980" y2="190" />
              <line class="trend-axis" x1="36" y1="24" x2="36" y2="190" />

              <text class="axis-label" x="24" y="34">120</text>
              <text class="axis-label" x="24" y="74">110</text>
              <text class="axis-label" x="24" y="114">100</text>
              <text class="axis-label" x="24" y="154">90</text>
              <text class="axis-label" x="24" y="194">80</text>

              <line class="wick wick-up" x1="70" y1="169" x2="70" y2="145" />
              <rect class="candle candle-up" x="64" y="150" width="12" height="14" />
              <line class="wick wick-down" x1="100" y1="143" x2="100" y2="169" />
              <rect class="candle candle-down" x="94" y="148" width="12" height="16" />
              <line class="wick wick-up" x1="130" y1="173" x2="130" y2="149" />
              <rect class="candle candle-up" x="124" y="154" width="12" height="14" />
              <line class="wick wick-up" x1="160" y1="151" x2="160" y2="125" />
              <rect class="candle candle-up" x="154" y="130" width="12" height="16" />
              <line class="wick wick-down" x1="190" y1="121" x2="190" y2="151" />
              <rect class="candle candle-down" x="184" y="126" width="12" height="20" />
              <line class="wick wick-up" x1="220" y1="137" x2="220" y2="109" />
              <rect class="candle candle-up" x="214" y="114" width="12" height="18" />
              <line class="wick wick-down" x1="250" y1="107" x2="250" y2="139" />
              <rect class="candle candle-down" x="244" y="112" width="12" height="22" />
              <line class="wick wick-up" x1="280" y1="119" x2="280" y2="91" />
              <rect class="candle candle-up" x="274" y="96" width="12" height="18" />
              <line class="wick wick-up" x1="310" y1="113" x2="310" y2="85" />
              <rect class="candle candle-up" x="304" y="90" width="12" height="18" />
              <line class="wick wick-down" x1="340" y1="99" x2="340" y2="131" />
              <rect class="candle candle-down" x="334" y="104" width="12" height="22" />
              <line class="wick wick-up" x1="370" y1="127" x2="370" y2="99" />
              <rect class="candle candle-up" x="364" y="104" width="12" height="18" />
              <line class="wick wick-down" x1="400" y1="105" x2="400" y2="141" />
              <rect class="candle candle-down" x="394" y="112" width="12" height="24" />
              <line class="wick wick-up" x1="430" y1="137" x2="430" y2="109" />
              <rect class="candle candle-up" x="424" y="114" width="12" height="18" />
              <line class="wick wick-up" x1="460" y1="133" x2="460" y2="103" />
              <rect class="candle candle-up" x="454" y="108" width="12" height="20" />
              <line class="wick wick-down" x1="490" y1="117" x2="490" y2="151" />
              <rect class="candle candle-down" x="484" y="124" width="12" height="22" />
              <line class="wick wick-up" x1="520" y1="151" x2="520" y2="123" />
              <rect class="candle candle-up" x="514" y="128" width="12" height="18" />
              <line class="wick wick-down" x1="550" y1="129" x2="550" y2="159" />
              <rect class="candle candle-down" x="544" y="134" width="12" height="20" />
              <line class="wick wick-up" x1="580" y1="157" x2="580" y2="129" />
              <rect class="candle candle-up" x="574" y="134" width="12" height="18" />
              <line class="wick wick-up" x1="610" y1="149" x2="610" y2="121" />
              <rect class="candle candle-up" x="604" y="126" width="12" height="18" />
              <line class="wick wick-down" x1="640" y1="139" x2="640" y2="169" />
              <rect class="candle candle-down" x="634" y="144" width="12" height="20" />
              <line class="wick wick-up" x1="670" y1="165" x2="670" y2="137" />
              <rect class="candle candle-up" x="664" y="142" width="12" height="18" />
              <line class="wick wick-down" x1="700" y1="133" x2="700" y2="169" />
              <rect class="candle candle-down" x="694" y="138" width="12" height="22" />
              <line class="wick wick-up" x1="730" y1="161" x2="730" y2="133" />
              <rect class="candle candle-up" x="724" y="138" width="12" height="18" />
              <line class="wick wick-up" x1="760" y1="155" x2="760" y2="127" />
              <rect class="candle candle-up" x="754" y="132" width="12" height="18" />
              <line class="wick wick-down" x1="790" y1="141" x2="790" y2="173" />
              <rect class="candle candle-down" x="784" y="148" width="12" height="20" />
              <line class="wick wick-up" x1="820" y1="171" x2="820" y2="143" />
              <rect class="candle candle-up" x="814" y="148" width="12" height="18" />
              <line class="wick wick-up" x1="850" y1="161" x2="850" y2="133" />
              <rect class="candle candle-up" x="844" y="138" width="12" height="18" />
              <line class="wick wick-down" x1="880" y1="137" x2="880" y2="167" />
              <rect class="candle candle-down" x="874" y="142" width="12" height="20" />
              <line class="wick wick-up" x1="910" y1="165" x2="910" y2="137" />
              <rect class="candle candle-up" x="904" y="142" width="12" height="18" />
              <line class="wick wick-up" x1="940" y1="157" x2="940" y2="129" />
              <rect class="candle candle-up" x="934" y="134" width="12" height="18" />
              <line class="wick wick-down" x1="970" y1="141" x2="970" y2="169" />
              <rect class="candle candle-down" x="964" y="146" width="12" height="18" />

              <text class="date-label" x="64" y="214">2026-03-26</text>
              <text class="date-label" x="255" y="214">2026-04-06</text>
              <text class="date-label" x="440" y="214">2026-04-14</text>
              <text class="date-label" x="650" y="214">2026-04-22</text>
              <text class="date-label" x="840" y="214">2026-04-30</text>
            </svg>
            </div>
            <div class="chart-legend">
              <span class="legend-item"><i class="legend-dot legend-dot-a"></i>上涨</span>
              <span class="legend-item"><i class="legend-dot legend-dot-b"></i>下跌</span>
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
.intro3-page {
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

.intro3-main {
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
  font-size: clamp(34px, 4.3vw, 52px);
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
  height: 300px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  border-radius: 10px;
  background:
    repeating-linear-gradient(
      0deg,
      rgba(148, 163, 184, 0.08) 0px,
      rgba(148, 163, 184, 0.08) 1px,
      transparent 1px,
      transparent 40px
    ),
    linear-gradient(180deg, rgba(2, 10, 24, 0.62), rgba(2, 10, 24, 0.82));
  overflow: hidden;
  position: relative;
  animation: fadeUp 0.75s ease-out 0.34s both;
}
.candle-stack {
  height: calc(100% - 20px);
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.trend-svg {
  width: 100%;
  flex: 1 1 0;
  height: auto;
}
.trend-gridline line {
  stroke: rgba(148, 163, 184, 0.2);
  stroke-width: 1;
}
.trend-axis {
  stroke: rgba(148, 163, 184, 0.45);
  stroke-width: 1.2;
}
.wick {
  stroke-width: 2.2;
}
.wick-up {
  stroke: #22c55e;
}
.wick-down {
  stroke: #ef4444;
}
.candle {
  rx: 2;
}
.candle-up {
  fill: rgba(34, 197, 94, 0.9);
  stroke: #22c55e;
  stroke-width: 1.2;
}
.candle-down {
  fill: rgba(239, 68, 68, 0.9);
  stroke: #ef4444;
  stroke-width: 1.2;
}
.axis-label {
  fill: rgba(148, 163, 184, 0.9);
  font-size: 11px;
  text-anchor: end;
}
.date-label {
  fill: rgba(148, 163, 184, 0.85);
  font-size: 11px;
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
  background: #22c55e;
  box-shadow: 0 0 8px rgba(34, 197, 94, 0.5);
}
.legend-dot-b {
  background: #ef4444;
  box-shadow: 0 0 8px rgba(239, 68, 68, 0.45);
}

@media (max-width: 980px) {
  .intro3-main {
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

