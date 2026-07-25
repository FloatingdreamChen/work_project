<template>
  <div class="chat-page">
    <header class="page-heading">
      <div>
        <p class="eyebrow">AI Chat</p>
        <h2>AI 问答</h2>
      </div>
      <div class="chat-tags">
        <el-select v-model="categoryHint" class="category-select" placeholder="问题分类">
          <el-option label="自动识别" value="" />
          <el-option label="日常问答" value="daily_chat" />
          <el-option label="模糊查询" value="fuzzy_query" />
          <el-option label="优化问题" value="question_optimize" />
          <el-option label="知识问答" value="knowledge_qa" />
          <el-option label="岗位匹配" value="position_match" />
          <el-option label="备考计划" value="study_plan" />
          <el-option label="面试模拟" value="interview" />
        </el-select>
        <el-tag effect="plain">{{ lastAgent || '自动路由' }}</el-tag>
        <el-tag v-if="lastCategory" type="info" effect="plain">{{ lastCategory }}</el-tag>
      </div>
    </header>

    <main ref="messageList" class="chat-window">
      <div v-for="item in messages" :key="item.id" :class="['chat-message', `chat-message--${item.role}`]">
        <div class="chat-bubble">
          <p>{{ item.content }}</p>
          <span v-if="item.meta">{{ item.meta }}</span>
        </div>
      </div>
    </main>

    <footer class="chat-composer">
      <el-input
        v-model="draft"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 5 }"
        placeholder="输入问题，按 Enter 发送，Shift + Enter 换行"
        @keydown.enter.exact.prevent="send"
      />
      <el-button type="primary" :loading="sending" :disabled="!draft.trim()" @click="send">发送</el-button>
    </footer>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { chat, type ChatRoute } from '@/api/govExam'
import { createConversationId } from '@/composables/sampleData'

type Message = {
  id: string
  role: 'user' | 'assistant'
  content: string
  meta?: string
}

const draft = ref('')
const sending = ref(false)
const messageList = ref<HTMLElement | null>(null)
const conversationId = ref(localStorage.getItem('chat_conversation_id') || createConversationId())
const categoryHint = ref('')
const messages = ref<Message[]>([
  {
    id: createConversationId(),
    role: 'assistant',
    content: '你好，我是考公 AI 助手。你可以问我岗位匹配、备考计划、知识库资料或面试问题。',
  },
])

const lastAssistant = computed(() => [...messages.value].reverse().find((item) => item.role === 'assistant'))
const lastAgent = ref('')
const lastCategory = ref('')

async function send() {
  const content = draft.value.trim()
  if (!content || sending.value) return
  draft.value = ''
  messages.value.push({ id: createConversationId(), role: 'user', content })
  await scrollBottom()
  sending.value = true
  try {
    localStorage.setItem('chat_conversation_id', conversationId.value)
    const result = await chat(content, conversationId.value, categoryHint.value || null)
    if (result.conversation_id) {
      conversationId.value = result.conversation_id
      localStorage.setItem('chat_conversation_id', result.conversation_id)
    }
    lastAgent.value = result.agent
    lastCategory.value = categoryLabel(result.route)
    messages.value.push({
      id: createConversationId(),
      role: 'assistant',
      content: cleanAnswer(result.answer),
      meta: lastCategory.value || undefined,
    })
  } catch {
    messages.value.push({
      id: createConversationId(),
      role: 'assistant',
      content: '我这边暂时没有连接到后端服务。请确认后端正在运行，登录状态有效，然后再试一次。',
    })
  } finally {
    sending.value = false
    await scrollBottom()
  }
}

function categoryLabel(route: ChatRoute | Record<string, unknown> | null | undefined) {
  if (!route) return ''
  if (typeof route.category_label === 'string') return route.category_label
  return ''
}

function cleanAnswer(answer: string) {
  const cleaned = (answer || '')
    .replace(/LLM\s*连接失败，?已切换为本地规则兜底。?/g, '')
    .replace(/已使用本地规则和知识库生成回答。/g, '')
    .trim()
  return cleaned || '我可以继续帮你分析。请补充目标考试、岗位、地区、学习时间或具体题目，我会按你的情况给出建议。'
}

async function scrollBottom() {
  await nextTick()
  if (messageList.value) {
    messageList.value.scrollTop = messageList.value.scrollHeight
  }
}
</script>
