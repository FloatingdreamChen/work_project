<template>
  <div class="workbench">
    <section class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Study Plan</p>
        <h2>个性化备考计划</h2>
        <p>按考试日期、学习时间、基础水平和薄弱模块倒排计划，少于三个月会提示风险。</p>
      </div>
      <div class="tool-card">
        <div class="form-grid">
          <el-form-item label="考试日期"><el-date-picker v-model="form.exam_date" type="date" value-format="YYYY-MM-DD" /></el-form-item>
          <el-form-item label="每日学习小时"><el-input-number v-model="form.daily_hours" :min="0.5" :max="12" :step="0.5" /></el-form-item>
          <el-form-item label="每周学习天数"><el-input-number v-model="form.weekly_days" :min="1" :max="7" /></el-form-item>
          <el-form-item label="当前基础">
            <el-select v-model="form.foundation_level">
              <el-option label="零基础" value="零基础" />
              <el-option label="一般" value="一般" />
              <el-option label="有基础" value="有基础" />
              <el-option label="较好" value="较好" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标岗位"><el-input v-model="form.target_position" placeholder="税务 / 海关 / 选调等" /></el-form-item>
          <el-form-item label="薄弱模块">
            <el-select v-model="form.weak_modules" multiple collapse-tags>
              <el-option v-for="item in moduleOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </div>
        <div class="toolbar">
          <el-button type="primary" :loading="planning" @click="buildPlan">生成计划</el-button>
          <el-button :loading="loadingReport" @click="loadReport">阶段报告</el-button>
        </div>
        <div v-if="studyPlan" class="plan-box">
          <el-alert v-if="studyPlan.warning" :title="studyPlan.warning" type="warning" :closable="false" />
          <div class="plan-summary">
            <strong>{{ studyPlan.planned_weeks }}周 / {{ studyPlan.planned_days }}天</strong>
            <span>每周约 {{ studyPlan.weekly_hours }} 小时</span>
          </div>
          <div class="weight-grid">
            <span v-for="(weight, key) in studyPlan.module_weights" :key="key">{{ key }} {{ Math.round(weight * 100) }}%</span>
          </div>
          <el-timeline>
            <el-timeline-item v-for="week in studyPlan.weekly_plan.slice(0, 8)" :key="week.week" :timestamp="`第${week.week}周`">
              <strong>{{ week.phase }}｜{{ week.focus }}</strong>
              <p>{{ week.tasks.slice(0, 3).join('；') }}</p>
            </el-timeline-item>
          </el-timeline>
        </div>
        <div v-if="studyReport" class="review-box">
          <strong>近{{ studyReport.days }}天练习：{{ studyReport.practice_count }}次</strong>
          <p>均分：{{ studyReport.average_score || '暂无' }}</p>
          <p>建议：{{ studyReport.suggestions.join('；') }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { buildStudyPlan, getProfile, getStudyReport, type Profile } from '@/api/govExam'
import { moduleOptions } from '@/composables/sampleData'

const planning = ref(false)
const loadingReport = ref(false)
const studyPlan = ref<Awaited<ReturnType<typeof buildStudyPlan>>['plan'] | null>(null)
const studyReport = ref<Awaited<ReturnType<typeof getStudyReport>> | null>(null)
const form = reactive({
  exam_date: '2027-11-28',
  daily_hours: 2,
  weekly_days: 6,
  foundation_level: '一般',
  target_position: '税务系统',
  weak_modules: ['行测-数量关系', '申论-大作文'],
})

async function buildPlan() {
  planning.value = true
  try {
    const profile: Profile = await getProfile().catch(() => ({}))
    const result = await buildStudyPlan({
      target_exam: profile.target_exam || '公务员考试',
      exam_date: form.exam_date,
      target_position: form.target_position,
      province: profile.target_region,
      daily_hours: form.daily_hours,
      weekly_days: form.weekly_days,
      foundation_level: form.foundation_level,
      weak_modules: form.weak_modules,
      include_interview: true,
      notes: `${profile.major || ''} ${profile.fresh_graduate_status || ''}`,
    })
    studyPlan.value = result.plan
  } catch {
    ElMessage.error('备考计划生成失败')
  } finally {
    planning.value = false
  }
}

async function loadReport() {
  loadingReport.value = true
  try {
    studyReport.value = await getStudyReport(30)
  } catch {
    studyReport.value = {
      days: 30,
      practice_count: 0,
      by_type: {},
      by_module: {},
      average_score: undefined,
      top_problem_keywords: [],
      suggestions: ['暂无练习记录，先从一次基线测试开始。'],
      recent: [],
    }
  } finally {
    loadingReport.value = false
  }
}
</script>
