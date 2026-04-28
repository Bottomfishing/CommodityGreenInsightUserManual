import { createRouter, createWebHashHistory } from 'vue-router'
import { getToken } from '@/api/auth'

const router = createRouter({
  history: createWebHashHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LandingView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/',
      name: 'Landing',
      component: () => import('@/views/LandingView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro',
      name: 'Intro',
      component: () => import('@/views/IntroView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/charts',
      name: 'IntroCharts',
      component: () => import('@/views/IntroChartsView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/data',
      name: 'IntroData',
      component: () => import('@/views/IntroDataView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/globe',
      name: 'IntroGlobe',
      component: () => import('@/views/IntroGlobeView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/predict',
      name: 'IntroPredict',
      component: () => import('@/views/IntroPredictView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/green-forecast',
      name: 'IntroGreenForecast',
      component: () => import('@/views/IntroGreenForecastView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/derivation',
      name: 'IntroDerivation',
      component: () => import('@/views/IntroDerivationView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/ai',
      name: 'IntroAI',
      component: () => import('@/views/IntroAIView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/intro/welcome',
      name: 'IntroWelcome',
      component: () => import('@/views/IntroWelcomeView.vue'),
      meta: { requiresAuth: false },
    },
    {
      path: '/home',
      name: 'Home',
      component: () => import('@/views/HomeView.vue'),
      meta: { requiresAuth: true },
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

// 导航守卫：已登录访问落地页 → 自动跳 /home
router.beforeEach((to) => {
  const token = getToken()
  // Intro 链路优先：任何 /intro/* 路径都允许直接访问，避免被其他逻辑重定向覆盖
  if (to.path.startsWith('/intro')) {
    return true
  }
  // 兜底：若异常跳回 Landing，但当前 URL 仍是 intro 链路，则强制拉回地球页
  if (to.name === 'Landing' && window.location.hash.startsWith('#/intro')) {
    return { path: '/intro/globe' }
  }
  if (to.meta.requiresAuth && !token) {
    return { name: 'Landing' }
  }
  // Landing 页面自己会处理 token 跳转逻辑（在 onMounted 里）
})

export default router
