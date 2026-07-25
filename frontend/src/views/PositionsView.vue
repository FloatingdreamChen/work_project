<template>
  <div class="workbench">
    <el-alert v-if="error" :title="error" type="error" show-icon @close="error = ''" />
    <section class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Positions</p>
        <h2>岗位匹配</h2>
        <p>导入样例岗位，基于画像生成“冲、稳、保”和资格风险。</p>
      </div>
      <div class="tool-card">
        <el-form class="match-options" label-position="top">
          <el-form-item label="匹配策略">
            <el-segmented v-model="riskPreference" :options="riskPreferenceOptions" />
          </el-form-item>
          <el-form-item label="偏好地区">
            <el-input v-model="preferredRegionsText" placeholder="深圳、广州、珠海" />
          </el-form-item>
        </el-form>
        <div class="toolbar">
          <el-button :icon="Upload" :loading="seeding" @click="seedPositions">导入样例岗位</el-button>
          <el-button :icon="Search" :loading="loading" @click="loadPositions">刷新岗位</el-button>
          <el-button type="primary" :icon="Aim" :loading="matching" @click="match">开始匹配</el-button>
        </div>
        <el-table :data="positions" height="320" empty-text="暂无岗位数据">
          <el-table-column prop="position_name" label="岗位" min-width="150" />
          <el-table-column prop="department" label="部门" min-width="160" />
          <el-table-column prop="province" label="地区" width="100" />
          <el-table-column prop="major_requirement" label="专业要求" min-width="180" />
          <el-table-column prop="competition_ratio" label="竞争比" width="95" />
        </el-table>
      </div>
    </section>
    <section v-if="matches.length" class="match-list">
      <article v-for="item in matches" :key="item.position.position_code || item.position.position_name" class="match-card">
        <div class="match-title">
          <el-tag :type="tierType(item.tier)" effect="dark">{{ item.tier }}</el-tag>
          <h3>{{ item.position.position_name }}</h3>
          <strong>{{ item.score }}分</strong>
        </div>
        <p>{{ item.rationale }}</p>
        <div class="evidence-grid">
          <div><span>已匹配</span><p>{{ item.matched.join('；') || '暂无' }}</p></div>
          <div><span>资格风险</span><p>{{ item.risks.join('；') || '暂无明确风险' }}</p></div>
          <div><span>人工核验</span><p>{{ item.verification.join('；') || '暂无' }}</p></div>
          <div><span>政策依据</span><p>{{ item.policy_basis?.source_name || item.position.source_name || '岗位表' }}</p></div>
        </div>
      </article>
      <p class="disclaimer">{{ disclaimer }}</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Aim, Search, Upload } from '@element-plus/icons-vue'
import { importPositions, listPositions, matchPositions, type MatchItem, type Position } from '@/api/govExam'
import { samplePositions, splitRegions } from '@/composables/sampleData'

const positions = ref<Position[]>([])
const matches = ref<MatchItem[]>([])
const disclaimer = ref('')
const error = ref('')
const loading = ref(false)
const seeding = ref(false)
const matching = ref(false)
const preferredRegionsText = ref('深圳、广州')
const riskPreference = ref('balanced')
const riskPreferenceOptions = [
  { label: '稳健', value: 'conservative' },
  { label: '均衡', value: 'balanced' },
  { label: '冲刺', value: 'aggressive' },
]

onMounted(loadPositions)

async function seedPositions() {
  seeding.value = true
  try {
    const result = await importPositions(samplePositions)
    positions.value = result.items
    ElMessage.success(`已导入 ${result.count} 个样例岗位`)
  } catch (err) {
    showError(err, '岗位导入失败')
  } finally {
    seeding.value = false
  }
}

async function loadPositions() {
  loading.value = true
  try {
    positions.value = await listPositions({ exam_year: 2027, exam_type: '国考', limit: 50 })
  } catch (err) {
    showError(err, '岗位加载失败')
  } finally {
    loading.value = false
  }
}

async function match() {
  matching.value = true
  try {
    const result = await matchPositions({
      exam_year: 2027,
      exam_type: '国考',
      preferred_regions: splitRegions(preferredRegionsText.value),
      risk_preference: riskPreference.value,
      limit: 20,
    })
    matches.value = result.items
    disclaimer.value = result.disclaimer
  } catch (err) {
    showError(err, '岗位匹配失败')
  } finally {
    matching.value = false
  }
}

function showError(err: unknown, fallback: string) {
  error.value = err instanceof Error ? err.message : fallback
  ElMessage.error(fallback)
}

function tierType(tier: string) {
  if (tier === '冲') return 'danger'
  if (tier === '稳') return 'success'
  if (tier === '保') return 'warning'
  return 'info'
}
</script>
