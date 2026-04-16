import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api'

export const useAppStore = defineStore('app', () => {
  // 全局状态
  const systemStatus = ref(null)
  const runList = ref([])
  const selectedRunId = ref(null)
  const theme = ref(localStorage.getItem('theme') || 'light')

  // 计算属性
  const isGlobalBusy = computed(() => systemStatus.value?.global_busy || false)
  const selectedRun = computed(() => runList.value.find(r => r.run_id === selectedRunId.value))
  const runCount = computed(() => systemStatus.value?.run_count || 0)

  // 主题切换
  function toggleTheme() {
    theme.value = theme.value === 'light' ? 'dark' : 'light'
    localStorage.setItem('theme', theme.value)
    document.documentElement.setAttribute('data-theme', theme.value)
  }
  function initTheme() {
    document.documentElement.setAttribute('data-theme', theme.value)
  }

  // 加载系统状态
  async function loadSystemStatus() {
    try {
      systemStatus.value = await api.getSystemStatus()
    } catch (e) { /* ignore */ }
  }

  // 加载运行列表
  async function loadRunList() {
    try {
      const res = await api.listOilRuns(30)
      runList.value = res.items || []
      // 如果还没选，自动选最新
      if (!selectedRunId.value && runList.value.length > 0) {
        selectedRunId.value = runList.value[0].run_id
      }
    } catch (e) { /* ignore */ }
  }

  // 选中run
  function selectRun(runId) {
    selectedRunId.value = runId
  }

  return {
    systemStatus, runList, selectedRunId, selectedRun,
    theme, isGlobalBusy, runCount,
    toggleTheme, initTheme,
    loadSystemStatus, loadRunList, selectRun
  }
})
