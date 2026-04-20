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
          <canvas
            ref="priceChartRef"
            class="dc-spark"
            width="160"
            height="36"
            aria-hidden="true"
          ></canvas>
        </div>

        <div class="dc dc--stock">
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
            <div class="ai-bar">
              <div class="ai-fill" style="width: 94.7%"></div>
            </div>
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
          <canvas
            ref="chartCanvasRef"
            class="chart-canvas"
            width="460"
            height="200"
            aria-hidden="true"
          ></canvas>
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
    else ctx.lineTo(px, py);
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

// ===== 主折线图 — 真实油价模拟数据 + 双色渐变曲线 + 置信区间 + 事件标注 =====
let chartAnimId: number | null = null;
let chartProgress = 0;

/*
 * 数据设计 — 模拟布伦特原油 30日走势（含预测段）
 *
 * 阶段划分：
 *   [0~17] 历史数据段（实线）：有真实涨跌震荡
 *   [18~29] GRU模型预测段（虚线发光）：带置信区间
 *
 * 价格故事线：
 *   D1-5:  稳定在 $81~83，小幅震荡（市场观望）
 *   D6-9:  急跌到 $72（OPEC+意外增产消息）
 *   D10-14: 强力反弹至 $84（地缘风险升温、库存下降）
 *   D15-17: 回调至 $80（获利了结）
 *   D18-21: 预测缓升 $80→$85（需求预期回暖）
 *   D22-25: 预测横盘震荡 $83~$86（多空博弈）
 *   D26-29: 预测温和上行 $85→$88（季节性需求）
 */

const OIL_DATA = {
  /* 原始价格数据（美元/桶），共30个点 */
  prices: [
    82.4, 81.7, 83.1, 82.5, 80.9,     // D1-5: 稳定微跌
    76.3, 73.8, 71.2, 72.6, 74.8,    // D6-10: 急跌后企稳反弹开始
    77.5, 80.1, 82.8, 84.3, 83.0,    // D11-15: 强力反弹
    81.2, 80.5, 79.8,                // D16-18: 回调
    // —— GRU 预测值 ——
    81.5, 82.8, 84.2, 85.0,           // D19-22: 预测缓升
    84.3, 85.7, 86.2, 84.8,           // D23-26: 预测震荡
    85.9, 87.1, 88.0, 87.3,           // D27-29: 温和上行
  ],
  /* 关键事件标注 */
  events: [
    { idx: 6, label: "OPEC+增产", type: "bear" as const },       // 跳水起点
    { idx: 8, label: "$71.2 低点", type: "low" as const },        // 阶段最低
    { idx: 13, label: "$84.3 高点", type: "high" as const },       // 反弹峰值
    { idx: 17, label: "PREDICT →", type: "predict" as const },    // 分界
  ],
  predictStartIdx: 18,
};

function drawMainChart() {
  const c = chartCanvasRef.value; if (!c) return;
  const ctx = c.getContext("2d"); if (!ctx) return;

  const dpr = window.devicePixelRatio || 1;
  const w = 480, h = 220;
  c.width = w * dpr; c.height = h * dpr;
  c.style.width = w + "px"; c.style.height = h + "px";
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);

  const pts = OIL_DATA.prices;
  const n = pts.length;
  const minV = Math.min(...pts) - 4;
  const maxV = Math.max(...pts) + 4;
  const range = maxV - minV || 1;

  const padL = 48, padR = 20, padT = 28, padB = 34;
  const cw = w - padL - padR, ch = h - padT - padB;

  ctx.clearRect(0, 0, w, h);

  // ── 坐标转换 ──
  function px(i: number) { return padL + (i / (n - 1)) * cw; }
  function py(v: number) { return padT + ch - ((v - minV) / range) * ch; }

  // ── Catmull-Rom → Bezier 控制点 ──
  function getCP(i: number) {
    const p0 = { x: px(Math.max(0,i-1)), y: py(pts[Math.max(0,i-1)]) };
    const p1 = { x: px(i),           y: py(pts[i]) };
    const p2 = { x: px(Math.min(n-1,i+1)), y: py(pts[Math.min(n-1,i+1)]) };
    const p3 = { x: px(Math.min(n-1,i+2)), y: py(pts[Math.min(n-1,i+2)]) };
    const t = 0.32;
    return {
      cp1x: p1.x + (p2.x - p0.x) * t, cp1y: p1.y + (p2.y - p0.y) * t,
      cp2x: p2.x - (p3.x - p1.x) * t, cp2y: p2.y - (p3.y - p1.y) * t,
    };
  }

  // ── 构建贝塞尔路径 ──
  function buildPath(endIdx: number): Path2D {
    const path = new Path2D();
    path.moveTo(px(0), py(pts[0]));
    for (let i = 0; i < endIdx - 1; i++) {
      const cp = getCP(i);
      path.bezierCurveTo(cp.cp1x, cp.cp1y, cp.cp2x, cp.cp2y, px(i+1), py(pts[i+1]));
    }
    return path;
  }

  // ═══ 第1层：背景网格 & 轴标签 ═══
  ctx.strokeStyle = "rgba(255,255,255,.034)"; ctx.lineWidth = 0.5;
  for (let g = 0; g <= 4; g++) {
    const gy = padT + ch * (g / 4);
    ctx.beginPath(); ctx.moveTo(padL, gy); ctx.lineTo(w - padR, gy); ctx.stroke();
  }
  // Y轴
  ctx.fillStyle = "rgba(148,163,184,.16)"; ctx.font = "9px system-ui"; ctx.textAlign = "right";
  ["$92","$84","$76","$68","$60"].forEach((lbl, i) => { ctx.fillText(lbl, padL - 6, padT + ch*(i/4)+3); });
  // X轴
  ctx.fillStyle = "rgba(148,163,184,.12)"; ctx.textAlign = "center";
  ["03/20","03/24","03/28","04/01","04/05","04/09","04/13","04/17"].forEach((d, i) => {
    ctx.fillText(d, padL+(i/7)*cw, h-6);
  });

  const drawN = Math.max(2, Math.floor(chartProgress * n));

  // ═══ 第2层：预测置信区间阴影带 ═══
  if (drawN > OIL_DATA.predictStartIdx) {
    const ps = OIL_DATA.predictStartIdx;
    const band = new Path2D();
    band.moveTo(px(ps), py(pts[ps]+1.5));
    for (let i=ps; i<drawN-1; i++) {
      const off = 1.5+(i-ps)*0.25;
      const cp=getCP(i);
      band.bezierCurveTo(cp.cp1x,py(pts[i])-off,cp.cp2x,py(pts[i+1])-off,px(i+1),py(pts[i+1])-off);
    }
    for (let i=drawN-1;i>=ps;i--) {
      const off=1.5+(i-ps)*0.25;
      if(i===drawN-1) band.lineTo(px(i),py(pts[i])+off);
      else{const cp=getCP(i-1);band.bezierCurveTo(cp.cp2x,py(pts[i])+off,cp.cp1x,py(pts[i-1])+off,px(i-1),py(pts[i-1])+off);}
    }
    band.closePath();
    const bg=ctx.createLinearGradient(0,padT,0,h-padB);
    bg.addColorStop(0,"rgba(56,189,248,.08)");bg.addColorStop(.5,"rgba(56,189,248,.04)");bg.addColorStop(1,"rgba(56,189,248,.01)");
    ctx.fillStyle=bg;ctx.fill(band);
  }

  // ═══ 第3层：面积填充（历史绿→预测蓝） ═══
  if (drawN >= 2) {
    const ap=new Path2D();ap.moveTo(px(0),h-padB);ap.lineTo(px(0),py(pts[0]));
    for(let i=0;i<drawN-1;i++){const cp=getCP(i);ap.bezierCurveTo(cp.cp1x,cp.cp1y,cp.cp2x,cp.cp2y,px(i+1),py(pts[i+1]));}
    ap.lineTo(px(drawN-1),h-padB);ap.closePath();
    const ag=ctx.createLinearGradient(padL,0,padL+cw*.65,0);
    ag.addColorStop(0,"rgba(52,211,153,.12)");ag.addColorStop(OIL_DATA.predictStartIdx/n,"rgba(52,211,153,.06)");
    ag.addColorStop(.75,"rgba(56,189,248,.06)");ag.addColorStop(1,"rgba(56,189,248,.01)");
    ctx.fillStyle=ag;ctx.fill(ap);
  }

  // ═══ 第4层：主曲线（五色渐变 + 发光） ═══
  const mainPath = buildPath(drawN);
  // 发光底层
  ctx.save();ctx.strokeStyle="rgba(52,211,153,.14)";ctx.lineWidth=8;ctx.lineCap="round";ctx.lineJoin="round";ctx.stroke(mainPath);ctx.restore();
  // 主线条
  const lg=ctx.createLinearGradient(padL,0,padL+cw,0);
  lg.addColorStop(0,"#34d399");lg.addColorStop(.35,"#2dd4bf");lg.addColorStop(.58,"#38bdf8");
  lg.addColorStop(.82,"#60a5fa");lg.addColorStop(1,"#a78bfa");
  ctx.strokeStyle=lg;ctx.lineWidth=2.5;ctx.lineCap="round";ctx.lineJoin="round";ctx.stroke(mainPath);

  // ═══ 第5层：事件标注 ═══
  if(chartProgress>=1){
    const time=Date.now()/1000;
    OIL_DATA.events.forEach((ev)=>{
      if(ev.idx>=n)return;
      const ex=px(ev.idx),ey=py(pts[ev.idx]);
      // 虚线
      ctx.save();ctx.setLineDash([3,4]);
      ctx.strokeStyle=ev.type==="bear"?"rgba(248,113,113,.2)":ev.type==="low"?"rgba(52,211,153,.2)":ev.type==="high"?"rgba(250,204,21,.25)":"rgba(167,139,250,.3)";
      ctx.lineWidth=.8;ctx.beginPath();ctx.moveTo(ex,ey);ctx.lineTo(ex,h-padB);ctx.stroke();ctx.restore();
      // 圆点
      ctx.beginPath();ctx.arc(ex,ey,ev.type==="predict"?4.5:3.5,0,Math.PI*2);
      const dc:{[k:string]:string}={bear:"#f87171",low:"#34d399",high:"#facc15",predict:"#a78bfa"};
      ctx.fillStyle=dc[ev.type]||"#fff";ctx.fill();
      if(ev.type==="predict"){
        const pr=6+Math.sin(time*3.5)*2.5;
        ctx.beginPath();ctx.arc(ex,ey,pr+3,0,Math.PI*2);
        ctx.strokeStyle=`rgba(167,139,250,${.15+Math.sin(time*3.5)*.1})`;ctx.lineWidth=1;ctx.stroke();
      }
      // 标签文字
      ctx.font=ev.type==="predict"?"bold 9px system-ui":"9px system-ui";
      ctx.textAlign=ev.idx<n*.5?"left":"right";
      const lx=ev.type==="predict"?ex:ex+(ctx.textAlign==="left"?8:-8);
      const ly=ey-(ev.type==="low"?14:-6);
      const tw=ctx.measureText(ev.label).width;
      ctx.fillStyle=ev.type==="bear"?"rgba(248,113,113,.1)":ev.type==="low"?"rgba(52,211,153,.1)":ev.type==="high"?"rgba(250,204,21,.1)":"rgba(167,139,250,.12)";
      const bx=ctx.textAlign==="left"?lx-4:lx-tw-4;
      ctx.fillRect(bx,ly-11,tw+8,15);
      ctx.fillStyle=dc[ev.type]||"rgba(255,255,255,.6)";
      ctx.fillText(ev.label,lx,ly);
    });
  }

  // ═══ 第6层：末端价格卡片（带涨跌幅） ═══
  if(chartProgress>=.97){
    const epX=px(n-1),epY=py(pts[n-1]);
    const time=Date.now()/1000;
    const lp=pts[n-1],pp=pts[n-2];
    const chg=lp-pp,chgP=(chg/pp)*100,isUp=chg>=0;
    // 脉冲环
    const pr=6+Math.sin(time*3)*2.5;
    ctx.beginPath();ctx.arc(epX,epY,pr+5,0,Math.PI*2);
    ctx.strokeStyle=isUp?`rgba(52,211,153,${.12+Math.sin(time*3)*.08})`:`rgba(248,113,113,${.12+Math.sin(time*3)*.08})`;
    ctx.lineWidth=1.2;ctx.stroke();
    // 中圈
    ctx.beginPath();ctx.arc(epX,epY,pr,0,Math.PI*2);
    ctx.fillStyle=isUp?"rgba(52,211,153,.15)":"rgba(248,113,113,.15)";ctx.fill();
    // 实心圆
    const dg=ctx.createRadialGradient(epX,epY,0,epX,epY,5.5);
    dg.addColorStop(0,"#fff");dg.addColorStop(.45,isUp?"#34d399":"#f87171");dg.addColorStop(1,isUp?"#38bdf8":"#fb923c");
    ctx.beginPath();ctx.arc(epX,epY,5.5,0,Math.PI*2);ctx.fillStyle=dg;ctx.fill();
    // 价格卡片
    const cardW=92,cardH=40,cx=epX-cardW/2,cy=epY-cardH-20-Math.sin(time*2)*3;
    ctx.fillStyle="rgba(8,14,22,.88)";
    ctx.strokeStyle=isUp?"rgba(52,211,153,.28)":"rgba(248,113,113,.28)";ctx.lineWidth=.8;
    ctx.beginPath();ctx.roundRect(cx,cy,cardW,cardH,8);ctx.fill();ctx.stroke();
    ctx.font="bold 14px system-ui";ctx.textAlign="center";
    ctx.fillStyle="#f1f5f9";ctx.fillText(`$${lp.toFixed(1)}`,epX,cy+18);
    ctx.font="bold 10px system-ui";
    ctx.fillStyle=isUp?"#34d399":"#f87171";
    ctx.fillText(`${isUp?"+":""}${chg.toFixed(1)} (${isUp?"+":""}${chgP.toFixed(2)}%)`,epX,cy+34);
  }

  // ═══ 第7层：历史/预测分界虚线 ═══
  if(chartProgress>=.65 && OIL_DATA.predictStartIdx<n){
    const dx=px(OIL_DATA.predictStartIdx);
    ctx.save();ctx.setLineDash([4,5]);
    ctx.strokeStyle="rgba(167,139,250,.22)";ctx.lineWidth=.8;
    ctx.beginPath();ctx.moveTo(dx,padT-4);ctx.lineTo(dx,h-padB+4);ctx.stroke();ctx.restore();
    ctx.font="bold 8px system-ui";ctx.textAlign="center";
    ctx.fillStyle="rgba(167,139,250,.45)";ctx.fillText("FORECAST →",dx,padT-8);
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
  animateChart();
  window.addEventListener("mousemove", onMouseMove);
  window.addEventListener("resize", () => {
    drawMainChart();
  });
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
  position: relative;
  min-height: 100vh;
  overflow: hidden;
  background: #080c10;
  color: #e2e8f0;
  font-family:
    -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, "PingFang SC",
    sans-serif;
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
  opacity: 0.035;
  background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 256 256' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='.85' numOctaves='4' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
  background-size: 220px 220px;
}
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(130px);
  opacity: 0.28;
}
.glow--1 {
  width: 600px;
  height: 600px;
  top: -200px;
  right: 5%;
  background: radial-gradient(circle, rgba(16, 120, 90, 0.45), transparent 70%);
  animation: drift1 24s ease-in-out infinite alternate;
}
.glow--2 {
  width: 500px;
  height: 500px;
  bottom: -150px;
  left: 25%;
  background: radial-gradient(
    circle,
    rgba(14, 100, 110, 0.32),
    transparent 70%
  );
  animation: drift2 28s ease-in-out infinite alternate;
}
@keyframes drift1 {
  to {
    transform: translate(-40px, 30px);
  }
}
@keyframes drift2 {
  to {
    transform: translate(50px, -20px);
  }
}

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
  padding: 48px 40px 48px 100px;
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
  background: #34d399;
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.6);
  border-radius: 1px;
}
.mark-text {
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 3px;
  color: rgba(52, 211, 153, 0.6);
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
  background: linear-gradient(135deg, #f1f5f9 0%, #94a3b8 60%, #34d399 100%);
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
  border-color: rgba(255, 255, 255, 0.06);
  background: rgba(52, 211, 153, 0.025);
  transform: translateX(6px);
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
  color: rgba(52, 211, 153, 0.32);
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
  background: linear-gradient(135deg, #059669, #047857);
  color: #fff;
  font-size: 13.5px;
  font-weight: 700;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.22, 1, 0.36, 1);
  box-shadow:
    0 4px 20px rgba(5, 150, 105, 0.4),
    inset 0 1px 0 rgba(255, 255, 255, 0.15);
}
.cta-primary:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 32px rgba(5, 150, 105, 0.5);
}
.cta-primary svg {
  transition: transform 0.25s;
}
.cta-primary:hover svg {
  transform: translateX(4px);
}
.cta-secondary {
  padding: 14px 26px;
  border: 1px solid rgba(255, 255, 255, 0.1);
  border-radius: 10px;
  background: transparent;
  color: rgba(148, 163, 184, 0.55);
  font-size: 13px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.25s;
}
.cta-secondary:hover {
  border-color: rgba(255, 255, 255, 0.2);
  color: #cbd5e1;
  background: rgba(255, 255, 255, 0.04);
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
    opacity: 0.4;
    box-shadow: 0 0 0 5px rgba(52, 211, 153, 0);
  }
}

@keyframes fadeUp {
  from {
    opacity: 0;
    transform: translateY(12px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}

/* ══════════════════════════════════════════════════
   RIGHT: Visualization — Floating Data Cards
   ══════════════════════════════════════════════════ */

.viz-col {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 32px 28px;
  overflow: hidden;
  border-left: 1px solid rgba(255, 255, 255, 0.025);
  height: 100%;
  perspective: 1200px; /* 为子卡片提供 3D 透视空间 */
}
.viz-canvas {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

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
  display: flex;
  flex-direction: column;
  overflow: hidden;

  /* 入场动画：从下方淡入 + 微缩放 */
  opacity: 0;
  animation: cardEnter 0.65s cubic-bezier(0.22, 1, 0.36, 1) forwards;

  transition:
    transform 0.4s cubic-bezier(0.22, 1, 0.36, 1),
    box-shadow 0.4s cubic-bezier(0.22, 1, 0.36, 1),
    border-color 0.4s ease;
}
@keyframes cardEnter {
  from {
    opacity: 0;
    transform: translateY(24px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: none;
  }
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
  top: 30%;
  left: 20%;
  transform: translateX(-50%);
  width: 500px;
  max-width: 74%;
  padding: 20px 22px;
  min-height: 350px;

  /* 无边框设计 — 靠内容本身发光 */
  border-color: transparent;
  background: rgba(6, 12, 18, 0.55);
  box-shadow:
    0 20px 60px rgba(0, 0, 0, 0.5),
    0 0 120px rgba(52, 211, 153, 0.05),
    0 0 60px rgba(56, 189, 248, 0.03);

  z-index: 5; /* 最高层 */
  animation-delay: 0.2s;
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
  top: 8%;
  left: 6%;
  width: 210px;
  border-color: rgba(52, 211, 153, 0.08);
  z-index: 4;
  animation-delay: 0.35s;
}
.dc--price:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow:
    0 20px 56px rgba(0, 0, 0, 0.5),
    0 0 70px rgba(52, 211, 153, 0.16),
    0 0 0 1px rgba(52, 211, 153, 0.22) inset;
  border-color: rgba(52, 211, 153, 0.32);
}

/* ★★☆ 卫星 2：新能源 — 右上 */
.dc--stock {
  top: 5%;
  right: 4%;
  width: 205px;
  border-color: rgba(56, 189, 248, 0.07);
  z-index: 3;
  animation-delay: 0.45s;
}
.dc--stock:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow:
    0 20px 56px rgba(0, 0, 0, 0.5),
    0 0 70px rgba(56, 189, 248, 0.14),
    0 0 0 1px rgba(56, 189, 248, 0.2) inset;
  border-color: rgba(56, 189, 248, 0.3);
}

/* ★☆☆ 卫星 3：债券 — 左下 */
.dc--bond {
  bottom: 12%;
  left: 8%;
  width: 215px;
  border-color: rgba(167, 139, 250, 0.07);
  z-index: 2;
  animation-delay: 0.55s;
}
.dc--bond:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow:
    0 20px 56px rgba(0, 0, 0, 0.5),
    0 0 70px rgba(167, 139, 250, 0.14),
    0 0 0 1px rgba(167, 139, 250, 0.2) inset;
  border-color: rgba(167, 139, 250, 0.3);
}

/* ★☆☆ 卫星 4：AI模型 — 右下 */
.dc--ai {
  bottom: 16%;
  right: 6%;
  width: 195px;
  border-color: rgba(251, 146, 60, 0.07);
  z-index: 2;
  animation-delay: 0.65s;
}
.dc--ai:hover {
  transform: translateY(-8px) scale(1.03);
  box-shadow:
    0 20px 56px rgba(0, 0, 0, 0.5),
    0 0 70px rgba(251, 146, 60, 0.14),
    0 0 0 1px rgba(251, 146, 60, 0.2) inset;
  border-color: rgba(251, 146, 60, 0.3);
}

/* ═══ 持续呼吸微动效（独立固定值 Keyframe，避免 postcss 问题）══ */

@keyframes breatheChart {
  0%,
  100% {
    box-shadow:
      0 20px 60px rgba(0, 0, 0, 0.5),
      0 0 120px rgba(52, 211, 153, 0.05),
      0 0 60px rgba(56, 189, 248, 0.03);
  }
  50% {
    box-shadow:
      0 24px 70px rgba(0, 0, 0, 0.54),
      0 0 150px rgba(52, 211, 153, 0.09),
      0 0 80px rgba(56, 189, 248, 0.06);
  }
}
@keyframes breathePrice {
  0%,
  100% {
    box-shadow:
      0 4px 24px rgba(0, 0, 0, 0.38),
      0 0 0 1px rgba(255, 255, 255, 0.02) inset;
  }
  50% {
    box-shadow:
      0 6px 28px rgba(0, 0, 0, 0.42),
      0 0 44px rgba(52, 211, 153, 0.09);
    border-color: rgba(52, 211, 153, 0.12);
  }
}
@keyframes breatheStock {
  0%,
  100% {
    box-shadow:
      0 4px 24px rgba(0, 0, 0, 0.38),
      0 0 0 1px rgba(255, 255, 255, 0.02) inset;
  }
  50% {
    box-shadow:
      0 6px 28px rgba(0, 0, 0, 0.42),
      0 0 44px rgba(56, 189, 248, 0.08);
    border-color: rgba(56, 189, 248, 0.1);
  }
}
@keyframes breatheBond {
  0%,
  100% {
    box-shadow: 0 4px 24px rgba(0, 0, 0, 0.38);
  }
  50% {
    box-shadow:
      0 5px 26px rgba(0, 0, 0, 0.42),
      0 0 42px rgba(167, 139, 250, 0.07);
    border-color: rgba(167, 139, 250, 0.1);
  }
}
@keyframes breatheAi {
  0%,
  100% {
    box-shadow:
      0 4px 24px rgba(0, 0, 0, 0.38),
      0 0 0 1px rgba(255, 255, 255, 0.02) inset;
  }
  50% {
    box-shadow:
      0 6px 28px rgba(0, 0, 0, 0.42),
      0 0 44px rgba(251, 146, 60, 0.08);
    border-color: rgba(251, 146, 60, 0.1);
  }
}

/* 分配给各卡片的复合动画：入场(一次) + 呼吸(循环) */
.dc--chart {
  animation:
    cardEnter 0.65s ease 0.2s forwards,
    breatheChart 5s ease-in-out 2.5s infinite;
}
.dc--price {
  animation:
    cardEnter 0.6s ease 0.35s forwards,
    breathePrice 4.2s ease-in-out 2.2s infinite;
}
.dc--stock {
  animation:
    cardEnter 0.6s ease 0.45s forwards,
    breatheStock 4.8s ease-in-out 2.6s infinite;
}
.dc--bond {
  animation:
    cardEnter 0.55s ease 0.55s forwards,
    breatheBond 3.8s ease-in-out 2.1s infinite;
}
.dc--ai {
  animation:
    cardEnter 0.55s ease 0.65s forwards,
    breatheAi 5.2s ease-in-out 2.9s infinite;
}

/* hover 时暂停呼吸动画 */
.dc:hover {
  animation-play-state: paused;
}

/* ═══ 扫光效果（hover 时从左到右扫过）══ */
.dc::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    transparent 0%,
    rgba(255, 255, 255, 0.06) 45%,
    transparent 100%
  );
  transition: left 0.7s ease;
  z-index: 1;
  pointer-events: none;
  border-radius: inherit;
}
.dc:hover::after {
  left: 100%;
}

/* ─── 卡片内部组件 ─── */

/* 头部 */
.dc-head {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}
/* 图表专属头部 */
.dc-head--chart {
  flex-direction: column;
  align-items: flex-start;
  gap: 6px;
  margin-bottom: 14px;
}
.chart-title-row {
  display: flex;
  align-items: center;
  gap: 8px;
}
.chart-tag {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 1.5px;
  padding: 3px 10px;
  border-radius: 5px;
  margin-left: 6px;
}
.chart-tag--gru {
  color: #34d399;
  background: rgba(52, 211, 153, 0.1);
  border: 1px solid rgba(52, 211, 153, 0.25);
  box-shadow: 0 0 14px rgba(52, 211, 153, 0.08);
}
.chart-sub-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
  padding-left: 14px; /* 对齐 dot */
}
.chart-acc {
  font-size: 10px;
  color: rgba(148, 163, 184, 0.28);
  letter-spacing: 0.3px;
}
.chart-acc strong {
  color: #34d399;
  font-weight: 800;
  margin-left: 4px;
  text-shadow: 0 0 12px rgba(52, 211, 153, 0.35);
}
.dc-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
}
.dc-dot--g {
  background: #34d399;
  box-shadow: 0 0 10px rgba(52, 211, 153, 0.7);
}
.dc-dot--b {
  background: #38bdf8;
  box-shadow: 0 0 10px rgba(56, 189, 248, 0.7);
}
.dc-dot--p {
  background: #a78bfa;
  box-shadow: 0 0 10px rgba(167, 139, 250, 0.7);
}
.dc-dot--o {
  background: #fb923c;
  box-shadow: 0 0 10px rgba(251, 146, 60, 0.7);
}
.dc-label {
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  text-transform: uppercase;
  color: rgba(148, 163, 184, 0.32);
}
.dc-sub {
  margin-left: auto;
  font-size: 10px;
  color: rgba(148, 163, 184, 0.2);
}

/* 油价数值 */
.dc-badge {
  margin-left: auto;
  font-size: 11px;
  font-weight: 700;
  padding: 4px 10px;
  border-radius: 7px;
  animation: pulseGlow 2.5s ease-in-out infinite;
}
.dc-badge--up {
  color: #34d399;
  background: rgba(52, 211, 153, 0.12);
  border: 1px solid rgba(52, 211, 153, 0.3);
  box-shadow: 0 0 14px rgba(52, 211, 153, 0.15);
}
@keyframes pulseGlow {
  0%,
  100% {
    box-shadow: 0 0 14px rgba(52, 211, 153, 0.15);
  }
  50% {
    box-shadow: 0 0 22px rgba(52, 211, 153, 0.3);
  }
}

.dc-price-val {
  font-size: 40px;
  font-weight: 800;
  letter-spacing: -2px;
  color: #f1f5f9;
  line-height: 1.1;
  margin-bottom: 8px;
  text-shadow:
    0 0 28px rgba(52, 211, 153, 0.45),
    0 0 48px rgba(52, 211, 153, 0.18);
  animation: glowText 3.5s ease-in-out infinite;
}
@keyframes glowText {
  0%,
  100% {
    text-shadow:
      0 0 28px rgba(52, 211, 153, 0.45),
      0 0 48px rgba(52, 211, 153, 0.18);
  }
  50% {
    text-shadow:
      0 0 36px rgba(52, 211, 153, 0.65),
      0 0 68px rgba(52, 211, 153, 0.28);
  }
}

.dc-spark {
  width: 100%;
  height: 40px;
  border-radius: 10px;
  display: block;
  background: rgba(52, 211, 153, 0.04);
  border: 1px solid rgba(52, 211, 153, 0.08);
}

/* 数据行 */
.dc-metrics {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.dcm-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 13px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.025);
  border: 1px solid rgba(255, 255, 255, 0.06);
  transition: all 0.3s ease;
}
.dcm-row:hover {
  background: rgba(255, 255, 255, 0.04);
  border-color: rgba(52, 211, 153, 0.2);
  transform: translateX(4px);
}
.dcm-name {
  font-size: 11px;
  font-weight: 600;
  color: rgba(148, 163, 184, 0.6);
  letter-spacing: 0.3px;
}
.dcm-val {
  font-size: 17px;
  font-weight: 800;
  color: #e2e8f0;
  letter-spacing: -0.5px;
  text-shadow: 0 0 14px rgba(52, 211, 153, 0.3);
}
.dcm-val small {
  font-size: 11.5px;
  font-weight: 600;
  opacity: 0.75;
}
.dcm-ch {
  font-size: 10.5px;
  font-weight: 700;
  margin-left: 7px;
  padding: 3px 7px;
  border-radius: 6px;
  background: rgba(52, 211, 153, 0.14);
  border: 1px solid rgba(52, 211, 153, 0.28);
}
.dcm-up {
  color: #34d399;
}

/* AI 卡片 */
.ai-block {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ai-lbl {
  font-size: 11px;
  font-weight: 600;
  color: rgba(148, 163, 184, 0.6);
  letter-spacing: 0.5px;
}
.ai-pct {
  font-size: 34px;
  font-weight: 800;
  letter-spacing: -1px;
  color: #e2e8f0;
  text-shadow:
    0 0 24px rgba(251, 146, 60, 0.5),
    0 0 44px rgba(251, 146, 60, 0.2);
  animation: glowOrange 3.5s ease-in-out infinite;
}
@keyframes glowOrange {
  0%,
  100% {
    text-shadow:
      0 0 24px rgba(251, 146, 60, 0.5),
      0 0 44px rgba(251, 146, 60, 0.2);
  }
  50% {
    text-shadow:
      0 0 32px rgba(251, 146, 60, 0.7),
      0 0 64px rgba(251, 146, 60, 0.3);
  }
}
.ai-bar {
  height: 8px;
  background: rgba(255, 255, 255, 0.07);
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(251, 146, 60, 0.12);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2) inset;
}
.ai-fill {
  height: 100%;
  border-radius: 4px;
  background: linear-gradient(90deg, #ea580c, #fb923c, #fdba74);
  box-shadow: 0 0 14px rgba(251, 146, 60, 0.4);
}

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
  position: absolute;
  top: 20px;
  right: 28px;
  z-index: 6;
  display: flex;
  align-items: center;
  gap: 6px;
  font-size: 9px;
  font-weight: 700;
  letter-spacing: 2px;
  color: rgba(52, 211, 153, 0.35);
  text-transform: uppercase;
  animation: fadeUp 0.6s ease 0.5s both;
}
.lt-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  background: #34d399;
  animation: blink 2s ease-in-out infinite;
  box-shadow: 0 0 8px rgba(52, 211, 153, 0.6);
}

/* ═══ 响应式 ═══ */
@media (max-width: 1280px) {
  .dc--chart {
    width: 420px;
  }
  .dc--price,
  .dc--stock {
    width: 190px;
  }
  .dc--bond,
  .dc--ai {
    width: 185px;
  }
}
@media (max-width: 1024px) {
  .main-grid {
    grid-template-columns: 1fr;
    grid-template-rows: auto auto;
  }
  .brand-col {
    padding: 36px 28px 32px;
  }
  .viz-col {
    border-left: none;
    border-top: 1px solid rgba(255, 255, 255, 0.025);
    min-height: 500px;
    padding: 24px 16px;
  }
  /* 小屏：取消绝对定位，改为流式布局 */
  .dc {
    position: relative !important;
    top: auto !important;
    left: auto !important;
    right: auto !important;
    bottom: auto !important;
    transform: none !important;
    width: 100% !important;
    max-width: 480px;
    margin: 0 auto 12px;
    animation: fadeUp 0.5s ease forwards !important;
  }
  .dc--chart {
    order: -1;
    margin-bottom: 16px;
  }
  .live-tag {
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
  .dc {
    max-width: 100% !important;
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
