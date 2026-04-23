<template>
  <div class="landing">
    <!-- 登录弹框 -->
    <AuthModal
      :visible="showAuth"
      @update:visible="showAuth = $event"
      @success="onAuthSuccess"
    />

    <!-- 背景 — 多层深度 -->
    <div class="bg-layer" aria-hidden="true">
      <!-- SVG噪点纹理 -->
      <svg class="noise-svg" aria-hidden="true">
        <filter id="grain">
          <feTurbulence
            type="fractalNoise"
            baseFrequency=".75"
            numOctaves="4"
            stitchTiles="stitch"
          />
        </filter>
        <rect width="100%" height="100%" filter="url(#grain)" opacity=".035" />
      </svg>
      <!-- 主渐变底色 -->
      <div class="bg-base"></div>
      <!-- 对角光线 -->
      <div class="bg-rays"></div>
      <!-- 漂浮光斑 -->
      <div class="bg-orb bg-orb--a"></div>
      <div class="bg-orb bg-orb--b"></div>
      <div class="bg-orb bg-orb--c"></div>
      <div class="bg-orb bg-orb--d"></div>
      <div class="bg-orb bg-orb--e"></div>
      <!-- 网格线 -->
      <div class="bg-grid"></div>
      <!-- 漂浮微粒 -->
      <canvas
        ref="particleCanvasRef"
        class="particle-canvas"
        aria-hidden="true"
      ></canvas>
    </div>

    <!-- 主内容 -->
    <main class="main-grid">
      <!-- ══ 左侧品牌区 ═══ -->
      <section class="brand-col">
        <header class="top-mark">
          <span class="mark-dot"></span>
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

      <!-- ══ 右侧：数据展示 ═══ -->
      <aside class="viz-col">
        <!-- 不规则卡片容器 -->
        <div class="card-scatter">
          <!-- ★ 主卡片 — 油价图表 -->
          <div
            class="data-card data-card--hero"
            @mousemove="onHeroTilt"
            @mouseleave="onHeroLeave"
            :style="heroStyle"
          >
            <div class="dc-spotlight" :style="heroSpotStyle"></div>
            <div class="dc-head">
              <span class="dc-tag">GRU MODEL</span>
              <span class="dc-sub">Brent Crude · Forecast</span>
            </div>
            <canvas
              ref="chartCanvasRef"
              class="dc-chart"
              width="400"
              height="200"
              aria-hidden="true"
            ></canvas>
            <div class="dc-foot">
              <span>Accuracy <strong>94.7%</strong></span>
              <span class="dc-live"><i class="live-dot"></i> LIVE</span>
            </div>
          </div>

          <!-- 油价实时卡 -->
          <div
            class="data-card data-card--oil"
            @mousemove="(e) => onCardTilt(e, 'price')"
            @mouseleave="() => onCardLeave('price')"
            :style="cardStyles.price"
          >
            <div class="dc-spotlight" :style="cardSpotStyles.price"></div>
            <div class="dc-content">
              <div class="dc-head-row">
                <span class="dc-label">Oil Price</span>
                <span class="dc-live-badge"><i class="live-dot"></i> LIVE</span>
              </div>
              <div class="dc-price-row">
                <span class="dc-big">$78.42</span>
                <span class="dc-chg dc-chg--up">+2.34%</span>
              </div>
              <canvas
                ref="priceChartRef"
                class="dc-spark"
                width="120"
                height="28"
                aria-hidden="true"
              ></canvas>
              <div class="dc-meta-row">
                <span>Vol: 2.4M</span>
                <span>$76.8 — $79.2</span>
              </div>
            </div>
          </div>

          <!-- 新能源股票卡 -->
          <div
            class="data-card data-card--energy"
            @mousemove="(e) => onCardTilt(e, 'stock')"
            @mouseleave="() => onCardLeave('stock')"
            :style="cardStyles.stock"
          >
            <div class="dc-spotlight" :style="cardSpotStyles.stock"></div>
            <div class="dc-content">
              <div class="dc-head-row">
                <span class="dc-label">New Energy</span>
                <span class="dc-badge dc-badge--up">↗ +1.4%</span>
              </div>
              <div class="dc-rows">
                <div class="dc-row">
                  <span>CSI新能源</span>
                  <em>3,847</em>
                  <small class="dc-up">+1.82%</small>
                </div>
                <div class="dc-row">
                  <span>光伏产业</span>
                  <em>4,126</em>
                  <small class="dc-up">+0.95%</small>
                </div>
                <div class="dc-row">
                  <span>新能源车</span>
                  <em>2,934</em>
                  <small class="dc-down">−0.42%</small>
                </div>
              </div>
              <div class="dc-spark-inline">
                <svg viewBox="0 0 80 22" preserveAspectRatio="none">
                  <polyline
                    fill="none"
                    stroke="#34d399"
                    stroke-width="1.3"
                    points="0,18 12,15 24,17 36,10 48,12 60,6 72,8 80,5"
                  />
                </svg>
              </div>
            </div>
          </div>

          <!-- 债券/利率卡 -->
          <div
            class="data-card data-card--bond"
            @mousemove="(e) => onCardTilt(e, 'bond')"
            @mouseleave="() => onCardLeave('bond')"
            :style="cardStyles.bond"
          >
            <div class="dc-spotlight" :style="cardSpotStyles.bond"></div>
            <div class="dc-content">
              <div class="dc-head-row">
                <span class="dc-label">Bond / Rate</span>
                <span class="dc-badge dc-badge--stable">Stable</span>
              </div>
              <div class="dc-rows">
                <div class="dc-row">
                  <span>10Y国债</span><em>2.34%</em
                  ><small class="dc-rate-down">−2bp</small>
                </div>
                <div class="dc-row">
                  <span>SHIBOR</span><em>1.68%</em
                  ><small class="dc-rate-flat">0bp</small>
                </div>
                <div class="dc-row">
                  <span>LPR 1Y</span><em>3.45%</em
                  ><small class="dc-rate-down">−5bp</small>
                </div>
              </div>
              <div class="dc-rate-bar">
                <div class="rate-bar-track">
                  <div class="rate-bar-fill" style="width: 65%"></div>
                </div>
              </div>
            </div>
          </div>

          <!-- AI 分析卡 -->
          <div
            class="data-card data-card--ai"
            @mousemove="(e) => onCardTilt(e, 'ai')"
            @mouseleave="() => onCardLeave('ai')"
            :style="cardStyles.ai"
          >
            <div class="dc-spotlight" :style="cardSpotStyles.ai"></div>
            <div class="dc-content">
              <div class="dc-head-row">
                <span class="dc-label">AI Insight</span>
                <span class="dc-live-badge"
                  ><i class="live-dot live-dot--green"></i> Active</span
                >
              </div>
              <div class="dc-ai-grid">
                <div class="ai-metric">
                  <span class="ai-metric-label">Confidence</span>
                  <span class="ai-metric-val">94.7%</span>
                </div>
                <div class="ai-metric">
                  <span class="ai-metric-label">Model</span>
                  <span class="ai-metric-val">GRU+LSTM</span>
                </div>
              </div>
              <div class="dc-signals">
                <div class="signal-item">
                  <span class="signal-dot signal-dot--buy"></span
                  ><span>Bullish — Brent</span>
                </div>
                <div class="signal-item">
                  <span class="signal-dot signal-dot--hold"></span
                  ><span>Hold — Green Bond</span>
                </div>
              </div>
              <div class="dc-ai-progress">
                <div class="ai-bar-track">
                  <div
                    class="ai-bar-fill"
                    :style="{ width: aiProgress + '%' }"
                  ></div>
                </div>
                <span class="ai-bar-label">Analysis {{ aiProgress }}%</span>
              </div>
            </div>
          </div>
        </div>
      </aside>
    </main>
  </div>
</template>

<script setup lang="ts">
// @ts-nocheck
import { ref, reactive, onMounted, onBeforeUnmount } from "vue";
import { useRouter } from "vue-router";
import AuthModal from "@/components/AuthModal.vue";
import { getToken } from "@/api/auth";

const router = useRouter();
const showAuth = ref(false);
const priceChartRef = ref<HTMLCanvasElement | null>(null);
const chartCanvasRef = ref<HTMLCanvasElement | null>(null);
const particleCanvasRef = ref<HTMLCanvasElement | null>(null);
const currentTime = ref("");

// ===== 3D 卡片倾斜 + 鼠标光晕 =====
const heroStyle = ref<Record<string, string>>({});
const heroSpotStyle = ref<Record<string, string>>({});
const cardStyles = reactive({
  price: {} as Record<string, string>,
  stock: {} as Record<string, string>,
  bond: {} as Record<string, string>,
  ai: {} as Record<string, string>,
});
const cardSpotStyles = reactive({
  price: {} as Record<string, string>,
  stock: {} as Record<string, string>,
  bond: {} as Record<string, string>,
  ai: {} as Record<string, string>,
});
const aiProgress = ref(0);

function onHeroTilt(e: MouseEvent) {
  const el = e.currentTarget as HTMLElement;
  const r = el.getBoundingClientRect();
  const x = e.clientX - r.left,
    y = e.clientY - r.top;
  const cx = r.width / 2,
    cy = r.height / 2;
  const rx = ((y - cy) / cy) * -6;
  const ry = ((x - cx) / cx) * 6;
  heroStyle.value = {
    transform: `perspective(900px) rotateX(${rx}deg) rotateY(${ry}deg)`,
  };
  heroSpotStyle.value = {
    opacity: "1",
    background: `radial-gradient(circle 200px at ${x}px ${y}px, rgba(99,102,241,.08), transparent)`,
  };
}
function onHeroLeave() {
  heroStyle.value = {
    transition: "transform .6s cubic-bezier(.22,1,.36,1)",
    transform: "perspective(900px) rotateX(0) rotateY(0)",
  };
  heroSpotStyle.value = { opacity: "0", transition: "opacity .5s" };
}

function onCardTilt(e: MouseEvent, key: "price" | "stock" | "bond" | "ai") {
  const el = e.currentTarget as HTMLElement;
  const r = el.getBoundingClientRect();
  const x = e.clientX - r.left,
    y = e.clientY - r.top;
  const cx = r.width / 2,
    cy = r.height / 2;
  const rx = ((y - cy) / cy) * -8;
  const ry = ((x - cx) / cx) * 8;
  cardStyles[key] = {
    transform: `perspective(700px) rotateX(${rx}deg) rotateY(${ry}deg) translateY(-2px)`,
  };
  const colors: Record<string, string> = {
    price: "rgba(245,158,11,.10)",
    stock: "rgba(16,185,129,.10)",
    bond: "rgba(244,114,182,.10)",
    ai: "rgba(139,92,246,.10)",
  };
  cardSpotStyles[key] = {
    opacity: "1",
    background: `radial-gradient(circle 140px at ${x}px ${y}px, ${colors[key]}, transparent)`,
  };
}
function onCardLeave(key: "price" | "stock" | "bond" | "ai") {
  cardStyles[key] = {
    transition: "transform .5s cubic-bezier(.22,1,.36,1)",
    transform: "perspective(700px) rotateX(0) rotateY(0)",
  };
  cardSpotStyles[key] = { opacity: "0", transition: "opacity .4s" };
}

// ===== 背景微粒 =====
let particleAnimId: number | null = null;
function initParticles() {
  const c = particleCanvasRef.value;
  if (!c) return;
  const ctx = c.getContext("2d");
  if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  function resize() {
    c.width = window.innerWidth * dpr;
    c.height = window.innerHeight * dpr;
    c.style.width = window.innerWidth + "px";
    c.style.height = window.innerHeight + "px";
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }
  resize();
  window.addEventListener("resize", resize);

  const particles: Array<{
    x: number;
    y: number;
    r: number;
    vx: number;
    vy: number;
    a: number;
    phase: number;
  }> = [];
  for (let i = 0; i < 60; i++) {
    particles.push({
      x: Math.random() * window.innerWidth,
      y: Math.random() * window.innerHeight,
      r: Math.random() * 1.2 + 0.3,
      vx: (Math.random() - 0.5) * 0.15,
      vy: (Math.random() - 0.5) * 0.1 - 0.05,
      a: Math.random() * 0.3 + 0.05,
      phase: Math.random() * Math.PI * 2,
    });
  }

  function draw() {
    ctx.clearRect(0, 0, window.innerWidth, window.innerHeight);
    const t = Date.now() / 1000;
    particles.forEach((p) => {
      p.x += p.vx + Math.sin(t + p.phase) * 0.08;
      p.y += p.vy;
      if (p.x < -10) p.x = window.innerWidth + 10;
      if (p.x > window.innerWidth + 10) p.x = -10;
      if (p.y < -10) p.y = window.innerHeight + 10;
      if (p.y > window.innerHeight + 10) p.y = -10;
      const flicker = 0.5 + Math.sin(t * 1.5 + p.phase) * 0.5;
      ctx.beginPath();
      ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(148,180,220,${p.a * flicker})`;
      ctx.fill();
    });
    particleAnimId = requestAnimationFrame(draw);
  }
  draw();
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
  ctx.strokeStyle = "#f59e0b";
  ctx.lineWidth = 1.5;
  ctx.lineCap = "round";
  ctx.lineJoin = "round";
  ctx.stroke();
  ctx.lineTo(w - 5, h - 5);
  ctx.lineTo(5, h - 5);
  ctx.closePath();
  const grad = ctx.createLinearGradient(0, 0, 0, h);
  grad.addColorStop(0, "rgba(245,158,11,0.2)");
  grad.addColorStop(1, "rgba(245,158,11,0)");
  ctx.fillStyle = grad;
  ctx.fill();
}

// ===== 主图表 — 暗夜雷达风 =====
let chartAnimId: number | null = null;
let chartProgress = 0;
const OIL_DATA = {
  actual: [82.4, 79.8, 76.3, 72.1, 71.2, 74.5, 78.0, 81.6, 84.3, 82.1],
  predicted: [82.1, 80.4, 83.7, 85.9, 87.1, 87.3],
  wti: [
    78.2, 76.1, 73.8, 69.5, 68.7, 71.8, 75.3, 78.9, 81.5, 79.3, 77.6, 81.2,
    83.4, 84.6, 84.9,
  ],
};

function drawMainChart() {
  const c = chartCanvasRef.value;
  if (!c) return;
  const ctx = c.getContext("2d");
  if (!ctx) return;
  const dpr = window.devicePixelRatio || 1;
  const W = 520,
    H = 300;
  c.width = W * dpr;
  c.height = H * dpr;
  c.style.width = W + "px";
  c.style.height = H + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const allPrices = [
    ...OIL_DATA.actual,
    ...OIL_DATA.predicted,
    ...OIL_DATA.wti,
  ];
  const minV = Math.min(...allPrices) - 4;
  const maxV = Math.max(...allPrices) + 5;
  const range = maxV - minV || 1;
  const pad = { top: 28, right: 50, bottom: 32, left: 48 };
  const chartW = W - pad.left - pad.right;
  const chartH = H - pad.top - pad.bottom;
  const time = Date.now() / 1000;
  ctx.clearRect(0, 0, W, H);

  // 扫描线
  const scanY = (time * 40) % H;
  const scanGrad = ctx.createLinearGradient(0, scanY - 30, 0, scanY + 30);
  scanGrad.addColorStop(0, "transparent");
  scanGrad.addColorStop(0.5, "rgba(59,130,246,.025)");
  scanGrad.addColorStop(1, "transparent");
  ctx.fillStyle = scanGrad;
  ctx.fillRect(0, 0, W, H);

  // 网格
  const hLines = 5;
  for (let i = 0; i <= hLines; i++) {
    const y = pad.top + (chartH / hLines) * i;
    ctx.beginPath();
    ctx.moveTo(pad.left, y);
    ctx.lineTo(W - pad.right, y);
    ctx.strokeStyle =
      i === hLines ? "rgba(148,163,184,.10)" : "rgba(148,163,184,.04)";
    ctx.lineWidth = i === hLines ? 0.7 : 0.4;
    ctx.stroke();
    const priceVal = maxV - (i / hLines) * range;
    ctx.font = "10px 'SF Mono','Cascadia Code',monospace";
    ctx.fillStyle = "rgba(148,163,184,.25)";
    ctx.textAlign = "right";
    ctx.fillText(`$${priceVal.toFixed(0)}`, pad.left - 8, y + 3);
  }
  const vLines = 6;
  for (let i = 0; i <= vLines; i++) {
    const x = pad.left + (chartW / vLines) * i;
    ctx.beginPath();
    ctx.moveTo(x, pad.top);
    ctx.lineTo(x, H - pad.bottom);
    ctx.strokeStyle = "rgba(148,163,184,.025)";
    ctx.lineWidth = 0.4;
    ctx.stroke();
  }

  const brentAll = [...OIL_DATA.actual, ...OIL_DATA.predicted];
  const wtiAll = OIL_DATA.wti;
  const totalN = brentAll.length;
  const drawN = Math.max(2, Math.floor(chartProgress * totalN));
  const wtiDrawN = Math.min(drawN, wtiAll.length);

  function toX(i: number, len: number) {
    return pad.left + (i / (len - 1)) * chartW;
  }
  function toY(val: number) {
    return pad.top + ((maxV - val) / range) * chartH;
  }

  function drawLine(
    data: number[],
    maxI: number,
    color: string,
    glowColor: string,
    fillC1: string,
    fillC2: string,
    lineW: number,
    isPrimary: boolean,
    nodeColor: string,
  ) {
    if (maxI < 2) return;
    const pts: Array<{ x: number; y: number }> = [];
    for (let i = 0; i < maxI && i < data.length; i++)
      pts.push({ x: toX(i, data.length), y: toY(data[i]) });

    // 面积
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) {
      if (i < pts.length - 1) {
        const mx = (pts[i].x + pts[i + 1].x) / 2;
        const my = (pts[i].y + pts[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my);
      } else ctx.lineTo(pts[i].x, pts[i].y);
    }
    ctx.lineTo(pts[pts.length - 1].x, H - pad.bottom);
    ctx.lineTo(pts[0].x, H - pad.bottom);
    ctx.closePath();
    const fg = ctx.createLinearGradient(0, pad.top, 0, H - pad.bottom);
    fg.addColorStop(0, fillC1);
    fg.addColorStop(1, fillC2);
    ctx.fillStyle = fg;
    ctx.fill();
    ctx.restore();

    // 发光
    if (isPrimary) {
      ctx.save();
      ctx.beginPath();
      ctx.moveTo(pts[0].x, pts[0].y);
      for (let i = 1; i < pts.length; i++) {
        if (i < pts.length - 1) {
          const mx = (pts[i].x + pts[i + 1].x) / 2;
          const my = (pts[i].y + pts[i + 1].y) / 2;
          ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my);
        } else ctx.lineTo(pts[i].x, pts[i].y);
      }
      ctx.strokeStyle = glowColor;
      ctx.lineWidth = 12;
      ctx.lineCap = "round";
      ctx.lineJoin = "round";
      ctx.filter = "blur(6px)";
      ctx.stroke();
      ctx.filter = "none";
      ctx.restore();
    }

    // 主线
    ctx.save();
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) {
      if (i < pts.length - 1) {
        const mx = (pts[i].x + pts[i + 1].x) / 2;
        const my = (pts[i].y + pts[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my);
      } else ctx.lineTo(pts[i].x, pts[i].y);
    }
    const lg = ctx.createLinearGradient(pts[0].x, 0, pts[pts.length - 1].x, 0);
    lg.addColorStop(0, color);
    lg.addColorStop(1, isPrimary ? "#c084fc" : color);
    ctx.strokeStyle = lg;
    ctx.lineWidth = lineW;
    ctx.lineCap = "round";
    ctx.lineJoin = "round";
    ctx.stroke();

    // 高光
    ctx.save();
    ctx.translate(0, -0.8);
    ctx.strokeStyle = "rgba(255,255,255,.10)";
    ctx.lineWidth = 0.7;
    ctx.filter = "blur(0.3px)";
    ctx.beginPath();
    ctx.moveTo(pts[0].x, pts[0].y);
    for (let i = 1; i < pts.length; i++) {
      if (i < pts.length - 1) {
        const mx = (pts[i].x + pts[i + 1].x) / 2;
        const my = (pts[i].y + pts[i + 1].y) / 2;
        ctx.quadraticCurveTo(pts[i].x, pts[i].y, mx, my);
      } else ctx.lineTo(pts[i].x, pts[i].y);
    }
    ctx.stroke();
    ctx.restore();
    ctx.restore();

    // 粒子
    if (isPrimary && chartProgress >= 1) {
      for (let i = 0; i < 6; i++) {
        const t = (time * 0.35 + i * 0.17) % 1;
        const idx = Math.floor(t * (pts.length - 1));
        const frac = t * (pts.length - 1) - idx;
        if (idx >= pts.length - 1) continue;
        const px = pts[idx].x + (pts[idx + 1].x - pts[idx].x) * frac;
        const py = pts[idx].y + (pts[idx + 1].y - pts[idx].y) * frac;
        const pr = 1.2 + Math.sin(time * 4 + i) * 0.6;
        const alpha = 0.25 + Math.sin(time * 3 + i * 1.3) * 0.15;
        ctx.save();
        ctx.beginPath();
        ctx.arc(px, py, pr + 3, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(96,165,250,${alpha * 0.12})`;
        ctx.fill();
        ctx.beginPath();
        ctx.arc(px, py, pr, 0, Math.PI * 2);
        ctx.fillStyle = `rgba(180,210,255,${alpha})`;
        ctx.fill();
        ctx.restore();
      }
    }

    // 节点
    if (chartProgress >= 1) {
      const nodeIdxs = isPrimary
        ? [
            0,
            Math.floor(data.length * 0.25),
            Math.floor(data.length * 0.5),
            Math.floor(data.length * 0.75),
            data.length - 1,
          ]
        : [0, Math.floor(data.length * 0.5), data.length - 1];
      nodeIdxs.forEach((idx) => {
        if (idx >= data.length || idx >= pts.length) return;
        const p = pts[idx];
        const isEnd = idx === data.length - 1;
        if (isEnd && isPrimary) {
          const pulseR = 7 + Math.sin(time * 3.5) * 2.5;
          ctx.beginPath();
          ctx.arc(p.x, p.y, pulseR, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(192,132,252,${0.12 + Math.sin(time * 3.5) * 0.06})`;
          ctx.lineWidth = 1;
          ctx.stroke();
          ctx.beginPath();
          ctx.arc(p.x, p.y, pulseR + 5, 0, Math.PI * 2);
          ctx.strokeStyle = `rgba(192,132,252,${0.04 + Math.sin(time * 2.5) * 0.02})`;
          ctx.lineWidth = 0.7;
          ctx.stroke();
        }
        const br = isEnd ? 3.5 : 2;
        const bg = ctx.createRadialGradient(
          p.x - br * 0.3,
          p.y - br * 0.3,
          0,
          p.x,
          p.y,
          br,
        );
        bg.addColorStop(0, "#ffffff");
        bg.addColorStop(0.4, nodeColor);
        bg.addColorStop(1, "rgba(0,0,0,.3)");
        ctx.beginPath();
        ctx.arc(p.x, p.y, br, 0, Math.PI * 2);
        ctx.fillStyle = bg;
        ctx.fill();
      });

      if (isPrimary) {
        const ep = pts[pts.length - 1];
        const lp = data[data.length - 1],
          pp = data[data.length - 2];
        const chg = lp - pp,
          chgP = (chg / pp) * 100,
          isUp = chg >= 0;
        const ly = ep.y - 18 - Math.sin(time * 2) * 1.5;
        ctx.save();
        const lblW = 58,
          lblH = 28,
          lblX = ep.x - lblW / 2,
          lblY = ly - 8;
        ctx.fillStyle = "rgba(10,18,36,.88)";
        ctx.strokeStyle = "rgba(148,163,184,.12)";
        ctx.lineWidth = 0.7;
        ctx.beginPath();
        ctx.roundRect(lblX, lblY, lblW, lblH, 5);
        ctx.fill();
        ctx.stroke();
        ctx.font = "bold 12px 'SF Mono','Cascadia Code',monospace";
        ctx.textAlign = "center";
        ctx.fillStyle = "#f1f5f9";
        ctx.fillText(`$${lp.toFixed(1)}`, ep.x, ly + 2);
        ctx.font = "bold 9px 'SF Mono','Cascadia Code',monospace";
        ctx.fillStyle = isUp ? "#34d399" : "#f87171";
        ctx.fillText(`${isUp ? "+" : ""}${chgP.toFixed(1)}%`, ep.x, ly + 13);
        ctx.restore();
      }
    }
  }

  // 预测分界
  if (chartProgress >= 0.6) {
    const divIdx = OIL_DATA.actual.length - 1;
    if (divIdx < drawN && divIdx < brentAll.length) {
      const dx = toX(divIdx, brentAll.length);
      ctx.save();
      const bandW = 18;
      const bandGrad = ctx.createLinearGradient(dx - bandW, 0, dx + bandW, 0);
      bandGrad.addColorStop(0, "transparent");
      bandGrad.addColorStop(0.5, "rgba(139,92,246,.05)");
      bandGrad.addColorStop(1, "transparent");
      ctx.fillStyle = bandGrad;
      ctx.fillRect(dx - bandW, pad.top, bandW * 2, chartH);
      ctx.setLineDash([3, 4]);
      ctx.strokeStyle = "rgba(139,92,246,.15)";
      ctx.lineWidth = 0.7;
      ctx.beginPath();
      ctx.moveTo(dx, pad.top);
      ctx.lineTo(dx, H - pad.bottom);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.font = "bold 8px 'SF Mono','Cascadia Code',monospace";
      ctx.textAlign = "center";
      ctx.fillStyle = "rgba(139,92,246,.35)";
      ctx.fillText("FORECAST", dx, pad.top - 6);
      ctx.restore();
    }
  }

  // WTI
  drawLine(
    wtiAll,
    wtiDrawN,
    "rgba(251,191,36,.40)",
    "rgba(251,191,36,.03)",
    "rgba(251,191,36,.03)",
    "rgba(251,191,36,.001)",
    1.4,
    false,
    "#fbbf24",
  );
  // Brent
  drawLine(
    brentAll,
    drawN,
    "#60a5fa",
    "rgba(96,165,250,.08)",
    "rgba(96,165,250,.07)",
    "rgba(96,165,250,.001)",
    2.2,
    true,
    "#60a5fa",
  );

  // 图例
  if (chartProgress >= 1) {
    ctx.save();
    const legX = W - pad.right + 8,
      legY = pad.top + 5;
    ctx.beginPath();
    ctx.moveTo(legX, legY);
    ctx.lineTo(legX + 14, legY);
    ctx.strokeStyle = "#60a5fa";
    ctx.lineWidth = 2.2;
    ctx.lineCap = "round";
    ctx.stroke();
    ctx.font = "bold 8px 'SF Mono','Cascadia Code',monospace";
    ctx.fillStyle = "rgba(226,232,240,.4)";
    ctx.textAlign = "left";
    ctx.fillText("BRENT", legX, legY + 13);
    ctx.beginPath();
    ctx.moveTo(legX, legY + 24);
    ctx.lineTo(legX + 14, legY + 24);
    ctx.strokeStyle = "rgba(251,191,36,.55)";
    ctx.lineWidth = 1.4;
    ctx.stroke();
    ctx.fillStyle = "rgba(226,232,240,.25)";
    ctx.fillText("WTI", legX, legY + 37);
    ctx.restore();
  }

  // 右侧价格条
  if (chartProgress >= 1) {
    ctx.save();
    const barX = W - pad.right + 5;
    const curPrice = brentAll[brentAll.length - 1];
    const curY = pad.top + ((maxV - curPrice) / range) * chartH;
    ctx.fillStyle = "rgba(148,163,184,.025)";
    ctx.beginPath();
    ctx.roundRect(barX - 1.5, pad.top, 3, chartH, 1.5);
    ctx.fill();
    ctx.beginPath();
    ctx.arc(barX, curY, 2.5, 0, Math.PI * 2);
    ctx.fillStyle = "#c084fc";
    ctx.fill();
    ctx.beginPath();
    ctx.arc(barX, curY, 4.5, 0, Math.PI * 2);
    ctx.strokeStyle = "rgba(192,132,252,.25)";
    ctx.lineWidth = 0.8;
    ctx.stroke();
    ctx.font = "bold 9px 'SF Mono','Cascadia Code',monospace";
    ctx.textAlign = "left";
    ctx.fillStyle = "rgba(192,132,252,.4)";
    ctx.fillText(`$${curPrice.toFixed(1)}`, barX + 9, curY + 3);
    ctx.restore();
  }
}

function animateChart() {
  if (chartProgress < 1) {
    chartProgress += 0.018;
    if (chartProgress > 1) chartProgress = 1;
    drawMainChart();
    chartAnimId = requestAnimationFrame(animateChart);
  } else {
    chartAnimId = requestAnimationFrame(function tick() {
      drawMainChart();
      chartAnimId = requestAnimationFrame(tick);
    });
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
  initParticles();
  // AI分析进度动画
  let aiTimer = setInterval(() => {
    if (aiProgress.value < 100)
      aiProgress.value = Math.min(
        100,
        aiProgress.value + Math.random() * 3 + 1,
      );
    else clearInterval(aiTimer);
  }, 120);
});
onBeforeUnmount(() => {
  clearInterval(clockTimer);
  if (chartAnimId !== null) cancelAnimationFrame(chartAnimId);
  if (particleAnimId !== null) cancelAnimationFrame(particleAnimId);
});
</script>

<style scoped>
/* ================================================================
   LANDING — 大宗绿测
   Style: 深邃暗色 · 有机布局 · 多层背景
   ================================================================ */

.landing {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #050a14;
  color: #e2e8f0;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "PingFang SC",
    sans-serif;
}

/* ─── 背景层 ─── */
.bg-layer {
  position: fixed;
  inset: 0;
  z-index: 0;
  pointer-events: none;
}
.noise-svg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  opacity: 0.04;
}
.bg-base {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(
      ellipse 80% 60% at 70% 20%,
      rgba(30, 64, 175, 0.18) 0%,
      transparent 70%
    ),
    radial-gradient(
      ellipse 60% 50% at 20% 80%,
      rgba(6, 182, 212, 0.1) 0%,
      transparent 65%
    ),
    radial-gradient(
      ellipse 50% 40% at 50% 50%,
      rgba(15, 23, 42, 0.9) 0%,
      #050a14 100%
    );
}
.bg-rays {
  position: absolute;
  inset: 0;
  background:
    linear-gradient(135deg, rgba(59, 130, 246, 0.04) 0%, transparent 40%),
    linear-gradient(225deg, rgba(139, 92, 246, 0.03) 0%, transparent 35%);
}
.bg-orb {
  position: absolute;
  border-radius: 50%;
  filter: blur(80px);
}
.bg-orb--a {
  width: 600px;
  height: 600px;
  top: -20%;
  right: -5%;
  background: radial-gradient(
    circle,
    rgba(30, 64, 175, 0.22) 0%,
    transparent 70%
  );
  animation: orbFloat1 25s ease-in-out infinite alternate;
}
.bg-orb--b {
  width: 450px;
  height: 450px;
  bottom: -15%;
  left: -8%;
  background: radial-gradient(
    circle,
    rgba(6, 182, 212, 0.14) 0%,
    transparent 65%
  );
  animation: orbFloat2 30s ease-in-out infinite alternate;
}
.bg-orb--c {
  width: 300px;
  height: 300px;
  top: 55%;
  right: 15%;
  background: radial-gradient(
    circle,
    rgba(245, 158, 11, 0.08) 0%,
    transparent 60%
  );
  animation: orbFloat3 20s ease-in-out infinite alternate;
}
.bg-orb--d {
  width: 250px;
  height: 250px;
  top: 35%;
  left: 25%;
  background: radial-gradient(
    circle,
    rgba(16, 185, 129, 0.06) 0%,
    transparent 55%
  );
  animation: orbFloat4 22s ease-in-out infinite alternate;
}
.bg-orb--e {
  width: 200px;
  height: 200px;
  bottom: 20%;
  right: 35%;
  background: radial-gradient(
    circle,
    rgba(244, 114, 182, 0.05) 0%,
    transparent 55%
  );
  animation: orbFloat5 18s ease-in-out infinite alternate;
}
@keyframes orbFloat1 {
  to {
    transform: translate(-40px, 30px) scale(1.06);
  }
}
@keyframes orbFloat2 {
  to {
    transform: translate(50px, -25px) scale(1.08);
  }
}
@keyframes orbFloat3 {
  to {
    transform: translate(-25px, -30px) scale(1.12);
  }
}
@keyframes orbFloat4 {
  to {
    transform: translate(30px, 15px) scale(0.92);
  }
}
@keyframes orbFloat5 {
  to {
    transform: translate(15px, 20px) scale(1.15);
  }
}

.bg-grid {
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(148, 163, 184, 0.02) 1px, transparent 1px),
    linear-gradient(90deg, rgba(148, 163, 184, 0.02) 1px, transparent 1px);
  background-size: 60px 60px;
  mask-image: radial-gradient(
    ellipse 70% 60% at 55% 45%,
    black 20%,
    transparent 80%
  );
  -webkit-mask-image: radial-gradient(
    ellipse 70% 60% at 55% 45%,
    black 20%,
    transparent 80%
  );
}

.particle-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

/* ─── 主布局 ─── */
.main-grid {
  position: relative;
  z-index: 1;
  display: grid;
  grid-template-columns: 38fr 62fr;
  min-height: 100vh;
  max-width: 1600px;
  margin: 0 auto;
  gap: 0;
}

/* ─── 左侧品牌 ─── */
.brand-col {
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 48px 32px 48px 36%;
}
.top-mark {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
  animation: fadeUp 0.5s ease both;
}
.mark-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #3b82f6;
  box-shadow:
    0 0 12px rgba(59, 130, 246, 0.6),
    0 0 24px rgba(59, 130, 246, 0.2);
}
.mark-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 3.5px;
  color: rgba(148, 163, 184, 0.45);
  text-transform: uppercase;
}
.hero-title {
  margin: 0 0 18px;
  animation: fadeUp 0.5s ease 0.08s both;
}
.title-line {
  display: block;
  font-size: clamp(36px, 4vw, 56px);
  font-weight: 800;
  letter-spacing: 4px;
  line-height: 1.15;
  background: linear-gradient(
    135deg,
    #f1f5f9 0%,
    #94a3b8 25%,
    #60a5fa 55%,
    #a78bfa 80%,
    #f472b6 100%
  );
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
}
.hero-desc {
  margin: 0 0 32px;
  font-size: 15px;
  line-height: 1.85;
  color: rgba(148, 163, 184, 0.5);
  max-width: 420px;
  animation: fadeUp 0.5s ease 0.16s both;
}

/* 功能列表 */
.feat-list {
  list-style: none;
  margin: 0 0 34px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}
.feat-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 12px 16px;
  border-radius: 12px;
  border: 1px solid transparent;
  background: transparent;
  cursor: default;
  opacity: 0;
  animation: fadeUp 0.5s cubic-bezier(0.22, 1, 0.36, 1) forwards;
  transition: all 0.3s ease;
}
.feat--1 {
  animation-delay: 0.26s;
}
.feat--2 {
  animation-delay: 0.32s;
}
.feat--3 {
  animation-delay: 0.38s;
}
.feat--4 {
  animation-delay: 0.44s;
}
.feat-item:hover {
  border-color: rgba(59, 130, 246, 0.1);
  background: rgba(59, 130, 246, 0.04);
  transform: translateX(4px);
}
.feat-num {
  font-size: 11px;
  font-weight: 800;
  min-width: 26px;
  color: rgba(96, 165, 250, 0.35);
  transition: color 0.3s;
}
.feat-item:hover .feat-num {
  color: rgba(96, 165, 250, 0.6);
}
.feat-body {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.feat-body strong {
  font-size: 15px;
  font-weight: 600;
  color: #cbd5e1;
}
.feat-body span {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.38);
  line-height: 1.55;
}

/* CTA */
.cta-row {
  display: flex;
  align-items: center;
  gap: 14px;
  animation: fadeUp 0.5s ease 0.52s both;
}
.cta-primary {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  padding: 15px 32px;
  border: none;
  border-radius: 12px;
  background: linear-gradient(135deg, #3b82f6, #6366f1);
  color: #fff;
  font-size: 15px;
  font-weight: 700;
  letter-spacing: 0.5px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow:
    0 4px 20px rgba(59, 99, 235, 0.3),
    0 0 30px -10px rgba(99, 102, 241, 0.15),
    inset 0 1px 0 rgba(255, 255, 255, 0.12);
}
.cta-primary:hover {
  transform: translateY(-2px);
  box-shadow:
    0 8px 30px rgba(59, 99, 235, 0.4),
    0 0 40px -10px rgba(99, 102, 241, 0.25);
}
.cta-primary svg {
  transition: transform 0.25s;
}
.cta-primary:hover svg {
  transform: translateX(3px);
}
.cta-secondary {
  padding: 15px 26px;
  border: 1px solid rgba(148, 163, 184, 0.12);
  border-radius: 12px;
  background: transparent;
  color: rgba(148, 163, 184, 0.5);
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
}
.cta-secondary:hover {
  border-color: rgba(148, 163, 184, 0.25);
  color: #cbd5e1;
  background: rgba(148, 163, 184, 0.04);
}

/* 状态栏 */
.status-bar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding-top: 28px;
  font-size: 11px;
  font-weight: 500;
  letter-spacing: 1.2px;
  color: rgba(148, 163, 184, 0.25);
  animation: fadeUp 0.5s ease 0.6s both;
}
.status-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #34d399;
  animation: blink 2s ease-in-out infinite;
}
.divider {
  opacity: 0.2;
}
@keyframes blink {
  0%,
  100% {
    opacity: 1;
    box-shadow: 0 0 0 0 rgba(52, 211, 153, 0.4);
  }
  50% {
    opacity: 0.3;
    box-shadow: 0 0 0 5px rgba(52, 211, 153, 0);
  }
}
@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* ═══ 右侧卡片区域 ═══ */
.viz-col {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 40px 32px 20px;
  overflow: hidden;
  height: 100%;
  perspective: 1000px;
}

/* ─── 不规则卡片布局 ─── */
.card-scatter {
  position: relative;
  z-index: 2;
  display: grid;
  grid-template-columns: 1fr 1fr;
  grid-template-rows: auto auto;
  gap: 14px;
  width: 100%;
  max-width: 620px;
}

/* ─── 卡片通用 ─── */
.data-card {
  position: relative;
  overflow: hidden;
  cursor: default;
  border-radius: 16px;
  background: rgba(10, 18, 36, 0.6);
  border: 1px solid rgba(255, 255, 255, 0.04);
  backdrop-filter: blur(20px) saturate(1.2);
  box-shadow:
    0 8px 32px -8px rgba(0, 0, 0, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.03);
  transition:
    transform 0.15s ease-out,
    box-shadow 0.3s,
    border-color 0.3s;
  transform-style: preserve-3d;
}

/* ─── 主图表卡 ─── */
.data-card--hero {
  grid-column: 1 / -1;
  background:
    linear-gradient(
      135deg,
      rgba(59, 130, 246, 0.05) 0%,
      rgba(139, 92, 246, 0.02) 40%,
      transparent 70%
    ),
    rgba(10, 18, 36, 0.65);
  border-color: rgba(59, 130, 246, 0.06);
  border-radius: 18px;
}
.data-card--hero:hover {
  border-color: rgba(99, 102, 246, 0.14);
  box-shadow:
    0 20px 60px -12px rgba(0, 0, 0, 0.5),
    0 0 50px -15px rgba(99, 102, 246, 0.08);
}
.dc-head {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 18px 20px 0;
}
.dc-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.15em;
  padding: 3px 8px;
  border-radius: 5px;
  text-transform: uppercase;
  color: #c084fc;
  background: rgba(139, 92, 246, 0.08);
  border: 1px solid rgba(139, 92, 246, 0.15);
}
.dc-sub {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.4);
}
.dc-chart {
  display: block;
  width: 100% !important;
  height: auto !important;
  max-height: 300px;
  padding: 0 4px;
}
.dc-foot {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 20px 16px;
  font-size: 11.5px;
  color: rgba(148, 163, 184, 0.4);
}
.dc-foot strong {
  color: #a78bfa;
  font-size: 13.5px;
}
.dc-live {
  display: flex;
  align-items: center;
  gap: 6px;
}
.live-dot {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: #c084fc;
  animation: pulseLive 2s ease infinite;
  box-shadow: 0 0 6px rgba(192, 132, 252, 0.4);
}
@keyframes pulseLive {
  0%,
  100% {
    opacity: 1;
  }
  50% {
    opacity: 0.25;
  }
}

/* ─── 油价卡 — 不等高 ─── */
.data-card--oil {
  grid-row: span 1;
  background: linear-gradient(
    160deg,
    rgba(245, 158, 11, 0.04) 0%,
    rgba(10, 18, 36, 0.6) 60%
  );
  border-color: rgba(245, 158, 11, 0.06);
  min-height: 150px;
}
.data-card--oil:hover {
  border-color: rgba(245, 158, 11, 0.15);
  box-shadow:
    0 12px 36px -6px rgba(0, 0, 0, 0.45),
    0 0 20px -8px rgba(245, 158, 11, 0.08);
}

/* ─── 新能源卡 ─── */
.data-card--energy {
  background: linear-gradient(
    160deg,
    rgba(16, 185, 129, 0.04) 0%,
    rgba(10, 18, 36, 0.6) 60%
  );
  border-color: rgba(16, 185, 129, 0.06);
  min-height: 140px;
}
.data-card--energy:hover {
  border-color: rgba(16, 185, 129, 0.15);
  box-shadow:
    0 12px 36px -6px rgba(0, 0, 0, 0.45),
    0 0 20px -8px rgba(16, 185, 129, 0.08);
}

/* ─── 债券卡 ─── */
.data-card--bond {
  background: linear-gradient(
    160deg,
    rgba(244, 114, 182, 0.04) 0%,
    rgba(10, 18, 36, 0.6) 60%
  );
  border-color: rgba(244, 114, 182, 0.06);
  min-height: 140px;
}
.data-card--bond:hover {
  border-color: rgba(244, 114, 182, 0.15);
  box-shadow:
    0 12px 36px -6px rgba(0, 0, 0, 0.45),
    0 0 20px -8px rgba(244, 114, 182, 0.08);
}

/* ─── AI分析卡 ─── */
.data-card--ai {
  background: linear-gradient(
    160deg,
    rgba(139, 92, 246, 0.05) 0%,
    rgba(10, 18, 36, 0.6) 60%
  );
  border-color: rgba(139, 92, 246, 0.06);
  min-height: 140px;
}
.data-card--ai:hover {
  border-color: rgba(139, 92, 246, 0.15);
  box-shadow:
    0 12px 36px -6px rgba(0, 0, 0, 0.45),
    0 0 20px -8px rgba(139, 92, 246, 0.08);
}

/* 卡片内容 */
.dc-content {
  padding: 16px 18px;
  position: relative;
  z-index: 2;
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.dc-head-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 3px;
}
.dc-label {
  display: block;
  font-size: 10px;
  font-weight: 600;
  letter-spacing: 0.15em;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.4);
}
.dc-price-row {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.dc-big {
  font-size: 30px;
  font-weight: 800;
  color: #f1f5f9;
  line-height: 1;
  letter-spacing: -0.03em;
}
.dc-chg {
  display: inline-block;
  font-size: 12.5px;
  font-weight: 700;
  padding: 3px 7px;
  border-radius: 5px;
}
.dc-chg--up {
  color: #f59e0b;
  background: rgba(245, 158, 11, 0.08);
}
.dc-spark {
  display: block;
  width: 100% !important;
  opacity: 0.65;
}

/* LIVE / 状态徽标 */
.dc-live-badge {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: rgba(192, 132, 252, 0.55);
}
.dc-badge {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 0.08em;
  padding: 3px 8px;
  border-radius: 5px;
}
.dc-badge--up {
  color: #34d399;
  background: rgba(16, 185, 129, 0.08);
}
.dc-badge--stable {
  color: rgba(148, 163, 184, 0.5);
  background: rgba(148, 163, 184, 0.06);
}

/* 底部元数据行 */
.dc-meta-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 10px;
  color: rgba(148, 163, 184, 0.32);
  letter-spacing: 0.03em;
}

/* 迷你折线图（内联SVG） */
.dc-spark-inline {
  margin-top: 3px;
  opacity: 0.5;
}
.dc-spark-inline svg {
  display: block;
  width: 100%;
  height: 22px;
}

/* 数据行 */
.dc-rows {
  display: flex;
  flex-direction: column;
  gap: 7px;
  margin-top: 3px;
}
.dc-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 8px;
  font-size: 12px;
  color: rgba(148, 163, 184, 0.5);
}
.dc-row em {
  font-style: normal;
  font-weight: 700;
  color: #e2e8f0;
  font-size: 14px;
}
.dc-row small {
  font-size: 10px;
  font-weight: 600;
  padding: 2px 6px;
  border-radius: 4px;
}
.dc-up {
  color: #34d399;
  background: rgba(16, 185, 129, 0.08);
}
.dc-down {
  color: #f87171;
  background: rgba(248, 113, 113, 0.08);
}
.dc-rate-down {
  color: #34d399;
  background: rgba(16, 185, 129, 0.06);
  font-size: 9.5px !important;
}
.dc-rate-flat {
  color: rgba(148, 163, 184, 0.35);
  background: rgba(148, 163, 184, 0.05);
  font-size: 9.5px !important;
}

/* 利率进度条 */
.dc-rate-bar {
  margin-top: 3px;
}
.rate-bar-track {
  height: 4px;
  border-radius: 2px;
  background: rgba(244, 114, 182, 0.06);
  overflow: hidden;
}
.rate-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(
    90deg,
    rgba(244, 114, 182, 0.3),
    rgba(244, 114, 182, 0.08)
  );
  transition: width 1s ease;
}

/* ─── AI分析卡内容 ─── */
.dc-ai-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  margin: 3px 0;
}
.ai-metric {
  display: flex;
  flex-direction: column;
  gap: 2px;
}
.ai-metric-label {
  font-size: 10px;
  color: rgba(148, 163, 184, 0.35);
  letter-spacing: 0.05em;
}
.ai-metric-val {
  font-size: 16px;
  font-weight: 800;
  color: #e2e8f0;
  letter-spacing: -0.02em;
}

.dc-signals {
  display: flex;
  flex-direction: column;
  gap: 5px;
}
.signal-item {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 12px;
  color: rgba(148, 163, 184, 0.55);
}
.signal-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.signal-dot--buy {
  background: #34d399;
  box-shadow: 0 0 6px rgba(52, 211, 153, 0.3);
}
.signal-dot--hold {
  background: #fbbf24;
  box-shadow: 0 0 6px rgba(251, 191, 36, 0.2);
}

.dc-ai-progress {
  margin-top: 3px;
}
.ai-bar-track {
  height: 4px;
  border-radius: 2px;
  background: rgba(139, 92, 246, 0.06);
  overflow: hidden;
}
.ai-bar-fill {
  height: 100%;
  border-radius: 2px;
  background: linear-gradient(
    90deg,
    rgba(139, 92, 246, 0.4),
    rgba(192, 132, 252, 0.15)
  );
  transition: width 0.3s ease;
}
.ai-bar-label {
  font-size: 9px;
  color: rgba(148, 163, 184, 0.28);
  letter-spacing: 0.05em;
  display: block;
  margin-top: 3px;
}

.live-dot--green {
  background: #34d399 !important;
  box-shadow: 0 0 6px rgba(52, 211, 153, 0.4) !important;
}

/* 鼠标光晕 */
.dc-spotlight {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border-radius: inherit;
  z-index: 0;
  opacity: 0;
  transition: opacity 0.3s;
}

/* ═══ 响应式 ═══ */
@media (max-width: 1400px) {
  .card-scatter {
    max-width: 560px;
  }
  .brand-col {
    padding: 48px 24px 48px 6%;
  }
}
@media (max-width: 1100px) {
  .main-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }
  .brand-col {
    padding: 40px 32px 32px;
  }
  .viz-col {
    min-height: auto;
    padding: 0 32px 40px;
  }
  .card-scatter {
    max-width: 100%;
  }
  .data-card--hero {
    order: -1;
  }
}
@media (max-width: 768px) {
  .brand-col {
    padding: 28px 20px 24px;
  }
  .title-line {
    font-size: clamp(28px, 6vw, 40px);
    letter-spacing: 2px;
  }
  .hero-desc {
    font-size: 13px;
  }
  .feat-body strong {
    font-size: 14px;
  }
  .feat-body span {
    font-size: 11.5px;
  }
  .cta-row {
    gap: 10px;
  }
  .cta-primary {
    padding: 13px 24px;
    font-size: 14px;
  }
  .cta-secondary {
    padding: 13px 20px;
    font-size: 13px;
  }
  .viz-col {
    padding: 0 16px 32px;
  }
  .card-scatter {
    gap: 10px;
  }
}
@media (max-width: 540px) {
  .brand-col {
    padding: 20px 14px 18px;
  }
  .title-line {
    letter-spacing: 1.5px;
  }
  .cta-row {
    flex-direction: column;
  }
  .card-scatter {
    grid-template-columns: 1fr;
  }
  .data-card--hero {
    order: -1;
  }
  .viz-col {
    padding: 0 12px 24px;
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
