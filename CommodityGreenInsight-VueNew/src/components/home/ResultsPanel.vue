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
      <h3>概览</h3>
      <pre>{{ overviewPreview }}</pre>
    </div>
    <div class="data-block">
      <h3>分析指标</h3>
      <pre>{{ analyticsPreview }}</pre>
    </div>
    <div class="data-block">
      <h3>AI 报告</h3>
      <pre>{{ aiReportText || "暂无报告" }}</pre>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  loading: boolean;
  selectedRunId: string;
  overviewPreview: string;
  analyticsPreview: string;
  aiReportText: string;
}>();
void props;

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
</style>

