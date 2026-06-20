import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTenantStore } from '@/stores/tenant'

const router = createRouter({
  history: createWebHistory('/app/'),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/LoginView.vue'),
      meta: { guest: true, title: '登录' },
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/RegisterView.vue'),
      meta: { guest: true, title: '注册' },
    },
    {
      path: '/',
      component: () => import('@/components/AppLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        { path: '', redirect: '/chat' },
        {
          path: 'chat',
          name: 'Chat',
          component: () => import('@/views/ChatView.vue'),
          meta: { title: '知识库对话' },
        },
        {
          path: 'llm-chat',
          name: 'LlmChat',
          component: () => import('@/views/LlmChatView.vue'),
          meta: { title: 'LLM 对话' },
        },
        {
          path: 'kb',
          name: 'KbList',
          component: () => import('@/views/KbListView.vue'),
          meta: { title: '知识库管理' },
        },
        {
          path: 'kb/:name',
          name: 'KbDetail',
          component: () => import('@/views/KbDetailView.vue'),
          meta: { title: '知识库详情' },
        },
        {
          path: 'tenants',
          name: 'TenantList',
          component: () => import('@/views/TenantListView.vue'),
          meta: { title: '租户管理' },
        },
        {
          path: 'tenants/:id',
          name: 'TenantDetail',
          component: () => import('@/views/TenantDetailView.vue'),
          meta: { title: '租户成员' },
        },
        {
          path: 'users',
          name: 'UserList',
          component: () => import('@/views/UserListView.vue'),
          meta: { title: '用户管理', requireSuperuser: true },
        },
        {
          path: 'mcp',
          name: 'McpConfig',
          component: () => import('@/views/McpConfigView.vue'),
          meta: { title: 'MCP 配置' },
        },
        {
          path: 'history',
          name: 'History',
          component: () => import('@/views/HistoryView.vue'),
          meta: { title: '对话历史' },
        },
      ],
    },
  ],
})

router.beforeEach(async (to, _from, next) => {
  const auth = useAuthStore()

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return next('/login')
  }

  if (to.meta.guest && auth.isAuthenticated) {
    return next('/')
  }

  if (auth.isAuthenticated && !auth.user) {
    try {
      await auth.fetchUser()
    } catch {
      return next('/login')
    }
  }

  if (to.meta.requireSuperuser && !auth.isSuperuser) {
    return next('/')
  }

  if (auth.isAuthenticated) {
    const tenant = useTenantStore()
    if (tenant.tenants.length === 0) {
      await tenant.fetchTenants()
    }
  }

  next()
})

router.afterEach((to) => {
  document.title = `${to.meta.title || ''} - Langchain ChatChat`
})

export default router
