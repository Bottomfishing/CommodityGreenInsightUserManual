<template>
  <div>
    <h2 class="section-h2">下载/导出</h2>

    <!-- 空状态 -->
    <template v-if="!selectedRunId">
      <div class="empty-state">
        <div class="empty-title">先在「运行」里跑一次</div>
        <div class="empty-desc">或者在左侧选择一个历史输出目录。</div>
      </div>
    </template>

    <template v-else>
      <p style="font-size:0.78rem;color:var(--text-muted);margin-bottom:0.75rem;">
        当前目录：<code>{{ selectedRunId }}</code>
      </p>

      <!-- loading -->
      <div v-if="loading" style="text-align:center;padding:2rem;">
        <span class="spinner"></span> 加载文件列表…
      </div>

      <!-- 无文件 -->
      <div v-else-if="!files.length" class="alert alert-info">
        没有找到输出文件。
      </div>

      <!-- 文件列表 -->
      <template v-else>
        <p style="font-size:0.88rem;margin-bottom:0.75rem;">
          点击按钮下载文件（CSV / PNG / H5 / LOG）：
        </p>

        <div v-for="file in files" :key="file.name" class="file-item">
          <div>
            <div class="file-name">{{ file.name }}</div>
            <div class="file-size">{{ formatSize(file.size) }}</div>
          </div>
          <button
            class="btn btn-secondary"
            style="padding:0.3rem 0.75rem;font-size:0.82rem;"
            @click="handleDownload(file.name)"
          >
            下载
          </button>
        </div>

        <hr class="divider" />

        <!-- ZIP 整包导出 -->
        <div style="display:flex;align-items:center;gap:1rem;">
          <a :href="getZipUrl()" class="btn btn-primary" :download="selectedRunId + '.zip'">
            📦 导出整包 ZIP
          </a>
          <span style="font-size:0.82rem;color:var(--text-muted);">
            将当前输出目录中所有文件打包为 zip 下载
          </span>
        </div>
      </template>
    </template>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { fetchFiles, downloadOilRunFile } from '../api/index.js'

const props = defineProps({
  selectedRunId: String,
})

const files = ref([])
const loading = ref(false)

async function loadFiles() {
  if (!props.selectedRunId) return
  loading.value = true
  files.value = []
  try {
    const data = await fetchFiles(props.selectedRunId)
    files.value = Array.isArray(data) ? data : (data.files || [])
  } catch(e) {
    files.value = []
  } finally {
    loading.value = false
  }
}

function formatSize(bytes) {
  if (!bytes) return '--'
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
}

async function handleDownload(name) {
  if (!props.selectedRunId) return
  try {
    await downloadOilRunFile(props.selectedRunId, name)
  } catch (e) {}
}

function getZipUrl() {
  return `/api/oil/runs/${props.selectedRunId}/export.zip`
}

watch(() => props.selectedRunId, (v) => {
  if (v) loadFiles()
})

onMounted(() => {
  if (props.selectedRunId) loadFiles()
})
</script>
