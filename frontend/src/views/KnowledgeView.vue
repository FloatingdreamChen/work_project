<template>
  <div class="workbench">
    <section class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Knowledge</p>
        <h2>知识库与 RAG</h2>
        <p>查看本地模型、向量检索状态，并检索政策和备考知识。</p>
      </div>
      <div class="tool-card">
        <div class="toolbar">
          <el-button :icon="Search" :loading="loading" @click="loadStatus">刷新状态</el-button>
          <el-tag :type="status?.vector_rag_ready ? 'success' : 'warning'">
            {{ status?.vector_rag_ready ? '向量 RAG 就绪' : '关键词兜底' }}
          </el-tag>
          <el-tag :type="status?.local_semantic_rag_ready ? 'success' : 'info'">
            {{ status?.local_semantic_rag_ready ? '本地语义 RAG 就绪' : '本地语义未就绪' }}
          </el-tag>
        </div>
        <div class="status-grid">
          <div v-for="[name, item] in modelEntries" :key="name">
            <strong>{{ name }}</strong>
            <span>{{ item.exists ? `${item.size_mb} MB` : '未安装' }}</span>
            <p>{{ item.exists ? item.path : item.missing_files.join('；') }}</p>
          </div>
        </div>
        <div class="toolbar">
          <el-input v-model="query" placeholder="例如：应届生身份如何认定" @keydown.enter="search" />
          <el-button type="primary" :loading="searching" @click="search">检索</el-button>
        </div>
        <el-table :data="results" height="360" empty-text="暂无知识库结果">
          <el-table-column prop="source_name" label="来源" width="180" />
          <el-table-column prop="content" label="片段" min-width="420" show-overflow-tooltip />
          <el-table-column prop="score" label="分数" width="90" />
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { Search } from '@element-plus/icons-vue'
import { getKnowledgeStatus, searchKnowledge } from '@/api/govExam'

const loading = ref(false)
const searching = ref(false)
const status = ref<Awaited<ReturnType<typeof getKnowledgeStatus>> | null>(null)
const query = ref('应届生身份认定')
const results = ref<Awaited<ReturnType<typeof searchKnowledge>>>([])
const modelEntries = computed(() => Object.entries(status.value?.models || {}))

onMounted(loadStatus)

async function loadStatus() {
  loading.value = true
  try {
    status.value = await getKnowledgeStatus()
  } finally {
    loading.value = false
  }
}

async function search() {
  if (!query.value.trim()) return
  searching.value = true
  try {
    results.value = await searchKnowledge({ query: query.value, top_k: 5 })
  } finally {
    searching.value = false
  }
}
</script>
