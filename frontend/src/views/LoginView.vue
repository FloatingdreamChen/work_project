<template>
  <main class="login-page">
    <section class="login-panel">
      <div class="login-copy">
        <p class="eyebrow">GovExamAgent</p>
        <h1>考公 AI 助手</h1>
        <p>先登录进入工作台，保存画像后即可进行岗位匹配、资格风险检查和练习批改。</p>
      </div>

      <el-form class="login-form" label-position="top" @submit.prevent="handleSubmit">
        <el-form-item label="用户名">
          <el-input v-model="form.username" autocomplete="username" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" show-password autocomplete="current-password" />
        </el-form-item>
        <div class="login-actions">
          <el-button type="primary" :loading="loading" @click="handleSubmit">登录</el-button>
          <el-button :loading="loading" @click="handleRegister">注册</el-button>
        </div>
      </el-form>
    </section>
  </main>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import { login, register } from '@/api/govExam'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const form = reactive({
  username: 'demo',
  password: 'Demo@123456',
})

async function handleSubmit() {
  loading.value = true
  try {
    const data = await login(form.username, form.password)
    auth.setSession(data.access_token, data.username)
    ElMessage.success('登录成功')
    router.push('/')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  loading.value = true
  try {
    await register(form.username, form.password)
    ElMessage.success('注册成功，请登录')
  } finally {
    loading.value = false
  }
}
</script>
