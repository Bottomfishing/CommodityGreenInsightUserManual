<template>
  <div class="work-panel">
    <div class="module-head">
      <span class="module-head-tag">RUN CONFIG</span>
      <span class="module-head-title">运行配置面板</span>
    </div>
    <dv-decoration-3 class="module-head-line" />

    <div class="form-grid">
      <label class="field">
        <span>数据 ZIP</span>
        <input type="file" accept=".zip" @change="emit('file-selected', $event)" />
      </label>
      <label class="field">
        <span>TopN</span>
        <input v-model.number="runForm.topN" type="number" min="1" />
      </label>
      <label class="field">
        <span>Epochs</span>
        <input v-model.number="runForm.epochs" type="number" min="1" />
      </label>
      <label class="field">
        <span>预测步长</span>
        <input v-model.number="runForm.forecastSteps" type="number" min="1" />
      </label>
      <label class="field">
        <span>截止日期（可选）</span>
        <input v-model="runForm.cutoffDate" type="date" />
      </label>
      <label class="checkbox-field">
        <input v-model="runForm.enableEarlyStopping" type="checkbox" />
        <span>启用早停</span>
      </label>
    </div>

    <div class="feature-actions">
      <button class="feature-btn feature-btn--primary" :disabled="runLoading" @click="emit('submit')">
        {{ runLoading ? "启动中..." : "开始运行" }}
      </button>
      <button class="feature-btn" :disabled="!selectedRunId || runLoading" @click="emit('stop')">
        停止当前运行
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  runForm: {
    topN: number;
    epochs: number;
    forecastSteps: number;
    cutoffDate: string;
    enableEarlyStopping: boolean;
  };
  runLoading: boolean;
  selectedRunId: string;
}>();

void props;

const emit = defineEmits<{
  (e: "file-selected", event: Event): void;
  (e: "submit"): void;
  (e: "stop"): void;
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
  box-shadow:
    inset 0 0 24px rgba(56, 189, 248, 0.05),
    0 10px 24px rgba(2, 6, 23, 0.24);
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
.form-grid {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 10px;
}
.field,
.checkbox-field {
  display: flex;
  flex-direction: column;
  gap: 6px;
  color: rgba(191, 219, 254, 0.92);
  font-size: 12px;
}
.checkbox-field {
  flex-direction: row;
  align-items: center;
  margin-top: 20px;
}
.field input {
  border: 1px solid rgba(56, 189, 248, 0.25);
  border-radius: 8px;
  background: rgba(4, 16, 38, 0.72);
  color: #e0f2fe;
  padding: 8px 10px;
  transition: all 0.2s;
}
.field input:focus {
  outline: none;
  border-color: rgba(34, 211, 238, 0.7);
  box-shadow: 0 0 0 3px rgba(34, 211, 238, 0.12);
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
  box-shadow: 0 4px 16px rgba(14, 116, 144, 0.3);
}
.feature-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
