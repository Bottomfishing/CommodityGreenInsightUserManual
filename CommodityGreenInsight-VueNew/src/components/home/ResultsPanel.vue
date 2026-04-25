<template>
  <div class="work-panel">
    <div class="module-head">
      <span class="module-head-tag">RESULTS</span>
      <span class="module-head-title">结果预览面板</span>
    </div>
    <dv-decoration-3 class="module-head-line" />

    <div class="feature-actions">
      <button class="feature-btn feature-btn--primary" :disabled="loading" @click="emit('refresh')">
        刷新结果
      </button>
      <button class="feature-btn" :disabled="loading || !selectedRunId" @click="emit('generate')">
        生成 AI 报告
      </button>
    </div>

    <div class="data-block">
      <h3>AI 报告</h3>
      <div class="ai-report-md" v-html="FIXED_AI_REPORT_HTML"></div>
    </div>
    <div class="data-block">
      <h3>固定结果图</h3>
      <div class="ratio-rows">
        <div v-for="row in ratioRows" :key="row.key" class="ratio-row">
          <div class="ratio-row-head">
            <span class="ratio-row-title">比例接近：{{ row.title }}</span>
            <span class="ratio-row-sub">本行 {{ row.items.length }} 张</span>
          </div>
          <div class="ratio-row-grid" :style="row.gridStyle">
            <figure
              v-for="item in row.items"
              :key="item.name"
              class="fixed-image-item"
              :class="imageSizeClass(item.name)"
            >
              <img v-if="item.url" :src="item.url" :alt="item.name" loading="lazy" />
              <div v-else class="image-missing">外部目录中暂无该图</div>
              <figcaption>{{ item.label }}</figcaption>
            </figure>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from "vue";
import { fetchStaticResultFiles, getStaticResultImageObjectUrl } from "@/api/index";

const props = defineProps<{
  loading: boolean;
  selectedRunId: string;
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

const FIXED_IMAGE_FILES: Array<{ candidates: string[]; label: string }> = [
  { candidates: ["gru_predictions.png", "future_forecast.png"], label: "价格预测对比" },
  { candidates: ["gru_returns.png"], label: "收益率预测对比" },
  { candidates: ["direction_confusion_matrix.png"], label: "方向混淆矩阵" },
  { candidates: ["direction_prob_distribution.png"], label: "方向概率分布" },
  { candidates: ["direction_prediction.png"], label: "方向预测结果" },
  { candidates: ["train_val_loss.png"], label: "训练/验证损失" },
  { candidates: ["return_scatter.png"], label: "收益散点图" },
  { candidates: ["residual_distribution.png"], label: "残差分布" },
  { candidates: ["backtest_nav_curve.png"], label: "回测净值曲线" },
  { candidates: ["rf_feature_importance.png", "top_drivers_rf_importance.png"], label: "RF 特征重要性" },
  { candidates: ["shap_feature_importance.png", "top_drivers_spearman.png"], label: "SHAP/相关性重要性" },
  { candidates: ["preprocess_distribution_compare.png"], label: "预处理分布对比" },
  { candidates: ["preprocess_before_after_returns.png"], label: "预处理前后收益" },
  { candidates: ["preprocess_feature_compare.png"], label: "特征预处理对比" },
  { candidates: ["vmd_before_after.png"], label: "VMD 前后对比" },
];

type FixedImageItem = { name: string; label: string; url: string | null };
const fixedImagesState = ref<Record<string, string | null>>({});
const fixedRatios = ref<Record<string, number | null>>({});

const fixedImages = computed<FixedImageItem[]>(() =>
  FIXED_IMAGE_FILES.map((item) => ({
    name: item.candidates[0],
    label: item.label,
    url: fixedImagesState.value[item.candidates[0]] ?? null,
  })),
);

type RatioRow = {
  key: string;
  title: string;
  items: FixedImageItem[];
  gridStyle: Record<string, string>;
};

function _fmtRatio(r: number | null | undefined): string {
  if (!r || !Number.isFinite(r)) return "未知";
  return r.toFixed(2);
}

function _gridMinWidthByRatio(r: number | null | undefined): number {
  // 越宽的图越需要更大的最小宽度，否则一行会太挤
  if (!r || !Number.isFinite(r)) return 300;
  if (r >= 2.2) return 520;
  if (r >= 1.8) return 440;
  if (r >= 1.4) return 360;
  return 280; // 方/近方
}

const ratioRows = computed<RatioRow[]>(() => {
  const pinnedNames = new Set(["return_scatter.png", "shap_feature_importance.png", "backtest_nav_curve.png"]);
  const pinnedItems = fixedImages.value.filter((x) => pinnedNames.has(x.name));
  const normalItems = fixedImages.value.filter((x) => !pinnedNames.has(x.name));

  const imgs = normalItems
    .map((img) => ({ ...img, ratio: fixedRatios.value[img.name] }))
    .sort((a, b) => {
      const ra = a.ratio ?? 999;
      const rb = b.ratio ?? 999;
      return ra - rb;
    });

  // 将“比例差不多”的聚成一行：相邻差值 <= 0.18 认为接近
  const rows: Array<Array<(FixedImageItem & { ratio: number | null | undefined })>> = [];
  let cur: Array<(FixedImageItem & { ratio: number | null | undefined })> = [];
  let base: number | null | undefined = undefined;
  const TH = 0.18;

  for (const it of imgs) {
    const r = it.ratio;
    if (!cur.length) {
      cur = [it];
      base = r;
      continue;
    }

    const baseNum: number | undefined =
      typeof base === "number" && Number.isFinite(base) ? base :
      typeof r === "number" && Number.isFinite(r) ? r :
      undefined;
    const rNum: number | undefined =
      typeof r === "number" && Number.isFinite(r) ? r : baseNum;

    if (baseNum === undefined || rNum === undefined || Math.abs(rNum - baseNum) <= TH) {
      cur.push(it);
      // 用滑动平均稳定分组
      if (typeof baseNum === "number" && typeof rNum === "number") {
        base = (baseNum * (cur.length - 1) + rNum) / cur.length;
      }
    } else {
      rows.push(cur);
      cur = [it];
      base = r;
    }
  }
  if (cur.length) rows.push(cur);

  const autoRows: RatioRow[] = rows.map((items, idx) => {
    const ratios = items
      .map((x) => x.ratio)
      .filter((x): x is number => typeof x === "number" && Number.isFinite(x));
    const minR = ratios.length ? Math.min(...ratios) : null;
    const maxR = ratios.length ? Math.max(...ratios) : null;
    const avgR = ratios.length ? ratios.reduce((a, b) => a + b, 0) / ratios.length : null;
    const minW = _gridMinWidthByRatio(avgR);
    return {
      key: `row_${idx}_${_fmtRatio(avgR)}`,
      title: minR !== null && maxR !== null ? `${_fmtRatio(minR)} ~ ${_fmtRatio(maxR)}` : "未知",
      items: items.map(({ ratio: _r, ...rest }) => rest),
      gridStyle: {
        gridTemplateColumns: `repeat(auto-fit, minmax(${minW}px, 1fr))`,
      },
    };
  });

  if (pinnedItems.length) {
    const pinnedRow: RatioRow = {
      key: "row_pinned_scatter_shap",
      title: "重点图：收益散点图 + SHAP + 回测净值曲线",
      items: pinnedItems,
      gridStyle: {
        gridTemplateColumns: "repeat(3, minmax(300px, 1fr))",
      },
    };
    return [pinnedRow, ...autoRows];
  }

  return autoRows;
});

function readImageRatio(url: string): Promise<number> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => {
      const w = Number(img.naturalWidth || 0);
      const h = Number(img.naturalHeight || 0);
      if (w > 0 && h > 0) resolve(w / h);
      else reject(new Error("invalid image size"));
    };
    img.onerror = () => reject(new Error("image load failed"));
    img.src = url;
  });
}

function imageSizeClass(name: string): string {
  const key = String(name || "").toLowerCase();
  // 这两张图在网格里观感容易“过大”，单独做紧凑展示
  if (key.includes("return_scatter") || key.includes("shap_feature_importance")) return "is-compact";
  return "";
}

function cleanupObjectUrls() {
  Object.values(fixedImagesState.value).forEach((url) => {
    if (url) URL.revokeObjectURL(url);
  });
  fixedImagesState.value = {};
  fixedRatios.value = {};
}

async function loadFixedImages() {
  cleanupObjectUrls();
  let fileSet = new Set<string>();
  try {
    const filesRes = await fetchStaticResultFiles();
    const list = filesRes?.files || [];
    fileSet = new Set<string>(list.map((x: any) => String(x?.name || x || "")));
  } catch {
    fileSet = new Set<string>();
  }

  await Promise.all(
    FIXED_IMAGE_FILES.map(async (item) => {
      const hit = item.candidates.find((name) => fileSet.has(name));
      if (!hit) {
        fixedImagesState.value = { ...fixedImagesState.value, [item.candidates[0]]: null };
        return;
      }
      try {
        const objectUrl = await getStaticResultImageObjectUrl(hit);
        fixedImagesState.value = { ...fixedImagesState.value, [item.candidates[0]]: objectUrl };
        try {
          const ratio = await readImageRatio(objectUrl);
          fixedRatios.value = { ...fixedRatios.value, [item.candidates[0]]: ratio };
        } catch {
          fixedRatios.value = { ...fixedRatios.value, [item.candidates[0]]: null };
        }
      } catch {
        fixedImagesState.value = { ...fixedImagesState.value, [item.candidates[0]]: null };
        fixedRatios.value = { ...fixedRatios.value, [item.candidates[0]]: null };
      }
    }),
  );
}

watch(
  () => props.selectedRunId,
  async () => {
    await loadFixedImages();
  },
  { immediate: true },
);

onBeforeUnmount(() => {
  cleanupObjectUrls();
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
  max-height: 220px;
  overflow: auto;
  font-size: 11px;
  line-height: 1.5;
  color: rgba(226, 232, 240, 0.9);
  font-family: "Cascadia Code", "Consolas", monospace;
}
.ai-report-md {
  max-height: 420px;
  overflow: auto;
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
.ratio-rows {
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.ratio-row {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.ratio-row-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  gap: 10px;
}
.ratio-row-title {
  font-size: 12px;
  font-weight: 700;
  color: rgba(186, 230, 253, 0.98);
}
.ratio-row-sub {
  font-size: 11px;
  color: rgba(148, 163, 184, 0.75);
}
.ratio-row-grid {
  display: grid;
  gap: 12px;
}
.fixed-image-item {
  margin: 0;
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  padding: 8px;
  background: rgba(2, 12, 28, 0.75);
  overflow: hidden;
}
.fixed-image-item.is-compact {
  max-width: 520px;
  margin: 0 auto;
}
.fixed-image-item.is-compact img {
  max-height: 260px !important;
}
.fixed-image-item img {
  width: 100%;
  height: auto;
  display: block;
  border-radius: 6px;
  object-fit: contain;
  object-position: center center;
  background: #07142a;
}
.fixed-image-item--wide img,
.fixed-image-item--wide .image-missing {
  max-height: 420px;
}
.fixed-image-item--square img,
.fixed-image-item--square .image-missing {
  max-height: 360px;
}
.image-missing {
  min-height: 220px;
  border: 1px dashed rgba(148, 163, 184, 0.4);
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: rgba(148, 163, 184, 0.9);
}
.fixed-image-item figcaption {
  margin-top: 8px;
  font-size: 11px;
  color: rgba(186, 230, 253, 0.95);
  text-align: center;
}
.empty-hint {
  font-size: 12px;
  color: rgba(148, 163, 184, 0.85);
}
@media (max-width: 1200px) {
  .fixed-image-item--wide img,
  .fixed-image-item--wide .image-missing {
    max-height: 360px;
  }
  .fixed-image-item--square img,
  .fixed-image-item--square .image-missing {
    max-height: 320px;
  }
}
@media (max-width: 900px) {
  .ratio-row-grid {
    grid-template-columns: 1fr !important;
  }
}
</style>

