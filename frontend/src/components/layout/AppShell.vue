<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark">考</div>
        <div>
          <strong>考公 AI 助手</strong>
          <span>岗位与备考工作台</span>
        </div>
      </div>

      <nav class="nav-list" aria-label="主导航">
        <a class="nav-item active" href="#profile">
          <el-icon><User /></el-icon>
          <span>用户画像</span>
        </a>
        <a class="nav-item" href="#positions">
          <el-icon><Briefcase /></el-icon>
          <span>岗位匹配</span>
        </a>
        <a class="nav-item" href="#practice">
          <el-icon><EditPen /></el-icon>
          <span>练习批改</span>
        </a>
        <a class="nav-item" href="#knowledge">
          <el-icon><Collection /></el-icon>
          <span>知识库</span>
        </a>
        <a class="nav-item" href="#history">
          <el-icon><Notebook /></el-icon>
          <span>练习历史</span>
        </a>
      </nav>
    </aside>

    <main class="main-panel">
      <header class="topbar">
        <div>
          <p class="eyebrow">本地开发环境</p>
          <h1>报考决策与备考推进</h1>
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
import { Briefcase, Collection, EditPen, Notebook, SwitchButton, User } from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
