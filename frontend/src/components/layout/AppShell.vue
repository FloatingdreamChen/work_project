<template>
  <div class="app-shell">
    <div v-if="showEntryTransition" class="entry-ribbon-transition" aria-hidden="true">
      <svg class="entry-ribbon-svg" viewBox="0 0 1400 760" preserveAspectRatio="none">
        <defs>
          <linearGradient id="entryRibbonRed" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stop-color="#7a0618" />
            <stop offset="26%" stop-color="#c8102e" />
            <stop offset="52%" stop-color="#f04c59" />
            <stop offset="76%" stop-color="#b90727" />
            <stop offset="100%" stop-color="#6f0014" />
          </linearGradient>
          <linearGradient id="entryRibbonGold" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%" stop-color="#9d7412" />
            <stop offset="45%" stop-color="#fff1a8" />
            <stop offset="100%" stop-color="#d4af37" />
          </linearGradient>
        </defs>
        <path
          class="entry-ribbon-main"
          d="M-180 455 C 118 170, 408 660, 713 360 C 980 96, 1162 424, 1580 256 L 1580 396 C 1204 548, 970 230, 724 494 C 432 806, 122 332, -180 590 Z"
        />
        <path
          class="entry-ribbon-highlight"
          d="M-160 482 C 158 248, 412 596, 706 386 C 988 182, 1198 410, 1540 286"
        />
      </svg>
      <div class="entry-ribbon-caption">起航</div>
    </div>

    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">考</div>
        <div>
          <strong>考公 AI 助手</strong>
          <span>岗位与备考工作台</span>
        </div>
      </div>

      <nav class="nav-list" aria-label="主导航">
        <router-link class="nav-item" to="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>AI 问答</span>
        </router-link>
        <router-link class="nav-item" to="/profile">
          <el-icon><User /></el-icon>
          <span>用户画像</span>
        </router-link>
        <router-link class="nav-item" to="/positions">
          <el-icon><Briefcase /></el-icon>
          <span>岗位匹配</span>
        </router-link>
        <router-link class="nav-item" to="/study-plan">
          <el-icon><Calendar /></el-icon>
          <span>备考计划</span>
        </router-link>
        <router-link class="nav-item" to="/knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </router-link>
        <router-link class="nav-item" to="/history">
          <el-icon><Notebook /></el-icon>
          <span>阶段记录</span>
        </router-link>
      </nav>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div>
          <p class="eyebrow">本地开发环境</p>
          <h1>{{ routeTitle }}</h1>
        </div>
        <div class="top-actions">
          <el-tag type="success" effect="plain">FastAPI / Vue</el-tag>
          <el-button :icon="SwitchButton" @click="handleLogout">退出</el-button>
        </div>
      </header>

      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { Briefcase, Calendar, ChatDotRound, Collection, Notebook, SwitchButton, User } from '@element-plus/icons-vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const auth = useAuthStore()
const showEntryTransition = ref(false)
let transitionTimer = 0

const titles: Record<string, string> = {
  chat: 'AI 问答',
  profile: '用户画像',
  positions: '岗位匹配',
  'study-plan': '个性化备考计划',
  knowledge: '知识库与 RAG',
  history: '阶段记录',
}

const routeTitle = computed(() => titles[String(route.name)] || '考公 AI 助手')

onMounted(() => {
  const shouldPlay = sessionStorage.getItem('play_login_entry_transition') === '1'
  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  sessionStorage.removeItem('play_login_entry_transition')
  if (!shouldPlay || reduceMotion) return
  showEntryTransition.value = true
  transitionTimer = window.setTimeout(() => {
    showEntryTransition.value = false
  }, 1650)
})

onBeforeUnmount(() => {
  window.clearTimeout(transitionTimer)
})

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
