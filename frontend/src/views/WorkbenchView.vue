<template>
  <div class="workbench">
    <section id="profile" class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Profile</p>
        <h2>用户画像</h2>
        <p>仅填写岗位匹配必要条件，敏感证件号不进入系统。</p>
      </div>

      <el-form class="tool-card profile-form" label-position="top">
        <div class="form-grid">
          <el-form-item label="目标考试">
            <el-input v-model="profile.target_exam" placeholder="2027 国考" />
          </el-form-item>
          <el-form-item label="目标地区">
            <el-input v-model="profile.target_region" placeholder="广东 / 深圳" />
          </el-form-item>
          <el-form-item label="学历">
            <el-select v-model="profile.education" placeholder="请选择">
              <el-option label="本科" value="本科" />
              <el-option label="硕士研究生" value="硕士研究生" />
              <el-option label="博士研究生" value="博士研究生" />
              <el-option label="大专" value="大专" />
            </el-select>
          </el-form-item>
          <el-form-item label="学位">
            <el-input v-model="profile.degree" placeholder="学士 / 硕士" />
          </el-form-item>
          <el-form-item label="专业">
            <el-input v-model="profile.major" placeholder="计算机科学与技术" />
          </el-form-item>
          <el-form-item label="应届身份">
            <el-select v-model="profile.fresh_graduate_status" placeholder="请选择">
              <el-option label="2027 应届" value="2027 应届" />
              <el-option label="择业期应届" value="择业期应届" />
              <el-option label="非应届" value="非应届" />
            </el-select>
          </el-form-item>
          <el-form-item label="政治面貌">
            <el-input v-model="profile.political_status" placeholder="中共党员 / 共青团员 / 群众" />
          </el-form-item>
          <el-form-item label="户籍">
            <el-input v-model="profile.household_region" placeholder="广东深圳" />
          </el-form-item>
          <el-form-item label="基层经历">
            <el-input v-model="profile.grassroots_experience" placeholder="无 / 2 年基层工作经历" />
          </el-form-item>
          <el-form-item label="工作年限">
            <el-input-number v-model="profile.work_years" :min="0" :max="60" :step="0.5" />
          </el-form-item>
        </div>
        <el-button type="primary" :loading="savingProfile" @click="handleSaveProfile">保存画像</el-button>
      </el-form>
    </section>

    <section id="positions" class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Positions</p>
        <h2>岗位匹配</h2>
        <p>可先导入样例岗位，再基于画像生成“冲、稳、保”和资格风险。</p>
      </div>

      <div class="tool-card">
        <div class="toolbar">
          <el-button :icon="Upload" @click="handleSeedPositions">导入样例岗位</el-button>
          <el-button :icon="Search" @click="handleLoadPositions">刷新岗位</el-button>
          <el-button type="primary" :icon="Aim" :loading="matching" @click="handleMatch">开始匹配</el-button>
        </div>

        <el-table :data="positions" height="260" empty-text="暂无岗位数据">
          <el-table-column prop="position_name" label="岗位" min-width="150" />
          <el-table-column prop="department" label="部门" min-width="160" />
          <el-table-column prop="province" label="地区" width="100" />
          <el-table-column prop="major_requirement" label="专业要求" min-width="180" />
        </el-table>
      </div>
    </section>

    <section v-if="matches.length" class="match-list" aria-label="匹配结果">
      <article v-for="item in matches" :key="item.position.position_code || item.position.position_name" class="match-card">
        <div>
          <div class="match-title">
            <el-tag :type="tierType(item.tier)" effect="dark">{{ item.tier }}</el-tag>
            <h3>{{ item.position.position_name }}</h3>
            <strong>{{ item.score }}分</strong>
          </div>
          <p>{{ item.rationale }}</p>
        </div>
        <div class="evidence-grid">
          <div>
            <span>已匹配</span>
            <p>{{ item.matched.join('；') || '暂无' }}</p>
          </div>
          <div>
            <span>资格风险</span>
            <p>{{ item.risks.join('；') || '暂无明确风险' }}</p>
          </div>
          <div>
            <span>人工核验</span>
            <p>{{ item.verification.join('；') || '暂无' }}</p>
          </div>
        </div>
      </article>
      <p class="disclaimer">{{ matchDisclaimer }}</p>
    </section>

    <section id="practice" class="dual-grid">
      <div class="tool-card">
        <div class="card-head">
          <h2>AI 问答</h2>
          <el-tag effect="plain">{{ chatAgent || '自动路由' }}</el-tag>
        </div>
        <el-input
          v-model="chatMessage"
          type="textarea"
          :rows="4"
          placeholder="例如：我计算机专业，2027 应届，可以报哪些国考岗位？"
        />
        <el-button type="primary" :loading="chatting" @click="handleChat">发送</el-button>
        <p v-if="chatAnswer" class="answer-box">{{ chatAnswer }}</p>
      </div>

      <div class="tool-card">
        <div class="card-head">
          <h2>练习批改</h2>
          <el-segmented v-model="practice.practice_type" :options="['行测', '申论', '面试']" />
        </div>
        <el-input v-model="practice.topic" placeholder="题目主题" />
        <el-input v-model="practice.user_answer" type="textarea" :rows="6" placeholder="粘贴你的作答" />
        <el-button type="primary" :loading="reviewing" @click="handleReview">生成批改</el-button>
        <div v-if="review" class="review-box">
          <strong>评分：{{ review.score }}</strong>
          <p>优点：{{ review.strengths.join('；') }}</p>
          <p>问题：{{ review.problems.join('；') }}</p>
          <p>优化示例：{{ review.improved_answer }}</p>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Aim, Search, Upload } from '@element-plus/icons-vue'

import {
  chat,
  getProfile,
  importPositions,
  listPositions,
  matchPositions,
  reviewPractice,
  saveProfile,
  type MatchItem,
  type Position,
  type Profile,
} from '@/api/govExam'

const profile = reactive<Profile>({
  target_exam: '2027 国考',
  target_region: '广东',
  education: '本科',
  degree: '学士',
  major: '计算机科学与技术',
  fresh_graduate_status: '2027 应届',
  political_status: '共青团员',
  household_region: '广东',
  grassroots_experience: '无',
  work_years: 0,
})

const positions = ref<Position[]>([])
const matches = ref<MatchItem[]>([])
const matchDisclaimer = ref('')
const savingProfile = ref(false)
const matching = ref(false)
const chatting = ref(false)
const reviewing = ref(false)
const chatMessage = ref('我计算机专业，2027 应届，可以报哪些国考岗位？')
const chatAnswer = ref('')
const chatAgent = ref('')
const practice = reactive({
  practice_type: '申论',
  topic: '基层治理',
  user_answer: '',
})
const review = ref<Awaited<ReturnType<typeof reviewPractice>> | null>(null)

const samplePositions: Position[] = [
  {
    exam_year: 2027,
    exam_type: '国考',
    province: '广东',
    city: '深圳',
    department: '国家税务总局深圳市税务局',
    position_name: '一级行政执法员',
    position_code: '300110001001',
    recruitment_count: 2,
    education_requirement: '本科及以上',
    degree_requirement: '学士及以上',
    major_requirement: '计算机科学与技术、软件工程、网络工程',
    political_requirement: '不限',
    grassroots_requirement: '不限',
    work_years_requirement: '不限',
    household_requirement: '不限',
    source_name: '样例岗位表',
  },
  {
    exam_year: 2027,
    exam_type: '国考',
    province: '广东',
    city: '广州',
    department: '广州海关',
    position_name: '监管岗位',
    position_code: '300129002001',
    recruitment_count: 1,
    education_requirement: '硕士研究生及以上',
    degree_requirement: '硕士',
    major_requirement: '法学、经济学',
    political_requirement: '中共党员',
    grassroots_requirement: '2年基层工作经历',
    work_years_requirement: '2年以上',
    household_requirement: '不限',
    source_name: '样例岗位表',
  },
]

onMounted(async () => {
  try {
    const saved = await getProfile()
    Object.assign(profile, saved)
    await handleLoadPositions()
  } catch {
    ElMessage.warning('暂未连接后端或尚未初始化画像')
  }
})

async function handleSaveProfile() {
  savingProfile.value = true
  try {
    const saved = await saveProfile(profile)
    Object.assign(profile, saved)
    ElMessage.success('画像已保存')
  } finally {
    savingProfile.value = false
  }
}

async function handleSeedPositions() {
  const result = await importPositions(samplePositions)
  positions.value = result.items
  ElMessage.success(`已导入 ${result.count} 个样例岗位`)
}

async function handleLoadPositions() {
  positions.value = await listPositions({ exam_year: 2027, exam_type: '国考', limit: 50 })
}

async function handleMatch() {
  matching.value = true
  try {
    const result = await matchPositions({
      profile,
      exam_year: 2027,
      exam_type: '国考',
      limit: 20,
    })
    matches.value = result.items
    matchDisclaimer.value = result.disclaimer
  } finally {
    matching.value = false
  }
}

async function handleChat() {
  chatting.value = true
  try {
    const result = await chat(chatMessage.value)
    chatAnswer.value = result.answer
    chatAgent.value = result.agent
  } finally {
    chatting.value = false
  }
}

async function handleReview() {
  reviewing.value = true
  try {
    review.value = await reviewPractice(practice)
  } finally {
    reviewing.value = false
  }
}

function tierType(tier: string) {
  if (tier === '冲') return 'danger'
  if (tier === '稳') return 'success'
  if (tier === '保') return 'warning'
  return 'info'
}
</script>
