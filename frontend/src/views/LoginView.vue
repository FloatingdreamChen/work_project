<template>
  <main class="login-page login-red-theme" @pointermove="handlePointerMove" @pointerleave="resetPointer">
    <canvas ref="ribbonCanvas" class="red-ribbon-canvas" aria-hidden="true" />
    <div class="red-silk-vignette" aria-hidden="true" />

    <section class="login-ceremony" aria-label="考公 AI 助手登录">
      <div class="ribbon-title-wrap" aria-hidden="true">
        <p class="ribbon-title">治国平天下 起航在今朝</p>
      </div>

      <article class="login-panel login-glass-card">
        <div class="login-copy">
          <p class="eyebrow">GovExamAgent</p>
          <h1>考公 AI 助手</h1>
          <p>登录后进入岗位匹配、资格风险检查、知识库问答和个性化备考工作台。</p>
        </div>

        <el-form class="login-form" label-position="top" @submit.prevent="submitCurrentMode">
          <el-form-item label="用户名">
            <el-input v-model="form.username" autocomplete="username" placeholder="请输入用户名或邮箱" />
          </el-form-item>
          <el-form-item v-if="mode === 'register'" label="邮箱">
            <el-input v-model="form.email" autocomplete="email" placeholder="用于注册和找回账号" />
          </el-form-item>
          <el-form-item label="密码">
            <el-input
              v-model="form.password"
              type="password"
              show-password
              :autocomplete="mode === 'login' ? 'current-password' : 'new-password'"
              placeholder="至少 8 位，包含大小写字母和数字"
            />
          </el-form-item>
          <el-form-item label="验证码">
            <div class="captcha-row">
              <el-input v-model="form.captcha" inputmode="numeric" placeholder="请输入结果" @keydown.enter="submitCurrentMode" />
              <button class="captcha-chip" type="button" title="点击刷新验证码" @click="refreshCaptcha">
                {{ captcha.question }}
              </button>
            </div>
          </el-form-item>

          <div class="login-extra">
            <el-checkbox v-model="rememberAccount">记住账号</el-checkbox>
            <button class="text-button" type="button" @click="toggleMode">
              {{ mode === 'login' ? '创建账号' : '返回登录' }}
            </button>
          </div>

          <div class="login-actions">
            <el-button class="gold-login-button" type="primary" :loading="loading" @click="submitCurrentMode">
              {{ mode === 'login' ? '登录' : '注册' }}
            </el-button>
          </div>
        </el-form>
      </article>
    </section>
  </main>
</template>

<script setup lang="ts">
import { onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import { login, register } from '@/api/govExam'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
const loading = ref(false)
const mode = ref<'login' | 'register'>('login')
const rememberAccount = ref(localStorage.getItem('remember_login') === '1')
const ribbonCanvas = ref<HTMLCanvasElement | null>(null)
const captcha = reactive(createCaptcha())
const form = reactive({
  username: localStorage.getItem('remember_username') || '',
  email: '',
  password: '',
  captcha: '',
})

let rafId = 0
let startTime = 0
let pointerX = 0
let pointerY = 0
let targetPointerX = 0
let targetPointerY = 0
let reduceMotion = false

onMounted(() => {
  reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  setupRibbonCanvas()
  window.addEventListener('resize', setupRibbonCanvas)
})

onBeforeUnmount(() => {
  cancelAnimationFrame(rafId)
  window.removeEventListener('resize', setupRibbonCanvas)
})

async function handleSubmit() {
  if (!validateLoginForm()) return
  loading.value = true
  try {
    const data = await login(form.username.trim(), form.password)
    auth.setSession(data.access_token, data.refresh_token, data.username, data.role)
    persistRememberedLogin()
    sessionStorage.setItem('play_login_entry_transition', '1')
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '登录失败，请检查用户名和密码')
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  if (!validateRegisterForm()) return
  loading.value = true
  try {
    await register(form.username.trim(), form.email.trim(), form.password)
    ElMessage.success('注册成功，请登录')
    mode.value = 'login'
    form.captcha = ''
    refreshCaptcha()
  } catch (error) {
    ElMessage.error(error instanceof Error ? error.message : '注册失败，请检查输入内容')
    refreshCaptcha()
  } finally {
    loading.value = false
  }
}

function submitCurrentMode() {
  if (mode.value === 'login') {
    handleSubmit()
    return
  }
  handleRegister()
}

function toggleMode() {
  mode.value = mode.value === 'login' ? 'register' : 'login'
  refreshCaptcha()
}

function validateCaptcha() {
  if (!form.captcha.trim() || Number(form.captcha) !== captcha.answer) {
    ElMessage.warning('验证码不正确，请重新输入')
    refreshCaptcha()
    return false
  }
  return true
}

function validateLoginForm() {
  if (!form.username.trim()) {
    ElMessage.warning('请输入用户名或邮箱')
    return false
  }
  if (!form.password) {
    ElMessage.warning('请输入密码')
    return false
  }
  return validateCaptcha()
}

function validateRegisterForm() {
  if (!form.username.trim() || form.username.trim().length < 3) {
    ElMessage.warning('用户名至少 3 个字符')
    return false
  }
  if (!isValidEmail(form.email)) {
    ElMessage.warning('请输入正确的邮箱地址')
    return false
  }
  if (!isValidPassword(form.password)) {
    ElMessage.warning('密码至少 8 位，并且必须包含大写字母、小写字母和数字')
    return false
  }
  return validateCaptcha()
}

function isValidEmail(value: string) {
  return /^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(value.trim())
}

function isValidPassword(value: string) {
  return value.length >= 8 && /[a-z]/.test(value) && /[A-Z]/.test(value) && /\d/.test(value)
}

function refreshCaptcha() {
  Object.assign(captcha, createCaptcha())
  form.captcha = ''
}

function createCaptcha() {
  const left = Math.floor(3 + Math.random() * 7)
  const right = Math.floor(2 + Math.random() * 8)
  return {
    question: `${left} + ${right} = ?`,
    answer: left + right,
  }
}

function persistRememberedLogin() {
  localStorage.setItem('remember_login', rememberAccount.value ? '1' : '0')
  if (rememberAccount.value) {
    localStorage.setItem('remember_username', form.username)
    return
  }
  localStorage.removeItem('remember_username')
}

function handlePointerMove(event: PointerEvent) {
  const width = window.innerWidth || 1
  const height = window.innerHeight || 1
  targetPointerX = (event.clientX / width - 0.5) * 2
  targetPointerY = (event.clientY / height - 0.5) * 2
}

function resetPointer() {
  targetPointerX = 0
  targetPointerY = 0
}

function setupRibbonCanvas() {
  const canvas = ribbonCanvas.value
  if (!canvas) return
  const ratio = Math.min(window.devicePixelRatio || 1, 2)
  canvas.width = Math.floor(window.innerWidth * ratio)
  canvas.height = Math.floor(window.innerHeight * ratio)
  canvas.style.width = `${window.innerWidth}px`
  canvas.style.height = `${window.innerHeight}px`
  const context = canvas.getContext('2d')
  if (!context) return
  context.setTransform(ratio, 0, 0, ratio, 0, 0)
  cancelAnimationFrame(rafId)
  startTime = performance.now()
  drawRibbon(context, canvas)
}

function drawRibbon(context: CanvasRenderingContext2D, canvas: HTMLCanvasElement) {
  const width = window.innerWidth
  const height = window.innerHeight
  const now = performance.now()
  const elapsed = (now - startTime) / 1000
  const intro = reduceMotion ? 1 : Math.min(1, elapsed / 2.25)
  const flow = reduceMotion ? 2.25 : elapsed
  pointerX += (targetPointerX - pointerX) * 0.045
  pointerY += (targetPointerY - pointerY) * 0.045

  context.clearRect(0, 0, width, height)
  paintBackground(context, width, height, flow)
  paintRibbon(context, width, height, flow, intro, 0, 92, 0.98)
  paintRibbon(context, width, height, flow + 0.9, intro, -150, 42, 0.46)
  paintRibbon(context, width, height, flow + 1.8, intro, 160, 38, 0.34)
  paintGoldDust(context, width, height, flow)

  if (!reduceMotion) {
    rafId = requestAnimationFrame(() => drawRibbon(context, canvas))
  }
}

function paintBackground(context: CanvasRenderingContext2D, width: number, height: number, time: number) {
  const gradient = context.createLinearGradient(0, 0, width, height)
  gradient.addColorStop(0, '#2B0A0A')
  gradient.addColorStop(0.52, '#5C0E0E')
  gradient.addColorStop(1, '#190606')
  context.fillStyle = gradient
  context.fillRect(0, 0, width, height)

  context.save()
  context.globalAlpha = 0.12
  for (let i = 0; i < 5; i += 1) {
    const y = height * (0.12 + i * 0.2) + Math.sin(time * 0.45 + i) * 18
    context.beginPath()
    context.moveTo(-60, y)
    context.bezierCurveTo(width * 0.25, y - 80, width * 0.72, y + 95, width + 80, y - 30)
    context.strokeStyle = i % 2 ? '#D4AF37' : '#C8102E'
    context.lineWidth = 1
    context.stroke()
  }
  context.restore()
}

function paintRibbon(
  context: CanvasRenderingContext2D,
  width: number,
  height: number,
  time: number,
  intro: number,
  offsetY: number,
  thickness: number,
  alpha: number,
) {
  const eased = easeOutCubic(intro)
  const scale = 0.32 + eased * 0.78
  const depthY = (1 - eased) * height * 0.24
  const centerY = height * 0.45 + offsetY + depthY + pointerY * 18
  const startX = -width * 0.16 + (1 - eased) * width * 0.32
  const endX = width * 1.16 - (1 - eased) * width * 0.18
  const pointsTop: Array<[number, number]> = []
  const pointsBottom: Array<[number, number]> = []
  const segments = 96

  for (let i = 0; i <= segments; i += 1) {
    const p = i / segments
    const x = startX + (endX - startX) * p + pointerX * 26 * (p - 0.5)
    const wave = Math.sin(p * Math.PI * 3.1 + time * 1.18) * 34 * scale
    const fold = Math.sin(p * Math.PI * 8.4 - time * 1.7) * 12 * scale
    const y = centerY + wave + fold
    const localThickness = thickness * scale * (0.7 + Math.sin(p * Math.PI) * 0.42)
    pointsTop.push([x, y - localThickness / 2])
    pointsBottom.push([x, y + localThickness / 2])
  }

  const ribbonGradient = context.createLinearGradient(0, centerY - thickness, width, centerY + thickness)
  ribbonGradient.addColorStop(0, `rgba(112, 0, 13, ${alpha})`)
  ribbonGradient.addColorStop(0.18, `rgba(200, 16, 46, ${alpha})`)
  ribbonGradient.addColorStop(0.48, `rgba(237, 42, 68, ${alpha})`)
  ribbonGradient.addColorStop(0.68, `rgba(172, 8, 33, ${alpha})`)
  ribbonGradient.addColorStop(1, `rgba(97, 0, 16, ${alpha})`)

  context.save()
  context.shadowColor = 'rgba(255, 0, 40, 0.42)'
  context.shadowBlur = 28 * scale
  context.beginPath()
  pointsTop.forEach(([x, y], index) => {
    if (index === 0) context.moveTo(x, y)
    else context.lineTo(x, y)
  })
  pointsBottom.reverse().forEach(([x, y]) => context.lineTo(x, y))
  context.closePath()
  context.fillStyle = ribbonGradient
  context.fill()
  context.clip()

  for (let i = 0; i < 9; i += 1) {
    const shineY = centerY - thickness * scale + i * thickness * scale * 0.28 + Math.sin(time + i) * 6
    context.beginPath()
    context.moveTo(-80, shineY)
    context.bezierCurveTo(width * 0.3, shineY - 40, width * 0.72, shineY + 46, width + 80, shineY - 14)
    context.strokeStyle = i % 3 === 0 ? 'rgba(255, 220, 120, 0.2)' : 'rgba(255, 255, 255, 0.1)'
    context.lineWidth = i % 3 === 0 ? 2.2 : 1
    context.stroke()
  }
  context.restore()
}

function paintGoldDust(context: CanvasRenderingContext2D, width: number, height: number, time: number) {
  context.save()
  for (let i = 0; i < 70; i += 1) {
    const seed = i * 37.17
    const x = (seed * 19 + time * (8 + (i % 5))) % (width + 120) - 60
    const y = height * (0.08 + ((seed * 7) % 86) / 100) + Math.sin(time * 0.65 + seed) * 14
    const radius = 0.8 + (i % 4) * 0.35
    context.globalAlpha = 0.18 + ((i % 7) / 7) * 0.28
    context.fillStyle = '#D4AF37'
    context.beginPath()
    context.arc(x, y, radius, 0, Math.PI * 2)
    context.fill()
  }
  context.restore()
}

function easeOutCubic(value: number) {
  return 1 - Math.pow(1 - value, 3)
}
</script>
