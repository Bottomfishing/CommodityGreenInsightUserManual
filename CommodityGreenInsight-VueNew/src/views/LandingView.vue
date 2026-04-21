<template>
  <div class="landing">
    <!-- 登录弹框 -->
    <AuthModal
      :visible="showAuth"
      @update:visible="showAuth = $event"
      @success="onAuthSuccess"
    />

    <!-- 背景 — 多层光晕 -->
    <div class="bg-layer" aria-hidden="true">
      <div class="noise"></div>
      <div class="glow glow--1"></div>
      <div class="glow glow--2"></div>
      <div class="glow glow--3"></div>
      <div class="glow glow--4"></div>
      <div class="glow glow--5"></div>
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

      <!-- ══ 右侧：3D 数据展示 ═══ -->
      <aside class="viz-col">

        <!-- Spotlight 光效层 -->
        <div class="spotlight-layer"></div>
        <div class="spotlight-layer spotlight-layer--2"></div>

        <!-- Bento Grid 3D 卡片容器 -->
        <div class="bento-grid">

          <!-- ★★★ 核心大卡 — 油价预测（占据主要视觉区域）-->
          <div class="bento-card bento-card--hero" @mousemove="onHeroTilt" @mouseleave="onHeroLeave" :style="heroStyle">
            <div class="hero-inner">
              <div class="hero-header">
                <span class="hero-tag hero-tag--gru">GRU MODEL</span>
                <span class="hero-meta">Brent Crude · Forecast</span>
              </div>
              <canvas ref="chartCanvasRef" class="hero-chart" width="400" height="200" aria-hidden="true"></canvas>
              <div class="hero-footer">
                <span class="hero-acc">Accuracy <strong>94.7%</strong></span>
                <span class="hero-live"><i class="live-pulse"></i> LIVE</span>
              </div>
            </div>
            <!-- 边缘光 -->
            <div class="hero-glow"></div>
            <div class="bc-shine"></div>
          </div>

          <!-- 油价实时卡 -->
          <div class="bento-card bento-card--price" @mousemove="(e) => onCardTilt(e, 'price')" @mouseleave="() => onCardLeave('price')" :style="cardStyles.price">
            <div class="bc-content">
              <span class="bc-icon bc-icon--oil"></span>
              <span class="bc-label">Oil Price</span>
              <span class="bc-value">$78.42</span>
              <span class="bc-delta bc-up">+2.34%</span>
              <canvas ref="priceChartRef" class="bc-spark" width="120" height="28" aria-hidden="true"></canvas>
            </div>
            <div class="bc-shine"></div>
          </div>

          <!-- 新能源股票卡 -->
          <div class="bento-card bento-card--stock" @mousemove="(e) => onCardTilt(e, 'stock')" @mouseleave="() => onCardLeave('stock')" :style="cardStyles.stock">
            <div class="bc-content">
              <span class="bc-icon bc-icon--bolt"></span>
              <span class="bc-label">New Energy</span>
              <div class="bc-list">
                <div class="bc-item">
                  <span>CSI新能源</span><em>3,847</em><small class="bc-up">+1.82%</small>
                </div>
                <div class="bc-item">
                  <span>光伏产业</span><em>4,126</em><small class="bc-up">+0.95%</small>
                </div>
              </div>
            </div>
            <div class="bc-shine"></div>
          </div>

          <!-- 债券/利率卡 -->
          <div class="bento-card bento-card--bond" @mousemove="(e) => onCardTilt(e, 'bond')" @mouseleave="() => onCardLeave('bond')" :style="cardStyles.bond">
            <div class="bc-content">
              <span class="bc-icon bc-icon--rate"></span>
              <span class="bc-label">Bond / Rate</span>
              <div class="bc-list">
                <div class="bc-item"><span>10Y国债</span><em>2.34%</em></div>
                <div class="bc-item"><span>SHIBOR</span><em>1.68%</em></div>
              </div>
            </div>
            <div class="bc-shine"></div>
          </div>

        </div>
      </aside>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import AuthModal from "@/components/AuthModal.vue";
import { getToken } from "@/api/auth";

const router = useRouter();
const showAuth = ref(false);
const priceChartRef = ref<HTMLCanvasElement | null>(null);
const chartCanvasRef = ref<HTMLCanvasElement | null>(null);
const currentTime = ref("");

// ===== 3D 卡片倾斜交互 =====
const heroStyle = ref<Record<string, string>>({});
const cardStyles = reactive({
  price: <Record<string, string>>{},
  stock: <Record<string, string>>{},
  bond: <Record<string, string>>{},
});

function onHeroTilt(e: MouseEvent) {
  const el = (e.currentTarget as HTMLElement);
  const r = el.getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  const cx = r.width / 2, cy = r.height / 2;
  const rx = ((y - cy) / cy) * -8;
  const ry = ((x - cx) / cx) * 8;
  heroStyle.value = {
    transform: `perspective(1000px) rotateX(${rx}deg) rotateY(${ry}deg) scale3d(1.02,1.02,1.02)`,
  };
}
function onHeroLeave() { heroStyle.value = { transition: "transform .5s ease", transform: "perspective(1000px) rotateX(0) rotateY(0)" }; }

function onCardTilt(e: MouseEvent, key: "price" | "stock" | "bond") {
  const el = (e.currentTarget as HTMLElement);
  const r = el.getBoundingClientRect();
  const x = e.clientX - r.left, y = e.clientY - r.top;
  const cx = r.width / 2, cy = r.height / 2;
  const rx = ((y - cy) / cy) * -10;
  const ry = ((x - cx) / cx) * 10;
  cardStyles[key] = {
    transform: `perspective(800px) rotateX(${rx}deg) rotateY(${ry}deg) scale3d(1.05,1.05,1.05)`,
  };
}
function onCardLeave(key: "price" | "stock" | "bond") {
  cardStyles[key] = { transition: "transform .4s ease", transform: "perspective(800px) rotateX(0) rotateY(0)" };
}

// ===== 时钟 =====
let clockTimer: number;
function updateClock() {
  const d = new Date();
  const h = String(d.getHours()).padStart(2, "0");
  const m = String(d.getMinutes()).padStart(2, "0");
  const s = String(d.getSeconds()).padStart(2, "0");
  currentTime.value = h + ":" + m + ":" + s;
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
    else ctx.lineTo(px, py);
  }
  ctx.strokeStyle = "#38bdf8";
  ctx.lineWidth = 1.5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();
  ctx.lineTo(w - 5, h - 5);
  ctx.lineTo(5, h - 5);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, "rgba(56,189,248,0.25)");
  grad.addColorStop(1, "rgba(56,189,248,0)");
  ctx.fillStyle = grad;
  ctx.fill();
}

// ===== 主折线图 — 科技蓝配色 =====
let chartAnimId: number | null = null;
let chartProgress = 0;

const OIL_DATA = {
  prices: [
    82.4, 79.8, 76.3, 72.1, 71.2,
    74.5, 78.0, 81.6, 84.3, 82.1,
    80.4, 83.7, 85.9, 87.1, 87.3,
  ],
  predictStartIdx: 9,
};

function drawMainChart() {
  const c = chartCanvasRef.value; if (!c) return;
  const ctx = c.getContext("2d"); if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const W = 440, H = 260;
  c.width = W * dpr; c.height = H * dpr;
  c.style.width = W + "px"; c.style.height = H + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const ox = W * 0.48, oy = H * 0.78;
  const depthY = 55;
  const gridCols = 7, gridRows = 4;

  const pts = OIL_DATA.prices;
  const n = pts.length;
  const minV = Math.min(...pts) - 3;
  const maxV = Math.max(...pts) + 4;
  const range = maxV - minV || 1;

  ctx.clearRect(0, 0, W, H);

  function proj(x2d: number, yVal: number, zDepth = 0): { x: number; y: number } {
    const hPx = ((yVal - minV) / range) * 110;
    const zScale = 1 - zDepth * 0.25;
    return {
      x: ox + (x2d - W / 2) * zScale,
      y: oy - hPx * zScale - zDepth * depthY,
    };
  }

  /* ─── 3D网格底座 ─── */
  const gW = 300, gH = 130;
  ctx.save();
  for (let r = 0; r <= gridRows; r++) {
    const ratio = r / gridRows;
    const yBase = oy + (ratio - 1) * gH * 0.6;
    const leftX = ox - gW / 2 * (1 - ratio * 0.35);
    const rightX = ox + gW / 2 * (1 - ratio * 0.35);
    ctx.beginPath();
    ctx.moveTo(leftX, yBase);
    ctx.lineTo(rightX, yBase);
    ctx.strokeStyle = `rgba(59,130,246,${0.04 + ratio * 0.02})`;
    ctx.lineWidth = 0.6;
    ctx.stroke();
  }
  for (let col = 0; col <= gridCols; col++) {
    const cxRatio = col / gridCols;
    const bottomX = ox - gW / 2 + cxRatio * gW;
    const topX = ox - gW / 2 * 0.65 + cxRatio * gW * 0.65;
    const topY = oy - gH * 0.6;
    ctx.beginPath();
    ctx.moveTo(bottomX, oy);
    ctx.lineTo(topX, topY);
    ctx.strokeStyle = `rgba(99,179,237,${0.03 + (1 - cxRatio) * 0.03})`;
    ctx.lineWidth = 0.5;
    ctx.stroke();
  }
  ctx.restore();

  /* ─── 数据点3D坐标 ─── */
  const drawN = Math.max(2, Math.floor(chartProgress * n));
  const xStep = gW / (n - 1);
  const pts3d = [];
  for (let i = 0; i < n; i++) {
    const x2d = ox - gW / 2 + i * xStep;
    const zD = Math.abs(i / (n - 1) - 0.5) * 0.15;
    pts3d.push(proj(x2d, pts[i], zD));
  }

  /* 面积填充 */
  if (drawN >= 2) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pts3d[0].x, pts3d[0].y);
    for (let i = 1; i < drawN; i++) {
      if (i < drawN - 1) {
        const mx = (pts3d[i].x + pts3d[i + 1].x) / 2;
        const my = (pts3d[i].y + pts3d[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts3d[i].x, pts3d[i].y, mx, my);
      } else {
        ctx.lineTo(pts3d[i].x, pts3d[i].y);
      }
    }
    const lastP = pts3d[drawN - 1];
    const firstP = pts3d[0];
    ctx.lineTo(lastP.x, oy);
    ctx.lineTo(ox + gW * 0.45, oy);
    ctx.lineTo(ox - gW * 0.45, oy);
    ctx.lineTo(firstP.x, oy);
    ctx.closePath();
    const ag = ctx.createLinearGradient(0, oy - 120, 0, oy);
    ag.addColorStop(0, "rgba(59,130,246,.12)");
    ag.addColorStop(OIL_DATA.predictStartIdx / n, "rgba(99,179,237,.06)");
    ag.addColorStop(.65, "rgba(139,92,246,.05)");
    ag.addColorStop(1, "rgba(139,92,246,.005)");
    ctx.fillStyle = ag;
    ctx.fill();
    ctx.globalCompositeOperation = "lighter";
    const glowG = ctx.createLinearGradient(0, oy - 100, 0, oy - 40);
    glowG.addColorStop(0, "rgba(59,130,246,.04)");
    glowG.addColorStop(1, "transparent");
    ctx.fillStyle = glowG;
    ctx.fill();
    ctx.restore();
  }

  /* 主曲线 */
  if (drawN >= 2) {
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pts3d[0].x, pts3d[0].y);
    for (let i = 1; i < drawN; i++) {
      if (i < drawN - 1) {
        const mx = (pts3d[i].x + pts3d[i + 1].x) / 2;
        const my = (pts3d[i].y + pts3d[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts3d[i].x, pts3d[i].y, mx, my);
      } else {
        ctx.lineTo(pts3d[i].x, pts3d[i].y);
      }
    }

    ctx.save();
    ctx.translate(2, 5);
    ctx.strokeStyle = "rgba(0,0,0,.30)";
    ctx.lineWidth = 8;
    ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.filter = "blur(5px)";
    ctx.stroke(); ctx.restore();

    ctx.strokeStyle = "rgba(59,130,246,.13)";
    ctx.lineWidth = 10;
    ctx.lineCap = "round"; ctx.lineJoin = "round";
    ctx.filter = "blur(3px)";
    ctx.stroke();
    ctx.filter = "none";

    const grad = ctx.createLinearGradient(
      pts3d[0].x, pts3d[0].y,
      pts3d[n - 1].x, pts3d[n - 1].y
    );
    grad.addColorStop(0, "#60a5fa");
    grad.addColorStop(.30, "#38bdf8");
    grad.addColorStop(.55, "#818cf8");
    grad.addColorStop(.80, "#a78bfa");
    grad.addColorStop(1, "#c084fc");

    ctx.strokeStyle = grad;
    ctx.lineWidth = 2.8;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();

    ctx.save();
    ctx.translate(-0.5, -1);
    ctx.strokeStyle = "rgba(255,255,255,.20)";
    ctx.lineWidth = 1.2;
    ctx.lineCap = "round";
    ctx.filter = "blur(0.4px)";
    ctx.beginPath();
    ctx.moveTo(pts3d[0].x, pts3d[0].y);
    for (let i = 1; i < drawN; i++) {
      if (i < drawN - 1) {
        const mx = (pts3d[i].x + pts3d[i + 1].x) / 2;
        const my = (pts3d[i].y + pts3d[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts3d[i].x, pts3d[i].y, mx, my);
      } else {
        ctx.lineTo(pts3d[i].x, pts3d[i].y);
      }
    }
    ctx.stroke();
    ctx.restore();
    ctx.restore();
  }

  /* 数据节点 */
  if (chartProgress >= 1) {
    const time = Date.now() / 1000;
    const keyIdx = [0, 4, 8, n - 1];
    keyIdx.forEach((idx) => {
      if (idx >= n || idx >= drawN) return;
      const p = pts3d[idx];
      const isEndpoint = idx === n - 1;
      const scale = isEndpoint ? 1.2 : (0.7 + Math.abs(idx / (n - 1) - 0.5) * 0.6);
      if (isEndpoint) {
        const pr = 6 + Math.sin(time * 3) * 2.5;
        ctx.beginPath(); ctx.arc(p.x, p.y, pr * scale + 5, 0, Math.PI * 2);
        ctx.strokeStyle = `rgba(192,132,252,${0.10 + Math.sin(time * 3) * 0.07})`;
        ctx.lineWidth = 1; ctx.stroke();
      }
      const ballR = (isEndpoint ? 5 : 3.5) * scale;
      const bx = p.x - ballR * 0.3, by = p.y - ballR * 0.3;
      const bg = ctx.createRadialGradient(bx, by, 0, p.x, p.y, ballR);
      if (idx <= OIL_DATA.predictStartIdx) {
        bg.addColorStop(0, "#ffffff");
        bg.addColorStop(.35, "#60a5fa");
        bg.addColorStop(1, "#1e3a8a");
      } else {
        bg.addColorStop(0, "#ffffff");
        bg.addColorStop(.35, "#a78bfa");
        bg.addColorStop(1, "#4c1d95");
      }
      ctx.beginPath(); ctx.arc(p.x, p.y, ballR, 0, Math.PI * 2);
      ctx.fillStyle = bg; ctx.fill();
    });

    const ep = pts3d[n - 1];
    const lp = pts[n - 1], pp = pts[n - 2];
    const chg = lp - pp, chgP = (chg / pp) * 100, isUp = chg >= 0;
    const labelY = ep.y - 18 - Math.sin(time * 2) * 2;
    ctx.font = "bold 14px system-ui";
    ctx.textAlign = "center";
    ctx.fillStyle = "#f1f5f9";
    ctx.fillText(`$${lp.toFixed(1)}`, ep.x, labelY);
    ctx.font = "bold 10px system-ui";
    ctx.fillStyle = isUp ? "#38bdf8" : "#f87171";
    ctx.fillText(`${isUp ? "+" : ""}${chg.toFixed(1)} (${isUp ? "+" : ""}${chgP.toFixed(1)}%)`, ep.x, labelY + 14);
  }

  /* 预测分界线 */
  if (chartProgress >= 0.7 && OIL_DATA.predictStartIdx < n && OIL_DATA.predictStartIdx < drawN) {
    const dp = pts3d[OIL_DATA.predictStartIdx];
    ctx.save();
    ctx.setLineDash([3, 4]);
    ctx.strokeStyle = "rgba(139,92,246,.18)";
    ctx.lineWidth = 0.8;
    ctx.beginPath();
    ctx.moveTo(dp.x, dp.y);
    ctx.lineTo(dp.x + 15, oy - 5);
    ctx.stroke();
    ctx.setLineDash([]);
    ctx.font = "bold 8px system-ui";
    ctx.textAlign = "left";
    ctx.fillStyle = "rgba(139,92,246,.4)";
    ctx.fillText("FORECAST", dp.x + 4, dp.y - 8);
    ctx.restore();
  }
}

function animateChart() {
  if(chartProgress<1){
    chartProgress+=.018;
    if(chartProgress>1)chartProgress=1;
    drawMainChart();
    chartAnimId=requestAnimationFrame(animateChart);
  }else{
    chartAnimId=requestAnimationFrame(function tick(){drawMainChart();chartAnimId=requestAnimationFrame(tick)});
  }
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
  drawPriceSparkline();
  animateChart();
  window.addEventListener("resize", () => {
    drawMainChart();
  });
});
onBeforeUnmount(() => {
  clearInterval(clockTimer);
  if (chartAnimId !== null) cancelAnimationFrame(chartAnimId);
  window.removeEventListener("resize", drawMainChart);
});
</script>

<style scoped>
/* ================================================================
   LANDING PAGE — 大宗绿测
   Design: Tech-blue dark-mode with glow orbs background
   Layout: Left brand (42%) | Right visualization (58%)
   ================================================================ */

/* ─── Reset & Container ─── */
.landing {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #060a14;
  color: #e2e8f0;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "PingFang SC",
    sans-serif;
}

/* ─── Background — 多层光晕 ─── */
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
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 220px 220px;
}
.glow {
  position: absolute;
  border-radius: 50%;
}
/* 主蓝色光晕 — 右上 */
.glow--1 {
  width: 700px; height: 700px;
  top: -250px; right: -100px;
  background: radial-gradient(circle, rgba(30,64,175,.35) 0%, rgba(30,64,175,.08) 40%, transparent 70%);
  filter: blur(80px);
  animation: drift1 20s ease-in-out infinite alternate;
}
/* 青蓝光晕 — 左下 */
.glow--2 {
  width: 550px; height: 550px;
  bottom: -200px; left: -100px;
  background: radial-gradient(circle, rgba(6,182,212,.2) 0%, transparent 65%);
  filter: blur(90px);
  animation: drift2 26s ease-in-out infinite alternate;
}
/* 紫蓝光晕 — 中心 */
.glow--3 {
  width: 400px; height: 400px;
  top: 35%; left: 40%;
  background: radial-gradient(circle, rgba(99,102,241,.12) 0%, transparent 60%);
  filter: blur(100px);
  animation: drift3 18s ease-in-out infinite alternate;
}
/* 小蓝点缀 — 右下 */
.glow--4 {
  width: 300px; height: 300px;
  bottom: 10%; right: 15%;
  background: radial-gradient(circle, rgba(56,189,248,.1) 0%, transparent 60%);
  filter: blur(70px);
  animation: drift4 22s ease-in-out infinite alternate;
}
/* 紫色点缀 — 左上 */
.glow--5 {
  width: 250px; height: 250px;
  top: 15%; left: 20%;
  background: radial-gradient(circle, rgba(139,92,246,.08) 0%, transparent 55%);
  filter: blur(60px);
  animation: drift5 15s ease-in-out infinite alternate;
}

@keyframes drift1 { to { transform: translate(-50px, 40px) scale(1.08); } }
@keyframes drift2 { to { transform: translate(60px, -30px) scale(1.1); } }
@keyframes drift3 { to { transform: translate(-30px, -40px) scale(1.15); } }
@keyframes drift4 { to { transform: translate(40px, 20px) scale(.9); } }
@keyframes drift5 { to { transform: translate(20px, 30px) scale(1.2); } }

/* ─── Main Grid ─── */
.main-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 42% 58%;
  min-height: 100vh;
  max-width: 1500px;
  margin: 0 auto;
}

/* ─── LEFT: Brand Column ─── */
.brand-col {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px 40px 48px 140px;
}

/* 标签行 */
.top-mark {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 22px;
  animation: fadeUp 0.5s ease both;
}
.mark-line {
  width: 24px;
  height: 2px;
  background: #3b82f6;
  box-shadow: 0 0 12px rgba(59, 130, 246, 0.7);
  border-radius: 1px;
}
.mark-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 3px;
  color: rgba(96, 165, 250, 0.6);
  text-transform: uppercase;
}

/* 标题 */
.hero-title {
  margin: 0 0 14px;
  animation: fadeUp 0.5s ease 0.08s both;
}
.title-line {
  display: block;
  font-size: clamp(34px, 4vw, 50px);
  font-weight: 800;
  letter-spacing: 4px;
  line-height: 1.12;
  background: linear-gradient(135deg, #f1f5f9 0%, #94a3b8 55%, #60a5fa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-desc {
  margin: 0 0 30px;
  font-size: 13.5px;
  line-height: 1.75;
  color: rgba(148, 163, 184, 0.5);
  max-width: 380px;
  animation: fadeUp 0.5s ease 0.16s both;
}

/* 功能列表 */
.feat-list {
  list-style: none;
  margin: 0 0 32px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.feat-item {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 12px 16px;
  border-radius: 11px;
  border: 1px solid transparent;
  background: transparent;
  cursor: default;
  opacity: 0;
  animation: fadeUp 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  transition: all 0.25s ease;
}
.feat-item:hover {
  border-color: rgba(59, 130, 246, 0.1);
  background: rgba(59, 130, 246, 0.03);
  transform: translateX(6px);
}
.feat--1 { animation-delay: 0.26s; }
.feat--2 { animation-delay: 0.34s; }
.feat--3 { animation-delay: 0.42s; }
.feat--4 { animation-delay: 0.5s; }
.feat-num {
  font-size: 11px;
  font-weight: 800;
  color: rgba(96, 165, 250, 0.3);
  min-width: 24px;
}
.feat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.feat-body strong {
  font-size: 13.5px;
  font-weight: 700;
  color: #e2e8f0;
}
.feat-body span {
  font-size: 11.5px;
  color: rgba(148, 163, 184, 0.38);
  line-height: 1.5;
}

/* CTA 按钮 */
.cta-row {
  display: flex;
  align-items: center;
  gap: 12px;
  animation: fadeUp 0.5s ease 0.58s both;
}
.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 14px 32px;
  border: none;
  border-radius: 10px;
  background: linear-gradient(135deg, #2563eb, #1d4ed8);
  color: #fff;
  font-size: 13.5px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow:
    0 4px 24px rgba(37, 99, 235, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
.cta-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 36px rgba(37, 99, 235, 0.5);
}
.cta-primary svg { transition: transform 0.25s; }
.cta-primary:hover svg { transform: translateX(4px); }
.cta-secondary {
  padding: 14px 26px;
  border: 1px solid rgba(96, 165, 250, 0.2);
  border-radius: 10px;
  background: transparent;
  color: rgba(148, 163, 184, 0.55);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
}
.cta-secondary:hover {
  border-color: rgba(96, 165, 250, 0.4);
  color: #93c5fd;
  background: rgba(59, 130, 246, 0.05);
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 7px;
  padding-top: 26px;
  font-size: 10px;
  font-weight: 500;
  letter-spacing: 1px;
  color: rgba(148, 163, 184, 0.25);
  animation: fadeUp 0.5s ease 0.66s both;
}
.status-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #3b82f6;
  animation: blink 2s ease-in-out infinite;
}
.divider { opacity: 0.2; }
@keyframes blink {
  0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(59,130,246,.4); }
  50% { opacity: 0.4; box-shadow: 0 0 0 5px rgba(59,130,246,0); }
}

@keyframes fadeUp {
  from { opacity: 0; transform: translateY(12px); }
  to { opacity: 1; transform: none; }
}

/* ══════════════════════════════════════════════════
   RIGHT: Bento Grid + 3D Cards + Spotlight
   ══════════════════════════════════════════════════ */

/* ─── 容器 ─── */
.viz-col {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 28px 24px;
  overflow: hidden;
  border-left: 1px solid rgba(59,130,246,.06);
  height: 100%;
  perspective: 1200px;
}

/* ─── Spotlight 聚光灯 ─── */
.spotlight-layer {
  position: absolute;
  width: 600px; height: 600px;
  top: -200px; right: -150px;
  background: radial-gradient(
    circle,
    rgba(59,130,246,.1) 0%,
    rgba(99,102,241,.05) 35%,
    transparent 70%
  );
  pointer-events: none;
  z-index: 1;
  animation: spotlightFloat 8s ease-in-out infinite alternate;
}
.spotlight-layer--2 {
  width: 500px; height: 500px;
  top: auto; bottom: -200px; right: auto; left: -100px;
  background: radial-gradient(
    circle,
    rgba(139,92,246,.06) 0%,
    transparent 65%
  );
  animation: spotlightFloat2 12s ease-in-out infinite alternate;
}
@keyframes spotlightFloat {
  0%   { transform: translate(0,0) scale(1); }
  50%  { transform: translate(-40px,30px) scale(1.15); }
  100% { transform: translate(-20px,-20px) scale(.95); }
}
@keyframes spotlightFloat2 {
  0%   { transform: translate(0,0) scale(1); }
  50%  { transform: translate(30px,-20px) scale(1.1); }
  100% { transform: translate(-10px,15px) scale(.9); }
}

/* ─── Bento Grid 布局（3小卡横排）─── */
.bento-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  grid-template-rows: auto auto;
  gap: 14px;
  z-index: 2;
  position: relative;
  width: 100%;
  max-width: 540px;
}

/* ═══ 核心大卡 — 油价预测 ═══ */
.bento-card--hero {
  grid-column: 1 / -1;
  border-radius: 18px;
  position: relative;
  overflow: hidden;
  background: linear-gradient(135deg, rgba(59,130,246,.06) 0%, transparent 50%),
              linear-gradient(to bottom, rgba(8,16,36,.75) 0%, rgba(6,10,20,.9) 100%);
  border: 1px solid rgba(59,130,246,.1);
  box-shadow:
    0 25px 70px -15px rgba(0,0,0,.55),
    0 0 60px -20px rgba(59,130,246,.08),
    inset 0 1px 0 rgba(255,255,255,.04);
  backdrop-filter: blur(24px) saturate(1.4);
  transition: transform .15s ease-out;
  transform-style: preserve-3d;
}
.hero-inner { padding: 18px 20px 16px; position: relative; z-index: 2; }
.hero-header { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.hero-tag { font-size: 9px; font-weight: 700; letter-spacing: .12em; padding: 3px 8px; border-radius: 6px; text-transform: uppercase; }
.hero-tag--gru { color: #a78bfa; background: rgba(139,92,246,.1); border: 1px solid rgba(139,92,246,.2); }
.hero-meta { font-size: 11px; color: rgba(148,163,184,.45); }
.hero-chart { display: block; width:100%!important; height:auto!important; max-height:200px; }
.hero-footer { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; font-size: 11px; color: rgba(148,163,184,.5); }
.hero-acc strong { color: #60a5fa; font-size: 13px; }
.hero-live { display: flex; align-items: center; gap: 5px; }
.live-pulse { display:inline-block; width:6px; height:6px; border-radius:50%; background:#3b82f6; animation: pulseLive 2s ease infinite; box-shadow:0 0 8px rgba(59,130,246,.5); }
@keyframes pulseLive { 0%,100%{opacity:1} 50%{opacity:.3} }

.hero-glow { position:absolute; inset:0; pointer-events:none; border-radius:18px;
  background: radial-gradient(ellipse at 50% 120%, rgba(59,130,246,.04) 0%, transparent 55%); z-index:1; }
.bento-card--hero:hover { border-color: rgba(59,130,246,.2);
  box-shadow: 0 35px 90px -15px rgba(0,0,0,.62), 0 0 80px -15px rgba(59,130,246,.15), inset 0 1px 0 rgba(255,255,255,.07); }

/* ═══ 小卡片 — 统一基础样式 ═══ */
.bento-card {
  border-radius: 14px;
  position: relative;
  overflow: hidden;
  cursor: default;
  background: linear-gradient(135deg, rgba(59,130,246,.04) 0%, transparent 50%),
              linear-gradient(to bottom, rgba(8,16,36,.7) 0%, rgba(6,10,20,.85) 100%);
  border: 1px solid rgba(59,130,246,.06);
  backdrop-filter: blur(20px) saturate(1.3);
  box-shadow: 0 12px 36px -10px rgba(0,0,0,.42), inset 0 1px 0 rgba(255,255,255,.03);
  transition: transform .12s ease-out, box-shadow .3s ease, border-color .3s ease;
  transform-style: preserve-3d;
}
.bc-content { padding: 14px 15px; position: relative; z-index: 2; }

/* 图标 */
.bc-icon { display:block; width:28px; height:28px; border-radius:8px; margin-bottom:8px; position:relative; overflow:hidden; }
.bc-icon--oil { background: linear-gradient(135deg,rgba(59,130,246,.15),rgba(59,130,246,.05)); border:1px solid rgba(59,130,246,.15); }
.bc-icon--oil::after { content:""; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; width:14px; height:14px; margin:auto; border-radius:50%; background:#60a5fa; box-shadow:0 0 6px rgba(59,130,246,.5); }
.bc-icon--bolt { background: linear-gradient(135deg,rgba(6,182,212,.15),rgba(6,182,212,.05)); border:1px solid rgba(6,182,212,.15); }
.bc-icon--bolt::after { content:""; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; width:14px; height:14px; margin:auto; border-radius:50%; background:#22d3ee; box-shadow:0 0 6px rgba(6,182,212,.5); }
.bc-icon--rate { background: linear-gradient(135deg,rgba(139,92,246,.15),rgba(139,92,246,.05)); border:1px solid rgba(139,92,246,.15); }
.bc-icon--rate::after { content:""; position:absolute; inset:0; display:flex; align-items:center; justify-content:center; width:14px; height:14px; margin:auto; border-radius:4px; background:#8b5cf6; box-shadow:0 0 6px rgba(139,92,246,.5); }

.bc-label { display:block; font-size:9px; font-weight:600; letter-spacing:.12em; text-transform:uppercase; color:rgba(148,163,184,.45); margin-bottom:6px; }
.bc-value { display:block; font-size:26px; font-weight:800; color:#f1f5f9; line-height:1.1; letter-spacing:-.02em; }
.bc-delta { display:inline-block; font-size:12px; font-weight:700; padding:2px 7px; border-radius:5px; margin-top:4px; }
.bc-delta.bc-up { color:#38bdf8; background: rgba(56,189,248,.1); }
.bc-list { display:flex; flex-direction: column; gap:5px; margin-top:4px; }
.bc-item { display:flex; align-items:baseline; justify-content:space-between; gap:8px; font-size:11px; color:rgba(148,163,184,.55); }
.bc-item em { font-style:normal; font-weight:700; color:#e2e8f0; font-size:13px; }
.bc-item small { font-size:10px; font-weight:600; padding:1px 5px; border-radius:4px; }
.bc-item small.bc-up { color:#38bdf8; background:rgba(56,189,248,.09); }
.bc-spark { display:block; width:100%!important; margin-top:6px; opacity:.7; }

/* 卡片高光（hover扫光）*/
.bc-shine { position:absolute; inset:0; pointer-events:none; opacity:0;
  background: linear-gradient(105deg, transparent 40%, rgba(96,165,250,.05) 45%, rgba(147,197,253,.1) 50%, rgba(96,165,250,.05) 55%, transparent 60%);
  border-radius: 14px; z-index:1; transition: opacity .3s ease; }
.bento-card:hover .bc-shine { opacity:1; }
.bento-card:hover { border-color: rgba(59,130,246,.15);
  box-shadow: 0 18px 48px -8px rgba(0,0,0,.5), 0 0 30px -10px rgba(59,130,246,.08), inset 0 1px 0 rgba(255,255,255,.06); }

/* 小卡高度 */
.bento-card--price { min-height: 130px; }
.bento-card--stock { min-height: 140px; }
.bento-card--bond  { min-height: 120px; }

/* ═══ 响应式 ═══ */
@media (max-width: 1280px) {
  .bento-grid { max-width: 100%; }
}
@media (max-width: 1024px) {
  .main-grid { grid-template-columns: 1fr; grid-template-rows: auto auto; }
  .brand-col { padding: 36px 28px 32px; }
  .viz-col { border-left: none; border-top: 1px solid rgba(59,130,246,.06); min-height: 500px; padding: 24px 16px; }
  .bento-card { position:relative!important; width:100%!important; margin:0 auto 12px; animation: fadeUp .5s ease forwards!important; }
  .bento-card--hero { order: -1; }
  .live-tag { display: none; }
}
@media (max-width: 640px) {
  .brand-col { padding: 24px 16px 20px; }
  .title-line { letter-spacing: 2px; }
  .cta-row { flex-direction: column; }
  .bento-card { max-width: 100%!important; }
}
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.001ms !important;
    transition-duration: 0.001ms !important;
  }
}
</style>
