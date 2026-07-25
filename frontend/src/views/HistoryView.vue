<template>
  <div class="workbench">
    <section class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">History</p>
        <h2>阶段记录</h2>
        <p>查看阶段报告和错题沉淀；练习批改入口已暂时移除。</p>
      </div>
      <div class="tool-card">
        <div class="toolbar">
          <el-select v-model="days" class="compact-select" @change="loadAll">
            <el-option label="近 7 天" :value="7" />
            <el-option label="近 30 天" :value="30" />
            <el-option label="近 90 天" :value="90" />
          </el-select>
          <el-button :icon="Refresh" :loading="loading" @click="loadAll">刷新</el-button>
        </div>

        <div class="report-summary">
          <div>
            <span>练习次数</span>
            <strong>{{ report?.practice_count ?? 0 }}</strong>
          </div>
          <div>
            <span>平均得分</span>
            <strong>{{ report?.average_score ?? '暂无' }}</strong>
          </div>
          <div>
            <span>记录周期</span>
            <strong>{{ report?.days ?? days }} 天</strong>
          </div>
        </div>

        <div class="dual-grid">
          <div class="plain-panel">
            <h3>阶段建议</h3>
            <el-empty v-if="!report?.suggestions.length" description="暂无阶段建议" />
            <ul v-else class="simple-list">
              <li v-for="item in report.suggestions" :key="item">{{ item }}</li>
            </ul>
          </div>
          <div class="plain-panel">
            <h3>高频问题</h3>
            <el-empty v-if="!report?.top_problem_keywords.length" description="暂无高频问题" />
            <ul v-else class="simple-list">
              <li v-for="item in report.top_problem_keywords" :key="item.keyword">
                {{ item.keyword }}：{{ item.count }} 次
              </li>
            </ul>
          </div>
        </div>

        <el-table :data="wrongQuestions" height="320" empty-text="暂无错题记录">
          <el-table-column prop="module_name" label="模块" width="150" />
          <el-table-column prop="question" label="题目" min-width="260" show-overflow-tooltip />
          <el-table-column prop="problem_summary" label="问题摘要" min-width="260" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="110" />
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { Refresh } from '@element-plus/icons-vue'
import { getStudyReport, listWrongQuestions } from '@/api/govExam'

const days = ref(30)
const loading = ref(false)
const report = ref<Awaited<ReturnType<typeof getStudyReport>> | null>(null)
const wrongQuestions = ref<Array<Record<string, unknown>>>([])

onMounted(loadAll)

async function loadAll() {
  loading.value = true
  try {
    const [reportResult, wrongResult] = await Promise.all([
      getStudyReport(days.value).catch(() => ({
        days: days.value,
        practice_count: 0,
        by_type: {},
        by_module: {},
        average_score: undefined,
        top_problem_keywords: [],
        suggestions: ['暂无练习记录，完成一次练习后这里会生成阶段建议。'],
        recent: [],
      })),
      listWrongQuestions({ status: 'open', limit: 50 }).catch(() => []),
    ])
    report.value = reportResult
    wrongQuestions.value = wrongResult
  } finally {
    loading.value = false
  }
}
</script>
