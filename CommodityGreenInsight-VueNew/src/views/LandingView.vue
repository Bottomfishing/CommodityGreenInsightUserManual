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
      <!-- ══ 左侧品牌区 ═══ -->
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
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
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

      <!-- ══ 右侧：悬浮数据驾驶舱 ═══ -->
      <aside class="viz-col">
        <!-- Canvas 粒子底层 -->
        <canvas ref="canvasRef" class="viz-canvas" aria-hidden="true"></canvas>

        <!-- 悬浮卡片（绝对定位，以 viz-col 为参考系）-->
        <div class="dc dc--price">
          <div class="dc-head">
            <span class="dc-dot dc-dot--g"></span>
            <span class="dc-label">OIL PRICE</span>
            <span class="dc-badge dc-badge--up">+2.34%</span>
          </div>
          <div class="dc-price-val">$78.42</div>
          <canvas ref="priceChartRef" class="dc-spark" width="160" height="36" aria-hidden="true"></canvas>
        </div>

        <div class="dc dc--stock">
          <div class="dc-head">
            <span class="dc-dot dc-dot--b"></span>
            <span class="dc-label">NEW ENERGY</span>
          </div>
          <div class="dc-metrics">
            <div class="dcm-row">
              <span class="dcm-name">CSI新能源</span
              ><span class="dcm-val">3,847 <small class="dcm-ch dcm-up">+1.82%</small></span>
            </div>
            <div class="dcm-row">
              <span class="dcm-name">光伏产业</span
              ><span class="dcm-val">4,126 <small class="dcm-ch dcm-up">+0.95%</small></span>
            </div>
          </div>
        </div>

        <div class="dc dc--bond">
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

        <div class="dc dc--ai">
          <div class="dc-head">
            <span class="dc-dot dc-dot--o"></span>
            <span class="dc-label">AI MODEL</span>
          </div>
          <div class="ai-block">
            <span class="ai-lbl">预测准确率</span>
            <span class="ai-pct">94.7%</span>
            <div class="ai-bar"><div class="ai-fill" style="width: 94.7%"></div></div>
          </div>
        </div>

        <!-- 主图表（居中主角）-->
        <div class="dc dc--chart">
          <div class="dc-head dc-head--chart">
            <div class="chart-title-row">
              <span class="dc-dot dc-dot--g"></span>
              <span class="dc-label">PRICE FORECAST</span>
              <span class="chart-tag chart-tag--gru">GRU MODEL</span>
            </div>
            <div class="chart-sub-row">
              <span class="dc-sub">Brent Crude · 30-Day Simulation</span>
              <span class="chart-acc">Accuracy <strong>94.7%</strong></span>
            </div>
          </div>
          <canvas ref="chartCanvasRef" class="chart-canvas" width="460" height="200" aria-hidden="true"></canvas>
        </div>

        <!-- 装饰 -->
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
interface Particle { x: number; y: number; vx: number; vy: number; r: number; alpha: number; hue: number; }
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
      x: Math.random() * w, y: Math.random() * h,
      vx: (Math.random() - 0.5) * 0.4, vy: (Math.random() - 0.5) * 0.4,
      r: Math.random() * 1.8 + 0.6, alpha: Math.random() * 0.45 + 0.12,
      hue: 152 + Math.random() * 25,
    });
  let lastT = performance.now();
  function tick(t: number) {
    const dt = Math.min((t - lastT) / 16.67, 3); lastT = t;
    ctx.clearRect(0, 0, w, h);
    const tt = t / 1000;
    for (let si = 0; si < 3; si++) {
      ctx.beginPath();
      const sy = h * (0.22 + si * 0.28) + Math.sin(tt * 0.35 + si * 2.1) * 28;
      for (let cx = 0; cx <= w; cx += 4) {
        const cy = sy + Math.sin(cx * 0.007 + tt * 0.45 + si) * 22 + Math.sin(cx * 0.003 - tt * 0.25) * 14;
        if (cx === 0) ctx.moveTo(cx, cy); else ctx.lineTo(cx, cy);
      }
      ctx.strokeStyle = "rgba(52,211,153," + (0.025 + si * 0.012).toFixed(3) + ")";
      ctx.lineWidth = 1; ctx.stroke();
    }
    const maxD = 130;
    for (let pi = 0; pi < particles.length; pi++) {
      const p = particles[pi];
      const dx = mousePos.x - p.x, dy = mousePos.y - p.y, d = Math.sqrt(dx * dx + dy * dy);
      if (d > 0 && d < 170) { const f = ((170 - d) / 170) * 0.007; p.vx += (dx / d) * f * dt; p.vy += (dy / d) * f * dt; }
      p.x += p.vx * dt; p.y += p.vy * dt;
      if (p.x < 0 || p.x > w) p.vx *= -0.8; if (p.y < 0 || p.y > h) p.vy *= -0.8;
      p.x = Math.max(0, Math.min(w, p.x)); p.y = Math.max(0, Math.min(h, p.y));
      p.vx *= 0.995; p.vy *= 0.995;
      for (let ji = pi + 1; ji < particles.length; ji++) {
        const q = particles[ji], ddx = p.x - q.x, ddy = p.y - q.y, dd = ddx * ddx + ddy * ddy;
        if (dd < maxD * maxD) { const dist = Math.sqrt(dd), la = (1 - dist / maxD) * 0.11;
          ctx.beginPath(); ctx.moveTo(p.x, p.y); ctx.lineTo(q.x, q.y);
          ctx.strokeStyle = "rgba(52,211,153," + la.toFixed(3) + ")"; ctx.lineWidth = 0.5; ctx.stroke();
        }
      }
      ctx.beginPath(); ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = "hsla(" + p.hue + ",62%,58%," + p.alpha.toFixed(2) + ")"; ctx.fill();
    }
    animId = requestAnimationFrame(tick);
  }
  animId = requestAnimationFrame(tick);
  window.addEventListener("resize", resize);
}

// ===== 迷你油价折线图 =====
function drawPriceSparkline() {
  const c = priceChartRef.value; if (!c) return;
  const ctx = c.getContext("2d"); if (!ctx) return;
  const w = c.width, h = c.height,
    pts = [30,38,32,45,40,52,48,58,55,62,58,68,64,72,78,74,80,76,82,78,84],
    minV = Math.min(...pts), maxV = Math.max(...pts), range = maxV - minV || 1;
  ctx.clearRect(0, 0, w, h);
  ctx.beginPath();
  for (let i = 0; i < pts.length; i++) {
    const px = (i / (pts.length - 1)) * (w - 10) + 5, py = h - 5 - ((pts[i] - minV) / range) * (h - 10);
    if (i === 0) ctx.moveTo(px, py); else ctx.lineTo(px, py);
  }
  ctx.strokeStyle = "#34d399"; ctx.lineWidth = 1.5; ctx.lineCap = "round"; ctx.lineJoin = "round"; ctx.stroke();
  ctx.lineTo(w - 5, h - 5); ctx.lineTo(5, h - 5); ctx.closePath();
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, "rgba(52,211,153,0.2)"); grad.addColorStop(1, "rgba(52,211,153,0)");
  ctx.fillStyle = grad; ctx.fill();
}

// ===== 主折线图 — 双色渐变平滑曲线 + 发光拖尾 + 动态绘制 =====
let chartAnimId: number | null = null;
let chartProgress = 0; // 0~1 绘制进度

function drawMainChart() {
  const c = chartCanvasRef.value;
  if (!c) return;
  const ctx = c.getContext("2d");
  if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const w = 460, h = 200;
  c.width = w * dpr;
  c.height = h * dpr;
  c.style.width = w + "px";
  c.style.height = h + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  // 更有波动感的数据
  const pts = [68,72,69,78,74,82,79,88,84,92,87,96,91,102,97,108,103,114,109,118,113,122,117,128,123,132,127,138,133,142];
  const minV = Math.min(...pts) - 8, maxV = Math.max(...pts) + 8, range = maxV - minV || 1;

  const padL = 44, padR = 16, padT = 24, padB = 28;
  const cw = w - padL - padR, ch = h - padT - padB;

  ctx.clearRect(0, 0, w, h);

  // ── 贝塞尔平滑曲线控制点计算 ──
  const ptsXY: {x:number,y:number}[] = [];
  for (let i = 0; i < pts.length; i++) {
    ptsXY.push({
      x: padL + (i / (pts.length - 1)) * cw,
      y: padT + ch - ((pts[i] - minV / 1.1) / range) * ch
    });
  }

  // Catmull-Rom → Cubic Bezier 转换
  function getControlPoints(p0:{x:number;y:number}, p1:{x:number;y:number}, p2:{x:number;y:number}, p3:{x:number;y:number}) {
    const t = 0.3;
    return {
      cp1x: p1.x + (p2.x - p0.x) * t,
      cp1y: p1.y + (p2.y - p0.y) * t,
      cp2x: p2.x - (p3.x - p1.x) * t,
      cp2y: p2.y - (p3.y - p1.y) * t,
    };
  }

  // ── 淡化水平参考线（仅3条）──
  ctx.strokeStyle = "rgba(255,255,255,.032)";
  ctx.lineWidth = 0.5;
  for (let g = 1; g <= 3; g++) {
    const gy = padT + ch * (g / 4);
    ctx.beginPath();
    ctx.moveTo(padL, gy);
    ctx.lineTo(w - padR, gy);
    ctx.stroke();
  }

  // ── Y轴标签（极淡）──
  ctx.fillStyle = "rgba(148,163,184,.18)";
  ctx.font = "9px system-ui";
  ctx.textAlign = "right";
  ["$140", "$105", "$70", "$35", "$0"].forEach((lbl, i) => {
    ctx.fillText(lbl, padL - 6, padT + ch * (i / 4) + 3);
  });

  // ── X轴日期标签（极淡）──
  ctx.fillStyle = "rgba(148,163,184,.14)";
  ctx.font = "9px system-ui";
  ctx.textAlign = "center";
  ["03/22", "03/26", "03/30", "04/03", "04/07", "04/11", "04/15", "04/19"].forEach((d, i) => {
    ctx.fillText(d, padL + (i / 7) * cw, h - 6);
  });

  // ── 计算要绘制的点数（动画进度）──
  const totalPts = ptsXY.length;
  const drawCount = Math.floor(chartProgress * totalPts);
  if (drawCount < 2) return; // 至少需要2个点才能画线

  // ── 面积填充（渐变）──
  const areaGrad = ctx.createLinearGradient(0, padT, 0, h - padB);
  areaGrad.addColorStop(0, "rgba(52,211,153,0.12)");
  areaGrad.addColorStop(0.5, "rgba(56,189,248,0.05)");
  areaGrad.addColorStop(1, "rgba(52,211,153,0)");

  ctx.beginPath();
  ctx.moveTo(ptsXY[0].x, h - padB);
  ctx.lineTo(ptsXY[0].x, ptsXY[0].y);

  for (let i = 0; i < drawCount - 1; i++) {
    const p0 = ptsXY[Math.max(0, i - 1)];
    const p1 = ptsXY[i];
    const p2 = ptsXY[i + 1];
    const p3 = ptsXY[Math.min(totalPts - 1, i + 2)];
    const cp = getControlPoints(p0, p1, p2, p3);
    ctx.bezierCurveTo(cp.cp1x, cp.cp1y, cp.cp2x, cp.cp2y, p2.x, p2.y);
  }

  // 最后一个部分点到终点
  const lastPt = ptsXY[drawCount - 1];
  ctx.lineTo(lastPt.x, h - padB);
  ctx.closePath();
  ctx.fillStyle = areaGrad;
  ctx.fill();

  // ── 主线条：双色渐变（翠绿 → 天蓝）──
  const lineGrad = ctx.createLinearGradient(padL, 0, padL + cw, 0);
  lineGrad.addColorStop(0, "#34d399");
  lineGrad.addColorStop(0.4, "#2dd4bf");
  lineGrad.addColorStop(0.7, "#38bdf8");
  lineGrad.addColorStop(1, "#60a5fa");

  ctx.beginPath();
  ctx.moveTo(ptsXY[0].x, ptsXY[0].y);

  for (let i = 0; i < drawCount - 1; i++) {
    const p0 = ptsXY[Math.max(0, i - 1)];
    const p1 = ptsXY[i];
    const p2 = ptsXY[i + 1];
    const p3 = ptsXY[Math.min(totalPts - 1, i + 2)];
    const cp = getControlPoints(p0, p1, p2, p3);
    ctx.bezierCurveTo(cp.cp1x, cp.cp1y, cp.cp2x, cp.cp2y, p2.x, p2.y);
  }

  // 线条发光层（粗+半透明）
  ctx.save();
  ctx.strokeStyle = "rgba(52,211,153,0.18)";
  ctx.lineWidth = 7;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();
  ctx.restore();

  // 主线条
  ctx.strokeStyle = lineGrad;
  ctx.lineWidth = 2.5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();

  // ── 最新端点：脉冲圆点 + 光环扩散 ──
  if (chartProgress >= 0.98) {
    const ep = ptsXY[totalPts - 1];
    const time = Date.now() / 1000;

    // 外圈扩散光环
    const pulseR = 6 + Math.sin(time * 3) * 3;
    ctx.beginPath();
    ctx.arc(ep.x, ep.y, pulseR + 4, 0, Math.PI * 2);
    ctx.strokeStyle = `rgba(52,211,153,${0.12 + Math.sin(time * 3) * 0.08})`;
    ctx.lineWidth = 1.2;
    ctx.stroke();

    // 中圈
    ctx.beginPath();
    ctx.arc(ep.x, ep.y, pulseR, 0, Math.PI * 2);
    ctx.fillStyle = "rgba(52,211,153,0.15)";
    ctx.fill();

    // 实心圆点（渐变）
    const dotGrad = ctx.createRadialGradient(ep.x, ep.y, 0, ep.x, ep.y, 5);
    dotGrad.addColorStop(0, "#ffffff");
    dotGrad.addColorStop(0.4, "#34d399");
    dotGrad.addColorStop(1, "#38bdf8");
    ctx.beginPath();
    ctx.arc(ep.x, ep.y, 5, 0, Math.PI * 2);
    ctx.fillStyle = dotGrad;
    ctx.fill();

    // 浮动数值标签
    const labelY = ep.y - 16 - Math.sin(time * 2) * 3;
    ctx.fillStyle = "rgba(255,255,255,.85)";
    ctx.font = "bold 11px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("$" + pts[pts.length - 1].toFixed(0), ep.x, labelY);
  }

  // ── 数据高亮点（每隔几个点标记）──
  if (chartProgress >= 1) {
    const highlights = [Math.floor(totalPts * 0.15), Math.floor(totalPts * 0.45), Math.floor(totalPts * 0.75)];
    highlights.forEach((hi) => {
      if (hi < totalPts && hi > 0) {
        const hp = ptsXY[hi];
        ctx.beginPath();
        ctx.arc(hp.x, hp.y, 2.5, 0, Math.PI * 2);
        ctx.fillStyle = "rgba(56,189,248,.55)";
        ctx.fill();
        // 小十字
        ctx.strokeStyle = "rgba(56,189,248,.25)";
        ctx.lineWidth = 0.6;
        ctx.beginPath();
        ctx.moveTo(hp.x - 5, hp.y);
        ctx.lineTo(hp.x + 5, hp.y);
        ctx.moveTo(hp.x, hp.y - 5);
        ctx.lineTo(hp.x, hp.y + 5);
        ctx.stroke();
      }
    });
  }
}

// 图表绘制动画驱动
function animateChart() {
  if (chartProgress < 1) {
    chartProgress += 0.02; // 约50帧完成
    if (chartProgress > 1) chartProgress = 1;
    drawMainChart();
    chartAnimId = requestAnimationFrame(animateChart);
  } else {
    drawMainChart(); // 最终帧
    // 持续更新端点动画（脉冲效果）
    chartAnimId = requestAnimationFrame(function tick() {
      drawMainChart();
      chartAnimId = requestAnimationFrame(tick);
    });
  }
}

// ===== 事件 =====
function onMouseMove(e: MouseEvent) {
  const c = canvasRef.value; if (!c) return;
  const r = c.getBoundingClientRect(); mousePos.x = e.clientX - r.left; mousePos.y = e.clientY - r.top;
}
function openManual() { window.open("/用户手册.pdf", "_blank"); }
function onAuthSuccess() { router.push({ name: "Home" }); }

onMounted(() => {
  if (getToken()) { router.replace({ name: "Home" }); return; }
  updateClock(); clockTimer = setInterval(updateClock, 1000);
  initCanvas(); drawPriceSparkline(); animateChart();
  window.addEventListener("mousemove", onMouseMove); window.addEventListener("resize", () => { drawMainChart(); });
});
onBeforeUnmount(() => {
  clearInterval(clockTimer);
  if (animId !== null) cancelAnimationFrame(animId);
  if (chartAnimId !== null) cancelAnimationFrame(chartAnimId);
  window.removeEventListener("mousemove", onMouseMove);
  window.removeEventListener("resize", drawMainChart);
});
</script>

<style scoped>
/* ================================================================
   LANDING PAGE — 大宗绿测
   Design: Premium dark-mode data dashboard with floating cards
   Layout: Left brand (46%) | Right visualization (54%)
   ================================================================ */

/* ─── Reset & Container ─── */
.landing {
  position: relative; min-height: 100vh; overflow: hidden;
  background: #080c10; color: #e2e8f0;
  font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "PingFang SC", sans-serif;
}
.bg-layer { position: fixed; inset: 0; z-index: 0; pointer-events: none; }
.noise {
  position: absolute; inset: 0; opacity: .035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 220px 220px;
}
.glow { position: absolute; border-radius: 50%; filter: blur(130px); opacity: .28; }
.glow--1 { width: 600px; height: 600px; top: -200px; right: 5%; background: radial-gradient(circle, rgba(16,120,90,.45), transparent 70%); animation: drift1 24s ease-in-out infinite alternate; }
.glow--2 { width: 500px; height: 500px; bottom: -150px; left: 25%; background: radial-gradient(circle, rgba(14,100,110,.32), transparent 70%); animation: drift2 28s ease-in-out infinite alternate; }
@keyframes drift1 { to { transform: translate(-40px, 30px); } }
@keyframes drift2 { to { transform: translate(50px, -20px); } }

/* ─── Main Grid ─── */
.main-grid {
  position: relative; z-index: 1;
  display: grid; grid-template-columns: 42% 58%;
  min-height: 100vh; max-width: 1500px; margin: 0 auto;
}

/* ─── LEFT: Brand Column ─── */
.brand-col {
  display: flex; flex-direction: column; justify-content: center;
  padding: 48px 40px 48px 64px;
}

/* 标签行 */
.top-mark { display: flex; align-items: center; gap: 10px; margin-bottom: 22px; animation: fadeUp .5s ease both; }
.mark-line { width: 24px; height: 2px; background: #34d399; box-shadow: 0 0 10px rgba(52,211,153,.6); border-radius: 1px; }
.mark-text { font-size: 10px; font-weight: 700; letter-spacing: 3px; color: rgba(52,211,153,.6); text-transform: uppercase; }

/* 标题 */
.hero-title { margin: 0 0 14px; animation: fadeUp .5s ease .08s both; }
.title-line {
  display: block;
  font-size: clamp(34px, 4vw, 50px); font-weight: 800; letter-spacing: 4px; line-height: 1.12;
  background: linear-gradient(135deg, #f1f5f9 0%, #94a3b8 60%, #34d399 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent; background-clip: text;
}
.hero-desc { margin: 0 0 30px; font-size: 13.5px; line-height: 1.75; color: rgba(148,163,184,.5); max-width: 380px; animation: fadeUp .5s ease .16s both; }

/* 功能列表 */
.feat-list { list-style: none; margin: 0 0 32px; padding: 0; display: flex; flex-direction: column; gap: 6px; }
.feat-item {
  display: flex; align-items: center; gap: 14px; padding: 12px 16px;
  border-radius: 11px; border: 1px solid transparent; background: transparent;
  cursor: default; opacity: 0; animation: fadeUp .5s cubic-bezier(.22,1,.36,1) forwards;
  transition: all .25s ease;
}
.feat-item:hover {
  border-color: rgba(255,255,255,.06); background: rgba(52,211,153,.025);
  transform: translateX(6px);
}
.feat--1 { animation-delay: .26s; }
.feat--2 { animation-delay: .34s; }
.feat--3 { animation-delay: .42s; }
.feat--4 { animation-delay: .50s; }
.feat-num { font-size: 11px; font-weight: 800; color: rgba(52,211,153,.32); min-width: 24px; }
.feat-body { display: flex; flex-direction: column; gap: 2px; }
.feat-body strong { font-size: 13.5px; font-weight: 700; color: #e2e8f0; }
.feat-body span { font-size: 11.5px; color: rgba(148,163,184,.38); line-height: 1.5; }

/* CTA 按钮 */
.cta-row { display: flex; align-items: center; gap: 12px; animation: fadeUp .5s ease .58s both; }
.cta-primary {
  display: inline-flex; align-items: center; gap: 8px;
  padding: 14px 32px; border: none; border-radius: 10px;
  background: linear-gradient(135deg, #059669, #047857);
  color: #fff; font-size: 13.5px; font-weight: 700; letter-spacing: 1px;
  cursor: pointer; transition: all .3s cubic-bezier(.22,1,.36,1);
  box-shadow: 0 4px 20px rgba(5,150,105,.4), inset 0 1px 0 rgba(255,255,255,.15);
}
.cta-primary:hover { transform: translateY(-3px); box-shadow: 0 8px 32px rgba(5,150,105,.5); }
.cta-primary svg { transition: transform .25s; }
.cta-primary:hover svg { transform: translateX(4px); }
.cta-secondary {
  padding: 14px 26px; border: 1px solid rgba(255,255,255,.1); border-radius: 10px;
  background: transparent; color: rgba(148,163,184,.55); font-size: 13px; font-weight: 600;
  cursor: pointer; transition: all .25s;
}
.cta-secondary:hover { border-color: rgba(255,255,255,.2); color: #cbd5e1; background: rgba(255,255,255,.04); }

/* 状态栏 */
.status-bar { display: flex; align-items: center; gap: 7px; padding-top: 26px; font-size: 10px; font-weight: 500; letter-spacing: 1px; color: rgba(148,163,184,.25); animation: fadeUp .5s ease .66s both; }
.status-dot { width: 5px; height: 5px; border-radius: 50%; background: #34d399; animation: blink 2s ease-in-out infinite; }
.divider { opacity: .2; }
@keyframes blink { 0%,100%{opacity:1;box-shadow:0 0 0 0 rgba(52,211,153,.4)} 50%{opacity:.4;box-shadow:0 0 0 5px rgba(52,211,153,0)} }

@keyframes fadeUp { from{opacity:0;transform:translateY(12px)} to{opacity:1;transform:none} }


/* ══════════════════════════════════════════════════
   RIGHT: Visualization — Floating Data Cards
   ══════════════════════════════════════════════════ */

.viz-col {
  position: relative; display: flex; align-items: center; justify-content: center;
  padding: 32px 28px; overflow: hidden;
  border-left: 1px solid rgba(255,255,255,.025); height: 100%;
  perspective: 1200px; /* 为子卡片提供 3D 透视空间 */
}
.viz-canvas { position: absolute; inset: 0; width: 100%; height: 100%; z-index: 0; }


/* ─── 统一卡片基础样式 ─── */
.dc {
  position: absolute;
  border-radius: 16px;
  background: rgba(6, 12, 18, 0.78);
  backdrop-filter: blur(24px) saturate(1.4);
  border: 1px solid rgba(255, 255, 255, 0.06);

  /* 多层阴影营造深度感 */
  box-shadow:
    0 4px 24px rgba(0, 0, 0, 0.38),
    0 0 0 1px rgba(255, 255, 255, 0.02) inset,
    0 1px 0 rgba(255, 255, 255, 0.04) inset;

  padding: 18px;
  display: flex; flex-direction: column;
  overflow: hidden;

  /* 入场动画：从下方淡入 + 微缩放 */
  opacity: 0;
  animation: cardEnter .65s cubic-bezier(.22, 1, .36, 1) forwards;

  transition:
    transform .4s cubic-bezier(.22, 1, .36, 1),
    box-shadow .4s cubic-bezier(.22, 1, .36, 1),
    border-color .4s ease;
}
@keyframes cardEnter {
  from { opacity: 0; transform: translateY(24px) scale(.96); }
  to { opacity: 1; transform: none; }
}


/* ═══ 卡片位置排布（以 viz-col 为坐标系）══ */

/*
  布局思路：
  - 图表是主角，居中偏上，最大尺寸，最高层级
  - 四张小卡片围绕图表分布，像卫星一样
  - 用百分比定位确保不同屏幕下相对位置稳定
  - 每张卡片略有不同的尺寸和透明度，形成层次
*/

/* ★★★ 主角：折线图 — 真正居中，最大，最高 z-index */
.dc--chart {
  top: 22%;
  left: 50%;
  transform: translateX(-50%);
  width: 500px;
  max-width: 74%;
  padding: 20px 22px;
  min-height: 310px;

  /* 无边框设计 — 靠内容本身发光 */
  border-color: transparent;
  background: rgba(6, 12, 18, 0.55);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 120px rgba(52, 211, 153, 0.05),
    0 0 60px rgba(56, 189, 248, 0.03);

  z-index: 5;           /* 最高层 */
  animation-delay: .2s;
}
.dc--chart:hover {
  transform: translateX(-50%) translateY(-8px) scale(1.015);
  box-shadow:
    0 32px 90px rgba(0, 0, 0, 0.6),
    0 0 140px rgba(52, 211, 153, 0.12),
    0 0 80px rgba(56, 189, 248, 0.08);
}


/* ★★☆ 卫星 1：油价 — 左上 */
.dc--price {
  top: 8%; left: 6%;
  width: 210px;
  border-color: rgba(52, 211, 153, 0.08);
  z-index: 4;
  animation-delay: .35s;
}
.dc--price:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 20px 56px rgba(0,0,0,.5), 0 0 70px rgba(52,211,153,.16), 0 0 0 1px rgba(52,211,153,.22) inset;
  border-color: rgba(52, 211, 153, 0.32);
}


/* ★★☆ 卫星 2：新能源 — 右上 */
.dc--stock {
  top: 5%; right: 4%;
  width: 205px;
  border-color: rgba(56, 189, 248, 0.07);
  z-index: 3;
  animation-delay: .45s;
}
.dc--stock:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 20px 56px rgba(0,0,0,.5), 0 0 70px rgba(56,189,248,.14), 0 0 0 1px rgba(56,189,248,.2) inset;
  border-color: rgba(56, 189, 248, 0.3);
}


/* ★☆☆ 卫星 3：债券 — 左下 */
.dc--bond {
  bottom: 12%; left: 8%;
  width: 215px;
  border-color: rgba(167, 139, 250, 0.07);
  z-index: 2;
  animation-delay: .55s;
}
.dc--bond:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 20px 56px rgba(0,0,0,.5), 0 0 70px rgba(167,139,250,.14), 0 0 0 1px rgba(167,139,250,.2) inset;
  border-color: rgba(167, 139, 250, 0.3);
}


/* ★☆☆ 卫星 4：AI模型 — 右下 */
.dc--ai {
  bottom: 16%; right: 6%;
  width: 195px;
  border-color: rgba(251, 146, 60, 0.07);
  z-index: 2;
  animation-delay: .65s;
}
.dc--ai:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow: 0 20px 56px rgba(0,0,0,.5), 0 0 70px rgba(251,146,60,.14), 0 0 0 1px rgba(251,146,60,.2) inset;
  border-color: rgba(251, 146, 60, 0.3);
}


/* ═══ 持续呼吸微动效（独立固定值 Keyframe，避免 postcss 问题）══ */

@keyframes breatheChart {
  0%,100% { box-shadow: 0 20px 60px rgba(0,0,0,.5), 0 0 120px rgba(52,211,153,.05), 0 0 60px rgba(56,189,248,.03); }
  50%      { box-shadow: 0 24px 70px rgba(0,0,0,.54), 0 0 150px rgba(52,211,153,.09), 0 0 80px rgba(56,189,248,.06); }
}
@keyframes breathePrice {
  0%,100% { box-shadow: 0 4px 24px rgba(0,0,0,.38), 0 0 0 1px rgba(255,255,255,.02) inset; }
  50%      { box-shadow: 0 6px 28px rgba(0,0,0,.42), 0 0 44px rgba(52,211,153,.09); border-color: rgba(52,211,153,.12); }
}
@keyframes breatheStock {
  0%,100% { box-shadow: 0 4px 24px rgba(0,0,0,.38), 0 0 0 1px rgba(255,255,255,.02) inset; }
  50%      { box-shadow: 0 6px 28px rgba(0,0,0,.42), 0 0 44px rgba(56,189,248,.08); border-color: rgba(56,189,248,.10); }
}
@keyframes breatheBond {
  0%,100% { box-shadow: 0 4px 24px rgba(0,0,0,.38); }
  50%      { box-shadow: 0 5px 26px rgba(0,0,0,.42), 0 0 42px rgba(167,139,250,.07); border-color: rgba(167,139,250,.10); }
}
@keyframes breatheAi {
  0%,100% { box-shadow: 0 4px 24px rgba(0,0,0,.38), 0 0 0 1px rgba(255,255,255,.02) inset; }
  50%      { box-shadow: 0 6px 28px rgba(0,0,0,.42), 0 0 44px rgba(251,146,60,.08); border-color: rgba(251,146,60,.10); }
}

/* 分配给各卡片的复合动画：入场(一次) + 呼吸(循环) */
.dc--chart  { animation: cardEnter .65s ease .2s forwards, breatheChart 5s ease-in-out 2.5s infinite; }
.dc--price  { animation: cardEnter .6s ease .35s forwards, breathePrice 4.2s ease-in-out 2.2s infinite; }
.dc--stock  { animation: cardEnter .6s ease .45s forwards, breatheStock 4.8s ease-in-out 2.6s infinite; }
.dc--bond   { animation: cardEnter .55s ease .55s forwards, breatheBond 3.8s ease-in-out 2.1s infinite; }
.dc--ai     { animation: cardEnter .55s ease .65s forwards, breatheAi 5.2s ease-in-out 2.9s infinite; }

/* hover 时暂停呼吸动画 */
.dc:hover { animation-play-state: paused; }


/* ═══ 扫光效果（hover 时从左到右扫过）══ */
.dc::after {
  content: "";
  position: absolute; top: 0; left: -100%;
  width: 100%; height: 100%;
  background: linear-gradient(90deg, transparent 0%, rgba(255,255,255,.06) 45%, transparent 100%);
  transition: left .7s ease;
  z-index: 1; pointer-events: none; border-radius: inherit;
}
.dc:hover::after { left: 100%; }


/* ─── 卡片内部组件 ─── */

/* 头部 */
.dc-head { display: flex; align-items: center; gap: 8px; margin-bottom: 12px; }
.dc-dot { width: 6px; height: 6px; border-radius: 50%; flex-shrink: 0; }
.dc-dot--g { background: #34d399; box-shadow: 0 0 10px rgba(52,211,153,.7); }
.dc-dot--b { background: #38bdf8; box-shadow: 0 0 10px rgba(56,189,248,.7); }
.dc-dot--p { background: #a78bfa; box-shadow: 0 0 10px rgba(167,139,250,.7); }
.dc-dot--o { background: #fb923c; box-shadow: 0 0 10px rgba(251,146,60,.7); }
.dc-label { font-size: 9px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; color: rgba(148,163,184,.32); }
.dc-sub { margin-left: auto; font-size: 10px; color: rgba(148,163,184,.2); }

/* 油价数值 */
.dc-badge {
  margin-left: auto; font-size: 11px; font-weight: 700;
  padding: 4px 10px; border-radius: 7px;
  animation: pulseGlow 2.5s ease-in-out infinite;
}
.dc-badge--up { color: #34d399; background: rgba(52,211,153,.12); border: 1px solid rgba(52,211,153,.3); box-shadow: 0 0 14px rgba(52,211,153,.15); }
@keyframes pulseGlow { 0%,100%{box-shadow:0 0 14px rgba(52,211,153,.15)} 50%{box-shadow:0 0 22px rgba(52,211,153,.3)} }

.dc-price-val {
  font-size: 40px; font-weight: 800; letter-spacing: -2px;
  color: #f1f5f9; line-height: 1.1; margin-bottom: 8px;
  text-shadow: 0 0 28px rgba(52,211,153,.45), 0 0 48px rgba(52,211,153,.18);
  animation: glowText 3.5s ease-in-out infinite;
}
@keyframes glowText {
  0%,100%{text-shadow:0 0 28px rgba(52,211,153,.45),0 0 48px rgba(52,211,153,.18)}
  50%     {text-shadow:0 0 36px rgba(52,211,153,.65),0 0 68px rgba(52,211,153,.28)}
}

.dc-spark { width: 100%; height: 40px; border-radius: 10px; display: block; background: rgba(52,211,153,.04); border: 1px solid rgba(52,211,153,.08); }

/* 数据行 */
.dc-metrics { display: flex; flex-direction: column; gap: 10px; }
.dcm-row {
  display: flex; justify-content: space-between; align-items: center;
  padding: 10px 13px; border-radius: 10px;
  background: rgba(255,255,255,.025);
  border: 1px solid rgba(255,255,255,.06);
  transition: all .3s ease;
}
.dcm-row:hover { background: rgba(255,255,255,.04); border-color: rgba(52,211,153,.2); transform: translateX(4px); }
.dcm-name { font-size: 11px; font-weight: 600; color: rgba(148,163,184,.6); letter-spacing: .3px; }
.dcm-val { font-size: 17px; font-weight: 800; color: #e2e8f0; letter-spacing: -.5px; text-shadow: 0 0 14px rgba(52,211,153,.3); }
.dcm-val small { font-size: 11.5px; font-weight: 600; opacity: .75; }
.dcm-ch { font-size: 10.5px; font-weight: 700; margin-left: 7px; padding: 3px 7px; border-radius: 6px; background: rgba(52,211,153,.14); border: 1px solid rgba(52,211,153,.28); }
.dcm-up { color: #34d399; }

/* AI 卡片 */
.ai-block { display: flex; flex-direction: column; gap: 10px; }
.ai-lbl { font-size: 11px; font-weight: 600; color: rgba(148,163,184,.6); letter-spacing: .5px; }
.ai-pct {
  font-size: 34px; font-weight: 800; letter-spacing: -1px; color: #e2e8f0;
  text-shadow: 0 0 24px rgba(251,146,60,.5), 0 0 44px rgba(251,146,60,.2);
  animation: glowOrange 3.5s ease-in-out infinite;
}
@keyframes glowOrange {
  0%,100%{text-shadow:0 0 24px rgba(251,146,60,.5),0 0 44px rgba(251,146,60,.2)}
  50%     {text-shadow:0 0 32px rgba(251,146,60,.7),0 0 64px rgba(251,146,60,.3)}
}
.ai-bar { height: 8px; background: rgba(255,255,255,.07); border-radius: 4px; overflow: hidden; border: 1px solid rgba(251,146,60,.12); box-shadow: 0 2px 8px rgba(0,0,0,.2) inset; }
.ai-fill { height: 100%; border-radius: 4px; background: linear-gradient(90deg, #ea580c, #fb923c, #fdba74); box-shadow: 0 0 14px rgba(251,146,60,.4); }

/* 图表 Canvas — 无边框，纯内容 */
.chart-canvas {
  display: block;
  width: 100%;
  height: auto;
  border-radius: 10px;
  background: transparent;
}

/* LIVE 标签 */
.live-tag {
  position: absolute; top: 20px; right: 28px; z-index: 6;
  display: flex; align-items: center; gap: 6px;
  font-size: 9px; font-weight: 700; letter-spacing: 2px;
  color: rgba(52,211,153,.35); text-transform: uppercase;
  animation: fadeUp .6s ease .5s both;
}
.lt-dot { width: 5px; height: 5px; border-radius: 50%; background: #34d399; animation: blink 2s ease-in-out infinite; box-shadow: 0 0 8px rgba(52,211,153,.6); }


/* ═══ 响应式 ═══ */
@media (max-width: 1280px) {
  .dc--chart { width: 420px; }
  .dc--price, .dc--stock { width: 190px; }
  .dc--bond, .dc--ai { width: 185px; }
}
@media (max-width: 1024px) {
  .main-grid { grid-template-columns: 1fr; grid-template-rows: auto auto; }
  .brand-col { padding: 36px 28px 32px; }
  .viz-col {
    border-left: none; border-top: 1px solid rgba(255,255,255,.025);
    min-height: 500px; padding: 24px 16px;
  }
  /* 小屏：取消绝对定位，改为流式布局 */
  .dc {
    position: relative !important;
    top: auto !important; left: auto !important; right: auto !important; bottom: auto !important;
    transform: none !important;
    width: 100% !important; max-width: 480px; margin: 0 auto 12px;
    animation: fadeUp .5s ease forwards !important;
  }
  .dc--chart { order: -1; margin-bottom: 16px; }
  .live-tag { display: none; }
}
@media (max-width: 640px) {
  .brand-col { padding: 24px 16px 20px; }
  .title-line { letter-spacing: 2px; }
  .cta-row { flex-direction: column; }
  .dc { max-width: 100% !important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after { animation-duration: .001ms !important; transition-duration: .001ms !important; }
}
</style>
