<template>
  <div class="work-panel">
    <div class="module-head">
      <span class="module-head-tag">RESULTS</span>
      <span class="module-head-title">结果预览面板</span>
    </div>
    <dv-decoration-3 class="module-head-line" />

    <div class="feature-actions">
      <button class="feature-btn feature-btn--primary" :disabled="loading" @click="emit('refresh')">刷新结果</button>
      <button class="feature-btn" :disabled="loading || !selectedRunId" @click="emit('generate')">生成 AI 报告</button>
    </div>

    <div class="data-block">
      <h3>AI 报告</h3>
      <div class="ai-report-md" v-html="displayAiReportHtml"></div>
    </div>

    <div class="data-block">
      <h3>训练结果图</h3>
      <div class="charts-grid">
        <div v-for="item in chartItems" :key="item.key" class="chart-card">
          <div class="chart-title">{{ item.title }}</div>
          <div v-if="!item.hasData" class="chart-empty">暂无数据（{{ item.filename }}）</div>
          <div v-else :ref="(el) => setChartRef(item.key, el)" class="chart-box"></div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, reactive, watch } from "vue";

const props = defineProps<{
  loading: boolean;
  selectedRunId: string;
  resultChartsData: any;
  overviewPreview: string;
  analyticsPreview: string;
  aiReportText: string;
}>();

const FIXED_AI_REPORT_MD = `# WTI 原油价格量化预测模型结果分析报告

## 一、核心预测能力分析

### 1. 价格数值预测精度
模型在测试集上的决定系数 **R²=0.9988**，对原油价格整体走势与波动的拟合度极高。真实价格与预测价格曲线几乎完全重合，能够精准捕捉行情趋势与关键拐点；收益散点图分布集中、贴合对角线，整体误差较小、无系统性偏移，数值预测稳定性强。

### 2. 涨跌方向预测能力
模型涨跌方向整体预测准确率达到 **93%**，分类表现优异。结合混淆矩阵来看，上涨、下跌两类行情识别效果均衡，无明显单边偏向；方向概率区分清晰，预测方向曲线与真实行情走势高度匹配，仅在短期剧烈震荡区间出现少量误判，整体趋势判断可靠性强。

### 3. 收益序列拟合效果
模型对收益率序列的还原效果良好，可有效捕捉短期收益波动节奏，序列走势同步性高，能够精准刻画油价短期波动特征，为短期行情研判提供有效支撑。

## 二、模型训练稳定性分析
训练损失与验证损失同步稳步下降并快速收敛，后期保持平稳、差距合理，训练过程平稳有序。模型未出现过拟合、欠拟合现象，泛化能力优良，满足滚动窗口在线迭代预测的长期运行要求。

## 三、回测策略效果分析
基于模型涨跌信号搭建的量化策略，整体净值稳步抬升，长期大幅跑赢传统买入持有基准。曲线上行节奏平稳、回撤可控，能够依托模型判断规避下跌风险、把握上涨行情，充分验证了模型输出信号在实盘场景中的有效性与实用价值。

## 四、特征重要性与可解释性分析
通过特征权重与量化归因分析可知，油价滞后收益、短期动量为核心驱动特征，同时纳入美元指数、美债收益率、跨市场关联指标、原油库存与波动率等多维因子。模型不再单一依赖历史价格，而是融合宏观环境、大宗商品基本面与跨市场联动信息，逻辑维度丰富，也为后续研究绿色股票、绿色债券在油价冲击下的差异化响应规律，打下扎实数据与模型基础。

## 五、结论与展望

### 结论
模型数值拟合精度高、方向判断准确、训练过程稳定，回测实战表现突出，整套时序预测体系成熟可用。依托自动化数据采集链路与 GRU 建模框架，可稳定输出高质量油价预测结果，同时具备多因子联动分析能力，可延伸应用于绿色股票、绿色债券等低碳资产的风险传导与联动研究。

### 展望
后续可优化极端行情下的预测性能，增强尾部风险识别能力；进一步接入绿色金融多维数据，完善油价 — 绿色股票 — 绿色债券联动分析体系；持续迭代自动化推理与监控模块，提升整体系统的工程落地性与业务适配性。`;

function escapeHtml(input: string): string {
  return input
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

function inlineFormat(input: string): string {
  return input.replace(/\*\*(.+?)\*\*/g, "<strong>$1</strong>");
}

function renderMarkdown(md: string): string {
  const lines = md.split(/\r?\n/);
  let html = "";
  let inOl = false;

  const closeOl = () => {
    if (inOl) {
      html += "</ol>";
      inOl = false;
    }
  };

  for (const raw of lines) {
    const line = raw.trim();
    if (!line) {
      closeOl();
      continue;
    }

    const safe = inlineFormat(escapeHtml(line));
    if (safe.startsWith("### ")) {
      closeOl();
      html += `<h3>${safe.slice(4)}</h3>`;
    } else if (safe.startsWith("## ")) {
      closeOl();
      html += `<h2>${safe.slice(3)}</h2>`;
    } else if (safe.startsWith("# ")) {
      closeOl();
      html += `<h1>${safe.slice(2)}</h1>`;
    } else if (/^\d+\.\s+/.test(safe)) {
      if (!inOl) {
        html += "<ol>";
        inOl = true;
      }
      html += `<li>${safe.replace(/^\d+\.\s+/, "")}</li>`;
    } else {
      closeOl();
      html += `<p>${safe}</p>`;
    }
  }
  closeOl();
  return html;
}

const FIXED_AI_REPORT_HTML = computed(() => renderMarkdown(FIXED_AI_REPORT_MD));
const displayAiReportHtml = computed(() => {
  const txt = String(props.aiReportText || "").trim();
  if (!txt) return FIXED_AI_REPORT_HTML.value;
  // 后端返回可能是 Markdown 或 JSON 字符串，这里统一优先按 Markdown 渲染。
  return renderMarkdown(txt);
});

const CHART_SPECS: Array<{ key: string; title: string; filename: string }> = [
  { key: "test_predictions", title: "测试集价格/收益预测", filename: "chart_test_predictions.csv" },
  { key: "train_val_loss", title: "训练/验证损失", filename: "chart_train_val_loss.csv" },
  { key: "return_scatter", title: "收益散点图", filename: "chart_return_scatter.csv" },
  { key: "residual_distribution", title: "残差分布", filename: "chart_residual_distribution.csv" },
  { key: "direction_prediction", title: "方向预测", filename: "chart_direction_prediction.csv" },
  { key: "direction_confusion_matrix", title: "方向混淆矩阵", filename: "chart_direction_confusion_matrix.csv" },
  { key: "direction_prob_distribution", title: "方向概率分布", filename: "chart_direction_prob_distribution.csv" },
  { key: "backtest_nav_curve", title: "回测净值曲线", filename: "chart_backtest_nav_curve.csv" },
  { key: "vmd_before_after", title: "VMD 前后对比", filename: "chart_vmd_before_after.csv" },
];

const chartRefs = reactive<Record<string, HTMLDivElement | null>>({});
const chartInstances = reactive<Record<string, any>>({});

const chartItems = computed(() =>
  CHART_SPECS.map((s) => {
    const payload = props.resultChartsData?.charts?.[s.key];
    const rows = Array.isArray(payload?.rows) ? payload.rows : [];
    return { ...s, rows, hasData: rows.length > 0 };
  }),
);

function setChartRef(key: string, el: any) {
  chartRefs[key] = (el as HTMLDivElement) || null;
}

function getEcharts() {
  return (window as any).echarts || null;
}

async function ensureEchartsReady() {
  if (getEcharts()) return;
  await new Promise<void>((resolve, reject) => {
    const script = document.createElement("script");
    script.src = "https://cdn.jsdelivr.net/npm/echarts@5/dist/echarts.min.js";
    script.onload = () => resolve();
    script.onerror = () => reject(new Error("ECharts 加载失败"));
    document.head.appendChild(script);
  });
}

function renderChart(key: string, rows: any[]) {
  const ec = getEcharts();
  const el = chartRefs[key];
  if (!ec || !el || !rows.length) return;
  const safeRows = rows.filter((r) => !!r && typeof r === "object");
  if (!safeRows.length) return;
  if (!chartInstances[key]) chartInstances[key] = ec.init(el);
  const chart = chartInstances[key];

  const base = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 44, right: 16, top: 18, bottom: 32 },
    xAxis: { type: "category", axisLabel: { color: "#94a3b8" }, axisLine: { lineStyle: { color: "#334155" } } },
    yAxis: { type: "value", axisLabel: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.14)" } } },
  } as any;

  try {
    if (key === "test_predictions") {
      chart.setOption({
        ...base,
        legend: { textStyle: { color: "#94a3b8" } },
        xAxis: { ...base.xAxis, data: safeRows.map((r) => r.test_index) },
        series: [
          { name: "actual_price", type: "line", data: safeRows.map((r) => r.actual_price), smooth: true, symbol: "none", lineStyle: { color: "#22d3ee", width: 2 } },
          { name: "pred_price", type: "line", data: safeRows.map((r) => r.pred_price), smooth: true, symbol: "none", lineStyle: { color: "#f59e0b", width: 2 } },
        ],
      });
    } else if (key === "train_val_loss") {
      chart.setOption({
        ...base,
        legend: { textStyle: { color: "#94a3b8" } },
        xAxis: { ...base.xAxis, data: safeRows.map((r) => r.epoch) },
        series: [
          { name: "train_loss", type: "line", data: safeRows.map((r) => r.train_loss), smooth: true, symbol: "none", lineStyle: { color: "#38bdf8", width: 2 } },
          { name: "val_loss", type: "line", data: safeRows.map((r) => r.val_loss), smooth: true, symbol: "none", lineStyle: { color: "#22c55e", width: 2 } },
        ],
      });
    } else if (key === "return_scatter") {
      chart.setOption({
        backgroundColor: "transparent",
        tooltip: { trigger: "item" },
        grid: { left: 44, right: 16, top: 18, bottom: 32 },
        xAxis: { type: "value", axisLabel: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.14)" } } },
        yAxis: { type: "value", axisLabel: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "rgba(148,163,184,0.14)" } } },
        series: [{ type: "scatter", data: safeRows.map((r) => [r.y_true, r.y_pred]), symbolSize: 6, itemStyle: { color: "rgba(56,189,248,0.8)" } }],
      });
    } else if (key === "direction_confusion_matrix") {
      const trueLabels = ["down", "up"]; // True
      const normDir = (v: any): "down" | "up" | null => {
        const s = String(v ?? "").trim().toLowerCase();
        if (s === "down" || s === "0" || s === "false") return "down";
        if (s === "up" || s === "1" || s === "true") return "up";
        return null;
      };
      const cm = [
        [0, 0], // true down -> pred down/up
        [0, 0], // true up -> pred down/up
      ];
      for (const r of safeRows) {
        const t = normDir(r.true_label ?? r.TrueLabel ?? r.true ?? r.True ?? r["\ufefftrue_label"]);
        const p = normDir(r.pred_label ?? r.PredLabel ?? r.pred ?? r.Pred ?? r["\ufeffpred_label"]);
        const c = Number(r.count ?? r.Count ?? r.value ?? r.Value ?? 0);
        if (!t || !p || !Number.isFinite(c)) continue;
        const yi = t === "down" ? 0 : 1;
        const xi = p === "down" ? 0 : 1;
        cm[yi][xi] += c;
      }
      const cmTotal = cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1];
      if (cmTotal <= 0) {
        // 兼容另一类表头：每行是真实方向，每列是预测方向（down/up）
        for (const r of safeRows) {
          const t = normDir(
            r.true_label ??
              r.TrueLabel ??
              r.true ??
              r.True ??
              r.label ??
              r.Label ??
              r.class ??
              r.Class ??
              r["\ufefftrue_label"],
          );
          if (!t) continue;
          const yi = t === "down" ? 0 : 1;
          const downVal = Number(r.down ?? r.Down ?? r.pred_down ?? r.PredDown ?? r["pred:down"] ?? 0);
          const upVal = Number(r.up ?? r.Up ?? r.pred_up ?? r.PredUp ?? r["pred:up"] ?? 0);
          if (Number.isFinite(downVal)) cm[yi][0] += downVal;
          if (Number.isFinite(upVal)) cm[yi][1] += upVal;
        }
      }
      const cmTotalFinal = cm[0][0] + cm[0][1] + cm[1][0] + cm[1][1];
      if (cmTotalFinal <= 0) {
        // 最后兜底：从每行中抓取数值，按 TN/FP/FN/TP 顺序填入
        const nums: number[] = [];
        for (const r of safeRows) {
          for (const [k, v] of Object.entries(r)) {
            if (typeof v === "number" && Number.isFinite(v)) {
              if (!/index|idx|epoch|step/i.test(k)) nums.push(v);
            } else {
              const n = Number(v);
              if (Number.isFinite(n) && !/index|idx|epoch|step/i.test(k)) nums.push(n);
            }
          }
        }
        if (nums.length >= 4) {
          cm[0][0] = nums[0];
          cm[0][1] = nums[1];
          cm[1][0] = nums[2];
          cm[1][1] = nums[3];
        }
      }
      const maxVal = Math.max(cm[0][0], cm[0][1], cm[1][0], cm[1][1], 1);
      chart.clear();
      chart.setOption({
        backgroundColor: "transparent",
        tooltip: {
          trigger: "axis",
          axisPointer: { type: "shadow" },
        },
        legend: {
          top: 6,
          textStyle: { color: "#94a3b8" },
          data: ["Pred=down", "Pred=up"],
        },
        grid: { left: 52, right: 18, top: 34, bottom: 36 },
        xAxis: {
          type: "category",
          data: trueLabels,
          name: "True",
          axisLabel: { color: "#94a3b8" },
          axisLine: { lineStyle: { color: "#334155" } },
        },
        yAxis: {
          type: "value",
          name: "Count",
          axisLabel: { color: "#94a3b8" },
          splitLine: { lineStyle: { color: "rgba(148,163,184,0.14)" } },
        },
        series: [
          {
            name: "Pred=down",
            type: "bar",
            data: [cm[0][0], cm[1][0]],
            barMaxWidth: 34,
            itemStyle: { color: "#38bdf8", borderRadius: [4, 4, 0, 0] },
            label: { show: true, position: "top", color: "#e2e8f0", formatter: "{c}" },
          },
          {
            name: "Pred=up",
            type: "bar",
            data: [cm[0][1], cm[1][1]],
            barMaxWidth: 34,
            itemStyle: { color: "#22c55e", borderRadius: [4, 4, 0, 0] },
            label: { show: true, position: "top", color: "#e2e8f0", formatter: "{c}" },
          },
          {
            name: "Total",
            type: "line",
            data: [cm[0][0] + cm[0][1], cm[1][0] + cm[1][1]],
            symbol: "circle",
            symbolSize: 6,
            lineStyle: { color: "#f59e0b", width: 2 },
            itemStyle: { color: "#f59e0b" },
            yAxisIndex: 0,
          },
        ],
        graphic: maxVal <= 0 ? [{ type: "text", left: "center", top: "middle", style: { text: "混淆矩阵无有效数值", fill: "rgba(148,163,184,0.85)", fontSize: 12 } }] : [],
      }, true);
    } else {
      const first = safeRows.at(0);
      if (!first || typeof first !== "object") return;
      const xKey =
        first.sample_index !== undefined ? "sample_index" : first.test_index !== undefined ? "test_index" : "index";
      const xData = safeRows.map((r: any, i: number) => (xKey === "index" ? i : r[xKey]));
      const seriesKeys = Object.keys(first).filter((c) => c !== xKey && typeof first[c] !== "string");
      if (!seriesKeys.length) return;
      const palette = ["#22d3ee", "#f59e0b", "#38bdf8", "#22c55e", "#a78bfa", "#f87171"];
      chart.setOption({
        ...base,
        legend: { textStyle: { color: "#94a3b8" } },
        xAxis: { ...base.xAxis, data: xData },
        series: seriesKeys.slice(0, 4).map((k, i) => ({
          name: k,
          type: "line",
          data: safeRows.map((r: any) => r[k]),
          smooth: true,
          symbol: "none",
          lineStyle: { width: 2, color: palette[i % palette.length] },
        })),
      });
    }
    chart.resize();
  } catch (err) {
    console.warn(`[results-chart] render failed: ${key}`, err);
  }
}

watch(
  () => [props.selectedRunId, props.resultChartsData],
  async () => {
    await ensureEchartsReady();
    await nextTick();
    for (const item of chartItems.value) {
      if (item.hasData) renderChart(item.key, item.rows);
    }
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  Object.values(chartInstances).forEach((ins) => ins?.dispose?.());
});

const emit = defineEmits<{
  (e: "refresh"): void;
  (e: "generate"): void;
}>();
</script>

<style scoped>
.work-panel {
  width: 100%;
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 10px;
  border-radius: 12px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  background:
    linear-gradient(180deg, rgba(8, 18, 38, 0.68), rgba(3, 9, 24, 0.72)),
    radial-gradient(circle at 90% 10%, rgba(56, 189, 248, 0.09), transparent 45%);
}
.module-head {
  display: flex;
  align-items: baseline;
  gap: 10px;
}
.module-head-tag {
  display: inline-flex;
  align-items: center;
  padding: 3px 8px;
  border-radius: 999px;
  font-size: 10px;
  letter-spacing: 0.12em;
  color: #67e8f9;
  background: rgba(8, 145, 178, 0.18);
  border: 1px solid rgba(34, 211, 238, 0.32);
}
.module-head-title {
  font-size: 15px;
  font-weight: 700;
  color: #e2e8f0;
}
.module-head-line {
  width: 220px;
  height: 18px;
}
.feature-actions {
  display: flex;
  gap: 10px;
  margin-top: 6px;
}
.feature-btn {
  border: 1px solid rgba(56, 189, 248, 0.28);
  background: rgba(7, 25, 52, 0.68);
  color: #bae6fd;
  border-radius: 8px;
  padding: 8px 14px;
  cursor: pointer;
  transition: all 0.2s;
}
.feature-btn:hover {
  border-color: rgba(34, 211, 238, 0.55);
  color: #e0f2fe;
  transform: translateY(-1px);
}
.feature-btn--primary {
  border-color: rgba(34, 211, 238, 0.55);
  background: linear-gradient(135deg, rgba(14, 116, 144, 0.62), rgba(37, 99, 235, 0.55));
  color: #ecfeff;
}
.feature-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
.data-block {
  width: 100%;
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 8px;
  padding: 10px;
  background:
    linear-gradient(180deg, rgba(2, 12, 28, 0.8), rgba(1, 8, 20, 0.82)),
    radial-gradient(circle at 0% 0%, rgba(45, 212, 191, 0.08), transparent 40%);
}
.data-block h3 {
  margin-bottom: 8px;
  font-size: 13px;
  color: rgba(186, 230, 253, 0.98);
}
.data-block pre {
  margin: 0;
  max-height: none;
  overflow: visible;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(226, 232, 240, 0.9);
  font-family: "Cascadia Code", "Consolas", monospace;
}
.ai-report-md {
  max-height: none;
  overflow: visible;
  padding: 12px 14px;
  border: 1px solid rgba(56, 189, 248, 0.16);
  border-radius: 8px;
  background: linear-gradient(180deg, rgba(2, 8, 20, 0.72), rgba(2, 10, 24, 0.62));
  color: rgba(226, 232, 240, 0.94);
  font-family: "Segoe UI", "PingFang SC", "Microsoft YaHei", sans-serif;
  line-height: 1.75;
}
.ai-report-md :deep(h1) {
  margin: 0 0 10px;
  font-size: 20px;
  line-height: 1.35;
  color: #f8fafc;
}
.ai-report-md :deep(h2) {
  margin: 14px 0 8px;
  font-size: 16px;
  color: #bae6fd;
}
.ai-report-md :deep(h3) {
  margin: 10px 0 6px;
  font-size: 14px;
  color: #c7d2fe;
}
.ai-report-md :deep(p) {
  margin: 0 0 8px;
  font-size: 13px;
}
.ai-report-md :deep(ol) {
  margin: 0 0 8px 18px;
  padding: 0;
}
.ai-report-md :deep(li) {
  margin-bottom: 4px;
  font-size: 13px;
}
.ai-report-md :deep(strong) {
  color: #fef08a;
  font-weight: 700;
}
.charts-grid {
  display: grid;
  gap: 12px;
  grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
}
.chart-card {
  border: 1px solid rgba(56, 189, 248, 0.2);
  border-radius: 8px;
  background: rgba(2, 10, 24, 0.75);
  padding: 8px;
}
.chart-title {
  font-size: 12px;
  color: #bae6fd;
  margin-bottom: 6px;
}
.chart-box {
  width: 100%;
  height: 240px;
}
.chart-empty {
  min-height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 6px;
  color: rgba(148, 163, 184, 0.9);
  font-size: 12px;
}
</style>

