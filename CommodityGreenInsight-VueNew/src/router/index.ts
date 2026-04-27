import { createRouter, createWebHistory } from 'vue-router'
import { getToken } from '@/api/auth'

const router = createRouter({
  history: createWebHistory(),
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
  if (to.meta.requiresAuth && !token) {
    return { name: 'Landing' }
  }
  // Landing 页面自己会处理 token 跳转逻辑（在 onMounted 里）
})

export default router
