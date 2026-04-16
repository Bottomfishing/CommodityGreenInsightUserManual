import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  { path: '/', redirect: '/run' },
  { path: '/run', component: () => import('@/views/RunView.vue'), meta: { tab: 'run' } },
  { path: '/monitor/:runId?', component: () => import('@/views/MonitorView.vue'), meta: { tab: 'monitor' } },
  { path: '/results/:runId?', component: () => import('@/views/ResultsView.vue'), meta: { tab: 'results' } },
  { path: '/download/:runId?', component: () => import('@/views/DownloadView.vue'), meta: { tab: 'download' } },
]

export default createRouter({
  history: createWebHistory(),
  routes
})
