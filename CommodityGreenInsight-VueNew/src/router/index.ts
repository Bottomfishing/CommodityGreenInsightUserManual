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
