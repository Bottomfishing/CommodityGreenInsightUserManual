<template>
  <div class="landing">
    <!-- 登录弹框 -->
    <AuthModal
      :visible="showAuth"
      @update:visible="showAuth = $event"
      @success="onAuthSuccess"
    />

    <!-- 背景 -->
    <div class="bg-layer" aria-hidden="true">
      <div class="noise"></div>
      <div class="glow glow--1"></div>
      <div class="glow glow--2"></div>
    </div>

    <!-- 主内容 -->
    <main class="main-grid">
      <!-- ══ 左侧品牌区（垂直居中）══ -->
      <section class="brand-col">
        <header class="top-mark">
          <span class="mark-line"></span>
          <span class="mark-text">GREEN FINTECH</span>
        </header>

        <h1 class="hero-title"><span class="title-line">大宗绿测</span></h1>

        <p class="hero-desc">基于油价因子的绿色金融产品预测与风险分析平台</p>

        <!-- 功能列表 -->
        <ul class="feat-list">
          <li class="feat-item feat--1">
            <span class="feat-num">01</span>
            <div class="feat-body">
              <strong>油价智能预测</strong
              ><span>GRU 深度学习时序模型，精准预测原油价格走势</span>
            </div>
          </li>
          <li class="feat-item feat--2">
            <span class="feat-num">02</span>
            <div class="feat-body">
              <strong>新能源股票分析</strong
              ><span>多因子模型评估收益趋势，捕捉板块机会</span>
            </div>
          </li>
          <li class="feat-item feat--3">
            <span class="feat-num">03</span>
            <div class="feat-body">
              <strong>绿色债券风控</strong
              ><span>违约风险实时评估与定价模型</span>
            </div>
          </li>
          <li class="feat-item feat--4">
            <span class="feat-num">04</span>
            <div class="feat-body">
              <strong>AI 智能报告</strong
              ><span>自动生成解读报告与策略建议</span>
            </div>
          </li>
        </ul>

        <!-- CTA -->
        <div class="cta-row">
          <button class="cta-primary" @click="showAuth = true">
            <span>立即开始</span>
            <svg
              width="16"
              height="16"
              viewBox="0 0 24 24"
              fill="none"
              stroke="currentColor"
              stroke-width="2.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            >
              <path d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          </button>
          <button class="cta-secondary" @click="openManual">用户手册</button>
        </div>

        <footer class="status-bar">
          <span class="status-dot"></span><span>SYSTEM ONLINE</span
          ><span class="divider">&middot;</span><span>{{ currentTime }}</span>
        </footer>
      </section>

      <!-- ══ 右侧：数据驾驶舱 ═══ -->
      <aside class="viz-col">
        <!-- Canvas 粒子底层 -->
        <canvas ref="canvasRef" class="viz-canvas" aria-hidden="true"></canvas>

        <!-- 驾驶舱容器（在 Canvas 之上） -->
        <div class="dash-container">
          <!-- 左上角：油价卡片 -->
          <div class="dc-price">
            <div class="dc-head">
              <span class="dc-dot dc-dot--g"></span>
              <span class="dc-label">OIL PRICE</span>
              <span class="dc-delta dc-up">+2.34%</span>
            </div>
            <div class="dc-price-val">$78.42</div>
            <canvas
              ref="priceChartRef"
              class="dc-spark"
              width="160"
              height="36"
              aria-hidden="true"
            ></canvas>
          </div>

          <!-- 右上角：新能源卡片 -->
          <div class="dc-stock">
            <div class="dc-head">
              <span class="dc-dot dc-dot--b"></span>
              <span class="dc-label">NEW ENERGY</span>
            </div>
            <div class="dc-metrics">
              <div class="dcm-row">
                <span class="dcm-name">CSI新能源</span
                ><span class="dcm-val"
                  >3,847 <small class="dcm-ch dcm-up">+1.82%</small></span
                >
              </div>
              <div class="dcm-row">
                <span class="dcm-name">光伏产业</span
                ><span class="dcm-val"
                  >4,126 <small class="dcm-ch dcm-up">+0.95%</small></span
                >
              </div>
            </div>
          </div>

          <!-- 左下角：债券卡片 -->
          <div class="dc-bond">
            <div class="dc-head">
              <span class="dc-dot dc-dot--p"></span>
              <span class="dc-label">BOND / RATE</span>
            </div>
            <div class="dc-metrics">
              <div class="dcm-row">
                <span class="dcm-name">10Y国债</span
                ><span class="dcm-val">2.34<small>%</small></span>
              </div>
              <div class="dcm-row">
                <span class="dcm-name">SHIBOR</span
                ><span class="dcm-val">1.68<small>%</small></span>
              </div>
            </div>
          </div>

          <!-- 右下角：AI卡片 -->
          <div class="dc-ai">
            <div class="dc-head">
              <span class="dc-dot dc-dot--o"></span>
              <span class="dc-label">AI MODEL</span>
            </div>
            <div class="ai-block">
              <span class="ai-lbl">预测准确率</span>
              <span class="ai-pct">94.7%</span>
              <div class="ai-bar">
                <div class="ai-fill" style="width: 94.7%"></div>
              </div>
            </div>
          </div>

          <!-- 中间：主图表 -->
          <div class="dc-chart">
            <div class="dc-head">
              <span class="dc-dot dc-dot--g"></span>
              <span class="dc-label">PRICE FORECAST TREND</span>
              <span class="dc-sub">布伦特原油 · 30日模拟数据</span>
            </div>
            <canvas
              ref="chartCanvasRef"
              class="chart-canvas"
              width="440"
              height="170"
              aria-hidden="true"
            ></canvas>
          </div>

          <!-- 连接线装饰 -->
          <div class="dash-connections">
            <div class="conn-line conn-top"></div>
            <div class="conn-line conn-left"></div>
            <div class="conn-line conn-right"></div>
            <div class="conn-line conn-bottom"></div>
          </div>
        </div>
        <!-- /.dash-container -->

        <!-- 装饰元素 -->
        <div class="frame-tl"></div>
        <div class="frame-tr"></div>
        <div class="frame-bl"></div>
        <div class="frame-br"></div>
        <div class="live-tag"><span class="lt-dot"></span>LIVE DATA</div>
      </aside>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import AuthModal from "@/components/AuthModal.vue";
import { getToken } from "@/api/auth";

const router = useRouter();
const showAuth = ref(false);
const canvasRef = ref<HTMLCanvasElement | null>(null);
const priceChartRef = ref<HTMLCanvasElement | null>(null);
const chartCanvasRef = ref<HTMLCanvasElement | null>(null);
const currentTime = ref("");

// ===== 时钟 =====
let clockTimer: number;
function updateClock() {
  const d = new Date();
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  currentTime.value = h + ":" + m + ":" + s;
}

// ===== Canvas 粒子背景 =====
interface Particle {
  x: number;
  y: number;
  vx: number;
  vy: number;
  r: number;
  alpha: number;
  hue: number;
}
let particles: Particle[] = [];
let animId: number | null = null;
let mousePos = { x: 0, y: 0 };

function initCanvas() {
  const c = canvasRef.value;
  if (!c) return;
  const ctx = c.getContext("2d");
  if (!ctx) return;
  function resize() {
    const p = c.parentElement;
    if (!p) return;
    const r = p.getBoundingClientRect();
    c.width = r.width * devicePixelRatio;
    c.height = r.height * devicePixelRatio;
    c.style.width = r.width + "px";
    c.style.height = r.height + "px";
    ctx.setTransform(devicePixelRatio, 0, 0, devicePixelRatio, 0, 0);
  }
  resize();
  const w = c.width / devicePixelRatio,
    h = c.height / devicePixelRatio,
    cnt = Math.min(Math.floor((w * h) / 8000), 70);
  particles = [];
  for (let i = 0; i < cnt; i++)
    particles.push({
      x: Math.random() * w,
      y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.4,
      vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.6,
      alpha: Math.random() * 0.45 + 0.12,
      hue: 152 + Math.random() * 25,
    });
  let lastT = performance.now();
  function tick(t: number) {
    const dt = Math.min((t - lastT) / 16.67, 3);
    lastT = t;
    ctx.clearRect(0, 0, w, h);
    const tt = t / 1000;
    for (let si = 0; si < 3; si++) {
      ctx.beginPath();
      const sy = h * (0.22 + si * 0.28) + Math.sin(tt * 0.35 + si * 2.1) * 28;
      for (let cx = 0; cx <= w; cx += 4) {
        const cy =
          sy +
          Math.sin(cx * 0.007 + tt * 0.45 + si) * 22 +
          Math.sin(cx * 0.003 - tt * 0.25) * 14;
        if (cx === 0) ctx.moveTo(cx, cy);
        else ctx.lineTo(cx, cy);
      }
      ctx.strokeStyle =
        "rgba(52,211,153," + (0.025 + si * 0.012).toFixed(3) + ")";
      ctx.lineWidth = 1;
      ctx.stroke();
    }
    const maxD = 130;
    for (let pi = 0; pi < particles.length; pi++) {
      const p = particles[pi];
      const dx = mousePos.x - p.x,
        dy = mousePos.y - p.y,
        d = Math.sqrt(dx * dx + dy * dy);
      if (d > 0 && d < 170) {
        const f = ((170 - d) / 170) * 0.007;
        p.vx += (dx / d) * f * dt;
        p.vy += (dy / d) * f * dt;
      }
      p.x += p.vx * dt;
      p.y += p.vy * dt;
      if (p.x < 0 || p.x > w) p.vx *= -0.8;
      if (p.y < 0 || p.y > h) p.vy *= -0.8;
      p.x = Math.max(0, Math.min(w, p.x));
      p.y = Math.max(0, Math.min(h, p.y));
      p.vx *= 0.995;
      p.vy *= 0.995;
      for (let ji = pi + 1; ji < particles.length; ji++) {
        const q = particles[ji],
          ddx = p.x - q.x,
          ddy = p.y - q.y,
          dd = ddx * ddx + ddy * ddy;
        if (dd < maxD * maxD) {
          const dist = Math.sqrt(dd),
            la = (1 - dist / maxD) * 0.11;
          ctx.beginPath();
          ctx.moveTo(p.x, p.y);
          ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = "rgba(52,211,153," + la.toFixed(3) + ")";
          ctx.lineWidth = 0.5;
          ctx.stroke();
        }
      }
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = "hsla(" + p.hue + ",62%,58%," + p.alpha.toFixed(2) + ")";
      ctx.fill();
    }
    animId = requestAnimationFrame(tick);
  }
  animId = requestAnimationFrame(tick);
  window.addEventListener("resize", resize);
}

// ===== 迷你油价折线图 =====
function drawPriceSparkline() {
  const c = priceChartRef.value;
  if (!c) return;
  const ctx = c.getContext("2d");
  if (!ctx) return;
  const w = c.width,
    h = c.height,
    pts = [
      30, 38, 32, 45, 40, 52, 48, 58, 55, 62, 58, 68, 64, 72, 78, 74, 80, 76,
      82, 78, 84,
    ],
    minV = Math.min(...pts),
    maxV = Math.max(...pts),
    range = maxV - minV || 1;
  ctx.clearRect(0, 0, w, h);
  ctx.beginPath();
  for (let i = 0; i < pts.length; i++) {
    const px = (i / (pts.length - 1)) * (w - 10) + 5,
      py = h - 5 - ((pts[i] - minV) / range) * (h - 10);
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, px);
  }
  ctx.strokeStyle = "#34d399";
  ctx.lineWidth = 1.5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();
  ctx.lineTo(w - 5, h - 5);
  ctx.lineTo(5, h - 5);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, "rgba(52,211,153,0.2)");
  grad.addColorStop(1, "rgba(52,211,153,0)");
  ctx.fillStyle = grad;
  ctx.fill();
}

// ===== 主折线图 =====
function drawMainChart() {
  const c = chartCanvasRef.value;
  if (!c) return;
  const ctx = c.getContext("2d");
  if (!ctx) return;
  const w = 440,
    h = 170;
  const dpr = window.devicePixelRatio || 1;
  c.width = w * dpr;
  c.height = h * dpr;
  c.style.width = w + "px";
  c.style.height = h + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  const pts = [
    72, 74, 71, 76, 73, 78, 75, 80, 77, 82, 79, 84, 81, 86, 83, 88, 85, 90, 87,
    92, 89, 94, 91, 96, 93, 98, 95, 100, 97, 102,
  ];
  const minV = Math.min(...pts) - 5,
    maxV = Math.max(...pts) + 5,
    range = maxV - minV || 1;
  const padL = 38,
    padR = 12,
    padT = 16,
    padB = 20,
    cw = w - padL - padR,
    ch = h - padT - padB;
  ctx.clearRect(0, 0, w, h);
  // 网格
  ctx.strokeStyle = "rgba(255,255,255,.045)";
  ctx.lineWidth = 0.5;
  for (let g = 0; g <= 4; g++) {
    const gy = padT + ch * (g / 4);
    ctx.beginPath();
    ctx.moveTo(padL, gy);
    ctx.lineTo(w - padR, gy);
    ctx.stroke();
  }
  // Y轴
  ctx.fillStyle = "rgba(148,163,184,.28)";
  ctx.font = "10px system-ui";
  ctx.textAlign = "right";
  for (let g = 0; g <= 4; g++) {
    const val = maxV - (maxV - minV) * (g / 4);
    ctx.fillText(val.toFixed(0), padL - 6, padT + ch * (g / 4) + 3);
  }
  // 面积
  const areaGrad = ctx.createLinearGradient(0, padT, 0, h - padB);
  areaGrad.addColorStop(0, "rgba(52,211,153,0.14)");
  areaGrad.addColorStop(0.6, "rgba(52,211,153,0.04)");
  areaGrad.addColorStop(1, "rgba(52,211,153,0)");
  ctx.beginPath();
  for (let i = 0; i < pts.length; i++) {
    const px = padL + (i / (pts.length - 1)) * cw,
      py = padT + ch - ((pts[i] - minV) / range) * ch;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, px);
  }
  ctx.lineTo(padL + cw, h - padB);
  ctx.lineTo(padL, h - padB);
  ctx.closePath();
  ctx.fillStyle = areaGrad;
  ctx.fill();
  // 线条
  ctx.beginPath();
  for (let i = 0; i < pts.length; i++) {
    const px = padL + (i / (pts.length - 1)) * cw,
      py = padT + ch - ((pts[i] - minV) / range) * ch;
    if (i === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, px);
  }
  const lineGrad = ctx.createLinearGradient(padL, 0, padL + cw, 0);
  lineGrad.addColorStop(0, "rgba(52,211,153,.4)");
  lineGrad.addColorStop(0.5, "#34d399");
  lineGrad.addColorStop(1, "rgba(56,189,248,.7)");
  ctx.strokeStyle = lineGrad;
  ctx.lineWidth = 2;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();
  // 最新值点
  const lpx = padL + cw,
    lpy = padT + ch - ((pts[pts.length - 1] - minV) / range) * ch;
  ctx.beginPath();
  ctx.arc(lpx, lpy, 4, 0, Math.PI * 2);
  ctx.fillStyle = "#34d399";
  ctx.fill();
  ctx.beginPath();
  ctx.arc(lpx, lpy, 8, 0, Math.PI * 2);
  ctx.strokeStyle = "rgba(52,211,153,.25)";
  ctx.lineWidth = 1;
  ctx.stroke();
  // X轴
  ctx.fillStyle = "rgba(148,163,184,.22)";
  ctx.font = "9px system-ui";
  ctx.textAlign = "center";
  const dates = [
    "03/22",
    "03/26",
    "03/30",
    "04/03",
    "04/07",
    "04/11",
    "04/15",
    "04/19",
  ];
  dates.forEach((d, i) => {
    ctx.fillText(d, padL + (i / (dates.length - 1)) * cw, h - 4);
  });
}

// ===== 事件 =====
function onMouseMove(e: MouseEvent) {
  const c = canvasRef.value;
  if (!c) return;
  const r = c.getBoundingClientRect();
  mousePos.x = e.clientX - r.left;
  mousePos.y = e.clientY - r.top;
}
function openManual() {
  window.open("/用户手册.pdf", "_blank");
}
function onAuthSuccess() {
  router.push({ name: "Home" });
}

onMounted(() => {
  if (getToken()) {
    router.replace({ name: "Home" });
    return;
  }
  updateClock();
  clockTimer = setInterval(updateClock, 1000);
  initCanvas();
  drawPriceSparkline();
  drawMainChart();
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("resize", drawMainChart);
});
onBeforeUnmount(() => {
  clearInterval(clockTimer);
  if (animId !== null) cancelAnimationFrame(animId);
  window.removeEventListener("mousemove", onMouseMove);
  window.removeEventListener("resize", drawMainChart);
});
</script>

<style scoped>
/* ═══ 容器 & 背景 ═══ */
.landing {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #080c10;
  color: #e2e8f0;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
}
.bg-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.noise {
  position: absolute;
  inset: 0;
  opacity: 0.03;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 200px 200px;
}
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(120px);
  opacity: 0.3;
}
.glow--1 {
  width: 550px;
  height: 550px;
  top: -180px;
  right: 8%;
  background: radial-gradient(circle, rgba(16, 120, 90, 0.4), transparent 70%);
  animation: g1 22s ease-in-out infinite alternate;
}
.glow--2 {
  width: 450px;
  height: 450px;
  bottom: -120px;
  left: 28%;
  background: radial-gradient(circle, rgba(14, 100, 110, 0.3), transparent 70%);
  animation: g2 26s ease-in-out infinite alternate;
}
@keyframes g1 {
  to {
    transform: translate(-30px, 24px);
  }
}
@keyframes g2 {
  to {
    transform: translate(40px, -16px);
  }
}

/* ═══ 主布局 ═══ */
.main-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: minmax(0, 46%) minmax(0, 54%);
  min-height: 100vh;
  max-width: 1560px;
  margin: 0 auto;
}

/* ═══ 左侧品牌列 ═══ */
.brand-col {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 44px 36px 44px 60px;
}

.top-mark {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
  animation: fsl 0.5s ease both;
}
.mark-line {
  display: block;
  width: 24px;
  height: 2px;
  background: #34d399;
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.5);
}
.mark-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 3px;
  color: rgba(52, 211, 153, 0.65);
  text-transform: uppercase;
}
.hero-title {
  margin: 0 0 14px;
  animation: fsl 0.5s ease 0.08s both;
}
.title-line {
  display: block;
  font-family:
    -apple-system, BlinkMacSystemFont, "PingFang SC", "Noto Sans SC", system-ui,
    sans-serif;
  font-size: clamp(32px, 4.2vw, 48px);
  font-weight: 800;
  letter-spacing: 3px;
  line-height: 1.15;
  color: #f1f5f9;
}
.hero-desc {
  margin: 0 0 28px;
  font-size: 13.5px;
  line-height: 1.7;
  color: rgba(148, 163, 184, 0.55);
  max-width: 360px;
  animation: fsl 0.5s ease 0.16s both;
}

.feat-list {
  list-style: none;
  margin: 0 0 28px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.feat-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 11px 15px;
  border-radius: 10px;
  border: 1px solid transparent;
  background: transparent;
  transition: all 0.2s ease;
  cursor: default;
  opacity: 0;
  animation: fsu 0.45s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.feat-item:hover {
  border-color: rgba(255, 255, 255, 0.06);
  background: rgba(52, 211, 153, 0.03);
  transform: translateX(4px);
}
.feat--1 {
  animation-delay: 0.26s;
}
.feat--2 {
  animation-delay: 0.34s;
}
.feat--3 {
  animation-delay: 0.42s;
}
.feat--4 {
  animation-delay: 0.5s;
}
.feat-num {
  font-size: 11px;
  font-weight: 800;
  color: rgba(52, 211, 153, 0.35);
  font-variant-numeric: tabular-nums;
  min-width: 22px;
  padding-top: 2px;
}
.feat-body {
  display: flex;
  flex-direction: column;
  gap: 3px;
}
.feat-body strong {
  font-size: 13.5px;
  font-weight: 700;
  color: #e2e8f0;
  letter-spacing: 0.3px;
}
.feat-body span {
  font-size: 11.5px;
  color: rgba(148, 163, 184, 0.4);
  line-height: 1.5;
}

/* CTA */
.cta-row {
  display: flex;
  align-items: center;
  gap: 12px;
  animation: fsu 0.45s ease 0.58s both;
}
.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 7px;
  padding: 13px 30px;
  border: none;
  border-radius: 8px;
  background: linear-gradient(135deg, #059669, #047857);
  color: #fff;
  font-size: 13.5px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.25s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow:
    0 2px 16px rgba(5, 150, 105, 0.35),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}
.cta-primary:hover {
  background: linear-gradient(135deg, #047857, #065f46);
  transform: translateY(-2px);
  box-shadow: 0 6px 24px rgba(5, 150, 105, 0.45);
}
.cta-primary svg {
  transition: transform 0.2s;
}
.cta-primary:hover svg {
  transform: translateX(3px);
}
.cta-secondary {
  padding: 13px 24px;
  border: 1px solid rgba(255, 255, 255, 0.09);
  border-radius: 8px;
  background: transparent;
  color: rgba(148, 163, 184, 0.65);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  letter-spacing: 0.3px;
  transition: all 0.2s;
}
.cta-secondary:hover {
  border-color: rgba(255, 255, 255, 0.18);
  color: #cbd5e1;
  background: rgba(255, 255, 255, 0.03);
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 7px;
  padding-top: 24px;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 0.8px;
  color: rgba(148, 163, 184, 0.28);
  font-variant-numeric: tabular-nums;
  animation: fsl 0.5s ease 0.66s both;
}
.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #34d399;
  animation: pdt 2s ease-in-out infinite;
}
.divider {
  opacity: 0.25;
}
@keyframes pdt {
  0%,
  100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.4);
  }
  50% {
    opacity: 0.5;
    box-shadow: 0 0 0 4px rgba(52, 211, 153, 0);
  }
}

/* ═══ 右侧可视化区域 ═══ */
.viz-col {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px 24px;
  overflow: hidden;
  border-left: 1px solid rgba(255, 255, 255, 0.03);
  height: 100%;
}

.viz-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

/* ═══ 驾驶舱容器（Grid 网格布局）══ */
.dash-container {
  position: relative;
  z-index: 2;
  width: 100%;
  max-width: 640px;

  /* 核心：3列网格，有组织地排列 */
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto 1fr auto;
  gap: 14px;
  align-content: start;

  opacity: 0;
  animation: dashIn 0.7s cubic-bezier(0.22, 1, 0.36, 1) 0.3s forwards;
}
@keyframes dashIn {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: none; }
}

/* ====== 卡片 Grid 排布 ====== */
/* 左上：油价卡片 */
.dc-price {
  grid-column: 1;
  grid-row: 1;
}

/* 右上：新能源卡片 */
.dc-stock {
  grid-column: 2;
  grid-row: 1;
}

/* 中间左侧：主图表（跨两行）*/
.dc-chart {
  grid-column: 1 / -1;  /* 横跨两列 */
  grid-row: 2 / 4;       /* 跨两行 */
}

/* 图表右侧：AI卡片 */
.dc-ai {
  grid-column: 2;
  grid-row: 2;
}

/* 底部：债券卡片（横跨两列）*/
.dc-bond {
  grid-column: 1 / -1;  /* 横跨两列 */
  grid-row: 4;
}

/* 连接线装饰 */
.dash-connections {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

.conn-line {
  position: absolute;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(52, 211, 153, 0.3),
    transparent
  );
  box-shadow: 0 0 12px rgba(52, 211, 153, 0.4);
  animation: pulse 2s ease-in-out infinite;
}

.conn-top {
  top: 25%;
  left: 25%;
  right: 25%;
  height: 1px;
}

.conn-left {
  left: 25%;
  top: 25%;
  bottom: 25%;
  width: 1px;
}

.conn-right {
  right: 25%;
  top: 25%;
  bottom: 25%;
  width: 1px;
}

.conn-bottom {
  bottom: 25%;
  left: 25%;
  right: 25%;
  height: 1px;
}

@keyframes pulse {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.8;
  }
}

/* 响应式调整 - 卡片宽度 */
@media (max-width: 1200px) {
  .dc-chart { width: 400px; }
}

@media (max-width: 992px) {
  .dash-container { min-height: auto; }
}

/* ═══ 统一卡片样式 ═══ */
.dc-price,
.dc-stock,
.dc-bond,
.dc-ai,
.dc-chart {
  border-radius: 14px;
  background: rgba(8, 14, 20, 0.82);
  backdrop-filter: blur(20px) saturate(1.3);
  border: 1px solid rgba(255, 255, 255, 0.06);
  padding: 18px;
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.35),
    0 0 40px rgba(0, 0, 0, 0.12),
    0 0 0 1px rgba(255, 255, 255, 0.03) inset,
    0 1px 0 rgba(255, 255, 255, 0.05) inset;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;

  /* 入场动画 */
  opacity: 0;
  animation: cardUp 0.6s cubic-bezier(0.22, 1, 0.36, 1) forwards;
}

/* 角卡片高度 */
.dc-price { min-height: 150px; }
.dc-stock { min-height: 150px; }
.dc-bond { min-height: 145px; }
.dc-ai { min-height: 140px; }
.dc-chart {
  padding: 20px;
  min-height: 360px;
}

/* ====== 独立悬浮动画（固定值，避免 postcss 问题）====== */
/* 每张卡片不同振幅和周期——永远不同步 */

@keyframes float1 { /* 折线图 - 最大振幅 */
  0%,100% { transform: translate(-50%, -50%) translateY(0); }
  50% { transform: translate(-50%, -50%) translateY(-7px); }
}
@keyframes float2 { /* 油价 */
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
@keyframes float3 { /* 新能源 */
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-4px); }
}
@keyframes float4 { /* 债券 */
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-5px); }
}
@keyframes float5 { /* AI */
  0%,100% { transform: translateY(0); }
  50% { transform: translateY(-3.5px); }
}

/* 给每张卡片分配独立浮动动画 */
.dc-chart {
  animation-name: cardUp, float1;
  animation-delay: 0.25s, 2s;   /* 入场后 2s 开始浮动 */
  animation-duration: 0.6s, 4.5s;
  animation-timing-function: cubic-bezier(0.22, 1, 0.36, 1), ease-in-out;
  animation-fill-mode: forwards, both;
  animation-iteration-count: 1, infinite;
}
.dc-price {
  animation-name: cardUp, float2;
  animation-delay: 0.35s, 2.3s;
  animation-duration: 0.55s, 3.8s;
  animation-fill-mode: forwards, both;
  animation-iteration-count: 1, infinite;
}
.dc-stock {
  animation-name: cardUp, float3;
  animation-delay: 0.45s, 2.6s;
  animation-duration: 0.55s, 4.2s;
  animation-fill-mode: forwards, both;
  animation-iteration-count: 1, infinite;
}
.dc-bond {
  animation-name: cardUp, float4;
  animation-delay: 0.55s, 2.1s;
  animation-duration: 0.5s, 3.5s;
  animation-fill-mode: forwards, both;
  animation-iteration-count: 1, infinite;
}
.dc-ai {
  animation-name: cardUp, float5;
  animation-delay: 0.65s, 2.9s;
  animation-duration: 0.5s, 4.8s;
  animation-fill-mode: forwards, both;
  animation-iteration-count: 1, infinite;
}

/* ====== Hover 效果：三层递进（上浮 → 发光 → 层级提升）====== */
.dc-price:hover,
.dc-stock:hover,
.dc-bond:hover,
.dc-ai:hover {
  transform: translateY(-10px) scale(1.03);
  z-index: 10 !important;
  transition: all 0.38s cubic-bezier(0.25, 1, 0.5, 1);
  animation-play-state: paused;  /* hover 时暂停浮动 */
}

.dc-chart:hover {
  transform: translate(-50%, -52%) scale(1.02) !important;
  z-index: 10 !important;
  transition: all 0.38s cubic-bezier(0.25, 1, 0.5, 1);
  animation-play-state: paused;
}

/* 各卡片专属 hover 发光 */
.dc-price:hover {
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.5),
    0 0 60px rgba(52, 211, 153, 0.15),
    0 0 100px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(52, 211, 153, 0.2) inset;
  border-color: rgba(52, 211, 153, 0.28);
}

.dc-stock:hover {
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.5),
    0 0 60px rgba(56, 189, 248, 0.12),
    0 0 100px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(56, 189, 248, 0.18) inset;
  border-color: rgba(56, 189, 248, 0.25);
}

.dc-bond:hover {
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.5),
    0 0 60px rgba(167, 139, 250, 0.12),
    0 0 100px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(167, 139, 250, 0.18) inset;
  border-color: rgba(167, 139, 250, 0.25);
}

.dc-ai:hover {
  box-shadow:
    0 16px 48px rgba(0, 0, 0, 0.5),
    0 0 60px rgba(251, 146, 60, 0.12),
    0 0 100px rgba(0, 0, 0, 0.2),
    0 0 0 1px rgba(251, 146, 60, 0.18) inset;
  border-color: rgba(251, 146, 60, 0.25);
}

.dc-chart:hover {
  box-shadow:
    0 24px 72px rgba(0, 0, 0, 0.65),
    0 0 80px rgba(52, 211, 153, 0.28),
    0 0 120px rgba(0, 0, 0, 0.25),
    0 0 0 1px rgba(52, 211, 153, 0.35) inset;
  border-color: rgba(52, 211, 153, 0.5);
}

/* 卡片扫光效果 */
.dc-price::before,
.dc-stock::before,
.dc-bond::before,
.dc-ai::before,
.dc-chart::before {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,.05), transparent);
  transition: left 0.7s ease;
  z-index: 1;
  pointer-events: none;
}
.dc-price:hover::before,
.dc-stock:hover::before,
.dc-bond:hover::before,
.dc-ai:hover::before,
.dc-chart:hover::before {
  left: 100%;
}

@keyframes cardUp {
  from { opacity: 0; transform: translateY(18px); }
  to { opacity: 1; transform: none; }
}

/* ===== 卡片头部 ===== */
.dc-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
}
.dc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dc-dot--g {
  background: #34d399;
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.5);
}
.dc-dot--b {
  background: #38bdf8;
  box-shadow: 0 0 8px rgba(56, 189, 248, 0.5);
}
.dc-dot--p {
  background: #a78bfa;
  box-shadow: 0 0 8px rgba(167, 139, 250, 0.5);
}
.dc-dot--o {
  background: #fb923c;
  box-shadow: 0 0 8px rgba(251, 146, 60, 0.5);
}
.dc-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.36);
}
.dc-sub {
  margin-left: auto;
  font-size: 10px;
  color: rgba(148, 163, 184, 0.22);
}

/* ===== 油价卡片 ===== */
.dc-delta {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 6px;
  border: 1px solid rgba(52, 211, 153, 0.3);
  box-shadow:
    0 2px 12px rgba(52, 211, 153, 0.2),
    0 0 20px rgba(52, 211, 153, 0.1);
  animation: glow 2s ease-in-out infinite;
}
.dc-up {
  color: #34d399;
  background: rgba(52, 211, 153, 0.15);
  border-color: rgba(52, 211, 153, 0.4);
}
.dc-down {
  color: #f87171;
  background: rgba(248, 113, 113, 0.15);
  border-color: rgba(248, 113, 113, 0.4);
  box-shadow:
    0 2px 12px rgba(248, 113, 113, 0.2),
    0 0 20px rgba(248, 113, 113, 0.1);
}
.dc-price-val {
  font-size: 42px;
  font-weight: 800;
  color: #f1f5f9;
  letter-spacing: -2px;
  font-variant-numeric: tabular-nums;
  line-height: 1.1;
  margin-bottom: 10px;
  text-shadow:
    0 0 24px rgba(52, 211, 153, 0.5),
    0 0 40px rgba(52, 211, 153, 0.2);
  position: relative;
  z-index: 2;
  animation: glow 3s ease-in-out infinite;
}

@keyframes glow {
  0%,
  100% {
    text-shadow:
      0 0 24px rgba(52, 211, 153, 0.5),
      0 0 40px rgba(52, 211, 153, 0.2);
  }
  50% {
    text-shadow:
      0 0 32px rgba(52, 211, 153, 0.7),
      0 0 60px rgba(52, 211, 153, 0.3);
  }
}
.dc-spark {
  width: 100%;
  height: 42px;
  border-radius: 8px;
  display: block;
  background: rgba(52, 211, 153, 0.05);
  padding: 8px;
  box-shadow: 0 2px 8px rgba(52, 211, 153, 0.1) inset;
}

/* ===== 新能源 / 债券 数据行 ===== */
.dc-metrics {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.dcm-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid rgba(255, 255, 255, 0.08);
  transition: all 0.3s ease;
  box-shadow:
    0 4px 16px rgba(0, 0, 0, 0.2),
    0 0 20px rgba(52, 211, 153, 0.05);
}
.dcm-row:hover {
  background: rgba(255, 255, 255, 0.05);
  border-color: rgba(52, 211, 153, 0.25);
  transform: translateX(6px) translateY(-2px);
  box-shadow:
    0 6px 24px rgba(0, 0, 0, 0.3),
    0 0 30px rgba(52, 211, 153, 0.15);
}
.dcm-name {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.7);
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.1);
}
.dcm-val {
  font-size: 18px;
  font-weight: 800;
  color: #e2e8f0;
  font-variant-numeric: tabular-nums;
  letter-spacing: -0.5px;
  text-shadow: 0 0 16px rgba(52, 211, 153, 0.4);
  animation: glow 3s ease-in-out infinite;
}
.dcm-val small {
  font-size: 12px;
  font-weight: 600;
  opacity: 0.8;
  text-shadow: 0 0 12px rgba(52, 211, 153, 0.3);
}
.dcm-ch {
  font-size: 11px;
  font-weight: 700;
  margin-left: 8px;
  padding: 3px 8px;
  border-radius: 6px;
  background: rgba(52, 211, 153, 0.15);
  border: 1px solid rgba(52, 211, 153, 0.3);
  box-shadow: 0 2px 8px rgba(52, 211, 153, 0.2);
  animation: glow 2s ease-in-out infinite;
}
.dcm-up {
  color: #34d399;
}
.dcm-down {
  color: #f87171;
  background: rgba(248, 113, 113, 0.15);
  border-color: rgba(248, 113, 113, 0.3);
  box-shadow: 0 2px 8px rgba(248, 113, 113, 0.2);
}

/* ===== AI 卡片 ===== */
.ai-block {
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.ai-lbl {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.7);
  font-weight: 600;
  letter-spacing: 0.5px;
  text-shadow: 0 0 8px rgba(255, 255, 255, 0.1);
}
.ai-pct {
  font-size: 36px;
  font-weight: 800;
  color: #e2e8f0;
  letter-spacing: -1px;
  text-shadow:
    0 0 24px rgba(251, 146, 60, 0.5),
    0 0 40px rgba(251, 146, 60, 0.2);
  position: relative;
  z-index: 2;
  animation: glow-orange 3s ease-in-out infinite;
}

@keyframes glow-orange {
  0%,
  100% {
    text-shadow:
      0 0 24px rgba(251, 146, 60, 0.5),
      0 0 40px rgba(251, 146, 60, 0.2);
  }
  50% {
    text-shadow:
      0 0 32px rgba(251, 146, 60, 0.7),
      0 0 60px rgba(251, 146, 60, 0.3);
  }
}
.ai-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.08);
  border-radius: 4px;
  overflow: hidden;
  margin-top: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) inset;
  border: 1px solid rgba(251, 146, 60, 0.15);
}
.ai-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #ea580c, #fb923c, #fdba74);
  transition: width 1.6s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow: 0 0 12px rgba(251, 146, 60, 0.4);
}

/* ===== 折线图内部 ===== */
.chart-canvas {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 16px;
  background: rgba(6, 10, 14, 0.6);
  padding: 20px;
  box-shadow:
    0 6px 24px rgba(52, 211, 153, 0.15) inset,
    0 0 40px rgba(52, 211, 153, 0.1);
  border: 1px solid rgba(52, 211, 153, 0.2);
  animation: glow 3s ease-in-out infinite;
}

/* 主图表卡片特殊效果 */
.dc-chart {
  box-shadow:
    0 16px 56px rgba(0, 0, 0, 0.5),
    0 0 64px rgba(52, 211, 153, 0.18),
    0 0 0 1px rgba(52, 211, 153, 0.2) inset;
  border-color: rgba(52, 211, 153, 0.3);
}

/* ===== 装饰边框角标 ===== */
.frame-tl,
.frame-tr,
.frame-bl,
.frame-br {
  position: absolute;
  width: 20px;
  height: 20px;
  z-index: 3;
  pointer-events: none;
}
.frame-tl {
  top: 18px;
  left: 18px;
  border-top: 1px solid rgba(52, 211, 153, 0.12);
  border-left: 1px solid rgba(52, 211, 153, 0.12);
}
.frame-tr {
  top: 18px;
  right: 18px;
  border-top: 1px solid rgba(52, 211, 153, 0.12);
  border-right: 1px solid rgba(52, 211, 153, 0.12);
}
.frame-bl {
  bottom: 18px;
  left: 18px;
  border-bottom: 1px solid rgba(52, 211, 153, 0.12);
  border-left: 1px solid rgba(52, 211, 153, 0.12);
}
.frame-br {
  bottom: 18px;
  right: 18px;
  border-bottom: 1px solid rgba(52, 211, 153, 0.12);
  border-right: 1px solid rgba(52, 211, 153, 0.12);
}

/* LIVE 标签 */
.live-tag {
  position: absolute;
  top: 18px;
  right: 26px;
  z-index: 4;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  color: rgba(52, 211, 153, 0.32);
  text-transform: uppercase;
  animation: fsl 0.6s ease 0.4s both;
}
.lt-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #34d399;
  animation: pdt 2s ease-in-out infinite;
  box-shadow: 0 0 6px rgba(52, 211, 153, 0.5);
}

/* 动画基础 */
@keyframes fsl {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@keyframes fsu {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* ═══ 响应式 ═══ */
@media (max-width: 1024px) {
  .main-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }
  .brand-col {
    padding: 32px 24px 24px;
  }
  .viz-col {
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.03);
    min-height: 420px;
    align-content: flex-start;
    padding: 20px 16px;
  }
  .dash-container {
    width: 96%;
    max-width: none;
    min-height: auto;
  }
  .dc-price,
  .dc-stock,
  .dc-bond,
  .dc-ai {
    position: relative !important;
    top: auto !important; left: auto !important; bottom: auto !important; right: auto !important;
    width: calc(50% - 8px);
  }
  .dc-chart {
    position: relative !important;
    top: auto !important; left: auto !important;
    transform: none !important;
    width: 100% !important;
    max-width: none;
    order: -1;
    margin-bottom: 10px;
  }
  .live-tag {
    display: none;
  }
  .frame-tl,
  .frame-tr,
  .frame-bl,
  .frame-br {
    display: none;
  }
}
@media (max-width: 640px) {
  .brand-col {
    padding: 24px 16px 20px;
  }
  .title-line {
    letter-spacing: 2px;
  }
  .cta-row {
    flex-direction: column;
  }
  .viz-col {
    display: none;
  }
}
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}
</style>
