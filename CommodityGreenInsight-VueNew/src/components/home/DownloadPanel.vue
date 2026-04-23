<template>
  <div class="work-panel">
    <div class="module-head">
      <span class="module-head-tag">EXPORT</span>
      <span class="module-head-title">下载导出面板</span>
    </div>
    <dv-decoration-3 class="module-head-line" />

    <div class="feature-actions">
      <button class="feature-btn feature-btn--primary" :disabled="loading" @click="emit('refresh')">
        刷新文件列表
      </button>
      <button class="feature-btn" :disabled="!selectedRunId" @click="emit('export')">
        下载整包 ZIP
      </button>
    </div>

    <div class="file-list">
      <button
        v-for="file in files"
        :key="file.name || file"
        class="file-item"
        @click="emit('download', file.name || file)"
      >
        {{ file.name || file }}
      </button>
      <p v-if="!files.length" class="empty-text">暂无可下载文件</p>
    </div>
  </div>
</template>

<script setup lang="ts">
const props = defineProps<{
  loading: boolean;
  selectedRunId: string;
  files: any[];
}>();
void props;

const emit = defineEmits<{
  (e: "refresh"): void;
  (e: "export"): void;
  (e: "download", name: string): void;
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
.file-list {
  width: 100%;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.file-item {
  text-align: left;
  border: 1px solid rgba(34, 211, 238, 0.24);
  border-radius: 8px;
  background: linear-gradient(135deg, rgba(8, 47, 73, 0.28), rgba(15, 23, 42, 0.5));
  color: #bae6fd;
  padding: 8px 10px;
  cursor: pointer;
  transition: all 0.2s;
}
.file-item:hover {
  border-color: rgba(45, 212, 191, 0.6);
  color: #e0f2fe;
  transform: translateY(-1px);
}
.empty-text {
  color: rgba(148, 163, 184, 0.8);
  font-size: 12px;
}
</style>

