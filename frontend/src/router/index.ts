import { createRouter, createWebHistory } from 'vue-router'

import AppShell from '@/components/layout/AppShell.vue'
import { useAuthStore } from '@/stores/auth'
import ChatView from '@/views/ChatView.vue'
import HistoryView from '@/views/HistoryView.vue'
import KnowledgeView from '@/views/KnowledgeView.vue'
import LoginView from '@/views/LoginView.vue'
import PositionsView from '@/views/PositionsView.vue'
import ProfileView from '@/views/ProfileView.vue'
import StudyPlanView from '@/views/StudyPlanView.vue'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true },
    },
    {
      path: '/',
      component: AppShell,
      children: [
        {
          path: '',
          redirect: '/chat',
        },
        {
          path: 'chat',
          name: 'chat',
          component: ChatView,
        },
        {
          path: 'profile',
          name: 'profile',
          component: ProfileView,
        },
        {
          path: 'positions',
          name: 'positions',
          component: PositionsView,
        },
        {
          path: 'study-plan',
          name: 'study-plan',
          component: StudyPlanView,
        },
        {
          path: 'knowledge',
          name: 'knowledge',
          component: KnowledgeView,
        },
        {
          path: 'history',
          name: 'history',
          component: HistoryView,
        },
      ],
    },
    {
      path: '/:pathMatch(.*)*',
      redirect: '/',
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.public) {
    return auth.isLoggedIn ? '/' : true
  }
  return auth.isLoggedIn ? true : '/login'
})

export default router
