<template>
  <div class="workbench">
    <el-alert v-if="pageError" :title="pageError" type="error" show-icon @close="pageError = ''" />

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
        <el-form class="match-options" label-position="top">
          <el-form-item label="匹配策略">
            <el-segmented v-model="matchOptions.risk_preference" :options="riskPreferenceOptions" />
          </el-form-item>
          <el-form-item label="偏好地区">
            <el-input v-model="matchOptions.preferred_regions_text" placeholder="深圳、广州、珠海" />
          </el-form-item>
        </el-form>
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
          <el-table-column prop="competition_ratio" label="竞争比" width="95" />
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
          <div>
            <span>政策依据</span>
            <p>
              {{ item.policy_basis?.source_name || item.position.source_name || '岗位表' }}
              <a v-if="item.policy_basis?.source_url" :href="item.policy_basis.source_url" target="_blank" rel="noreferrer">查看来源</a>
            </p>
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
        <el-select v-model="practice.module_name" placeholder="练习模块">
          <el-option v-for="item in moduleOptions" :key="item" :label="item" :value="item" />
        </el-select>
        <div class="form-grid">
          <el-form-item label="正确率">
            <el-input-number v-model="practice.accuracy" :min="0" :max="100" />
          </el-form-item>
          <el-form-item label="耗时分钟">
            <el-input-number v-model="practice.duration_minutes" :min="0" :max="300" />
          </el-form-item>
        </div>
        <el-input v-model="practice.user_answer" type="textarea" :rows="6" placeholder="粘贴你的作答" />
        <el-button type="primary" :loading="reviewing" @click="handleReview">生成批改</el-button>
        <div v-if="review" class="review-box">
          <strong>评分：{{ review.score }}</strong>
          <p>优点：{{ review.strengths.join('；') }}</p>
          <p>问题：{{ review.problems.join('；') }}</p>
          <p>优化示例：{{ review.improved_answer }}</p>
          <p v-if="review.follow_up_question">面试追问：{{ review.follow_up_question }}</p>
        </div>
      </div>
    </section>

    <section class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Study Plan</p>
        <h2>个性化备考计划</h2>
        <p>按考试日期、学习时间、基础水平和薄弱模块倒排计划，少于三个月会自动提示风险。</p>
      </div>

      <div class="tool-card">
        <div class="form-grid">
          <el-form-item label="考试日期">
            <el-date-picker v-model="planForm.exam_date" type="date" value-format="YYYY-MM-DD" />
          </el-form-item>
          <el-form-item label="每日学习小时">
            <el-input-number v-model="planForm.daily_hours" :min="0.5" :max="12" :step="0.5" />
          </el-form-item>
          <el-form-item label="每周学习天数">
            <el-input-number v-model="planForm.weekly_days" :min="1" :max="7" />
          </el-form-item>
          <el-form-item label="当前基础">
            <el-select v-model="planForm.foundation_level">
              <el-option label="零基础" value="零基础" />
              <el-option label="一般" value="一般" />
              <el-option label="有基础" value="有基础" />
              <el-option label="较好" value="较好" />
            </el-select>
          </el-form-item>
          <el-form-item label="目标岗位">
            <el-input v-model="planForm.target_position" placeholder="税务 / 海关 / 选调等" />
          </el-form-item>
          <el-form-item label="薄弱模块">
            <el-select v-model="planForm.weak_modules" multiple collapse-tags>
              <el-option v-for="item in moduleOptions" :key="item" :label="item" :value="item" />
            </el-select>
          </el-form-item>
        </div>
        <div class="toolbar">
          <el-button type="primary" :loading="planning" @click="handleBuildPlan">生成计划</el-button>
          <el-button :loading="loadingReport" @click="handleLoadReport">阶段报告</el-button>
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
            <el-timeline-item v-for="week in studyPlan.weekly_plan.slice(0, 6)" :key="week.week" :timestamp="`第${week.week}周`">
              <strong>{{ week.phase }}｜{{ week.focus }}</strong>
              <p>{{ week.tasks.slice(0, 2).join('；') }}</p>
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

    <section id="knowledge" class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Knowledge</p>
        <h2>知识库与 RAG</h2>
        <p>查看本地模型、向量检索状态，并检索已导入的政策和岗位知识。</p>
      </div>

      <div class="tool-card">
        <div class="toolbar">
          <el-button :icon="Search" :loading="loadingKnowledge" @click="handleKnowledgeStatus">刷新状态</el-button>
          <el-tag :type="knowledgeStatus?.vector_rag_ready ? 'success' : 'warning'">
            {{ knowledgeStatus?.vector_rag_ready ? '向量 RAG 就绪' : '关键词兜底' }}
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
          <el-input v-model="knowledgeQuery" placeholder="例如：应届生身份如何认定" />
          <el-button type="primary" :loading="searchingKnowledge" @click="handleKnowledgeSearch">检索</el-button>
        </div>
        <el-table :data="knowledgeResults" height="220" empty-text="暂无知识库结果">
          <el-table-column prop="source_name" label="来源" width="150" />
          <el-table-column prop="content" label="片段" min-width="320" show-overflow-tooltip />
          <el-table-column prop="score" label="分数" width="90" />
        </el-table>
      </div>
    </section>

    <section id="history" class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">History</p>
        <h2>练习历史</h2>
        <p>汇总近阶段练习情况，并查看仍待复盘的错题。</p>
      </div>

      <div class="tool-card">
        <div class="toolbar">
          <el-button :loading="loadingReport" @click="handleLoadReport">刷新阶段报告</el-button>
          <el-button :loading="loadingWrongQuestions" @click="handleLoadWrongQuestions">刷新错题</el-button>
        </div>
        <div v-if="studyReport" class="review-box">
          <strong>近{{ studyReport.days }}天练习：{{ studyReport.practice_count }}次</strong>
          <p>均分：{{ studyReport.average_score || '暂无' }}</p>
          <p>高频问题：{{ studyReport.top_problem_keywords.map((item) => item.keyword).join('；') || '暂无' }}</p>
          <p>建议：{{ studyReport.suggestions.join('；') }}</p>
        </div>
        <el-table :data="wrongQuestions" height="220" empty-text="暂无错题">
          <el-table-column prop="module_name" label="模块" width="150" />
          <el-table-column prop="question" label="题目" min-width="260" show-overflow-tooltip />
          <el-table-column prop="reason" label="问题" min-width="220" show-overflow-tooltip />
          <el-table-column prop="status" label="状态" width="100" />
        </el-table>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { Aim, Search, Upload } from '@element-plus/icons-vue'

import {
  chat,
  buildStudyPlan,
  getProfile,
  getKnowledgeStatus,
  getStudyReport,
  importPositions,
  listWrongQuestions,
  listPositions,
  matchPositions,
  reviewPractice,
  searchKnowledge,
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
const pageError = ref('')
const matchOptions = reactive({
  risk_preference: 'balanced',
  preferred_regions_text: '深圳、广州',
})
const riskPreferenceOptions = [
  { label: '稳健', value: 'conservative' },
  { label: '均衡', value: 'balanced' },
  { label: '冲刺', value: 'aggressive' },
]
const savingProfile = ref(false)
const matching = ref(false)
const chatting = ref(false)
const reviewing = ref(false)
const chatMessage = ref('我计算机专业，2027 应届，可以报哪些国考岗位？')
const chatAnswer = ref('')
const chatAgent = ref('')
const practice = reactive({
  practice_type: '申论',
  module_name: '申论-小题',
  topic: '基层治理',
  user_answer: '',
  accuracy: undefined as number | undefined,
  duration_minutes: undefined as number | undefined,
})
const review = ref<Awaited<ReturnType<typeof reviewPractice>> | null>(null)
const planning = ref(false)
const loadingReport = ref(false)
const studyPlan = ref<Awaited<ReturnType<typeof buildStudyPlan>>['plan'] | null>(null)
const studyReport = ref<Awaited<ReturnType<typeof getStudyReport>> | null>(null)
const loadingKnowledge = ref(false)
const searchingKnowledge = ref(false)
const loadingWrongQuestions = ref(false)
const knowledgeStatus = ref<Awaited<ReturnType<typeof getKnowledgeStatus>> | null>(null)
const knowledgeQuery = ref('应届生身份认定')
const knowledgeResults = ref<Awaited<ReturnType<typeof searchKnowledge>>>([])
const wrongQuestions = ref<Array<Record<string, unknown>>>([])
const modelEntries = computed(() => Object.entries(knowledgeStatus.value?.models || {}))
const moduleOptions = ['行测-常识', '行测-言语理解', '行测-数量关系', '行测-判断推理', '行测-资料分析', '申论-材料阅读', '申论-小题', '申论-大作文', '面试-表达与素材']
const planForm = reactive({
  exam_date: '2027-11-28',
  daily_hours: 2,
  weekly_days: 6,
  foundation_level: '一般',
  target_position: '税务系统',
  weak_modules: ['行测-数量关系', '申论-大作文'],
})

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
    applicant_count: 46,
    competition_ratio: 23,
    previous_min_score: 128.5,
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
    applicant_count: 188,
    competition_ratio: 188,
    previous_min_score: 138.2,
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
    await handleKnowledgeStatus()
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
  try {
    const result = await importPositions(samplePositions)
    positions.value = result.items
    ElMessage.success(`已导入 ${result.count} 个样例岗位`)
  } catch (error) {
    showError(error, '岗位导入失败')
  }
}

async function handleLoadPositions() {
  try {
    positions.value = await listPositions({ exam_year: 2027, exam_type: '国考', limit: 50 })
  } catch (error) {
    showError(error, '岗位加载失败')
  }
}

async function handleMatch() {
  matching.value = true
  try {
    const result = await matchPositions({
      profile,
      exam_year: 2027,
      exam_type: '国考',
      preferred_regions: splitRegions(matchOptions.preferred_regions_text),
      risk_preference: matchOptions.risk_preference,
      limit: 20,
    })
    matches.value = result.items
    matchDisclaimer.value = result.disclaimer
  } finally {
    matching.value = false
  }
}

function splitRegions(value: string) {
  return value
    .split(/[,，、\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
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

async function handleBuildPlan() {
  planning.value = true
  try {
    const result = await buildStudyPlan({
      target_exam: profile.target_exam || '公务员考试',
      exam_date: planForm.exam_date,
      target_position: planForm.target_position,
      province: profile.target_region,
      daily_hours: planForm.daily_hours,
      weekly_days: planForm.weekly_days,
      foundation_level: planForm.foundation_level,
      weak_modules: planForm.weak_modules,
      include_interview: true,
      notes: `${profile.major || ''} ${profile.fresh_graduate_status || ''}`,
    })
    studyPlan.value = result.plan
  } finally {
    planning.value = false
  }
}

async function handleLoadReport() {
  loadingReport.value = true
  try {
    studyReport.value = await getStudyReport(30)
  } catch (error) {
    showError(error, '阶段报告加载失败')
  } finally {
    loadingReport.value = false
  }
}

async function handleKnowledgeStatus() {
  loadingKnowledge.value = true
  try {
    knowledgeStatus.value = await getKnowledgeStatus()
  } catch (error) {
    showError(error, '知识库状态加载失败')
  } finally {
    loadingKnowledge.value = false
  }
}

async function handleKnowledgeSearch() {
  searchingKnowledge.value = true
  try {
    knowledgeResults.value = await searchKnowledge({ query: knowledgeQuery.value, top_k: 5 })
  } catch (error) {
    showError(error, '知识库检索失败')
  } finally {
    searchingKnowledge.value = false
  }
}

async function handleLoadWrongQuestions() {
  loadingWrongQuestions.value = true
  try {
    wrongQuestions.value = await listWrongQuestions({ status: 'open', limit: 20 })
  } catch (error) {
    showError(error, '错题加载失败')
  } finally {
    loadingWrongQuestions.value = false
  }
}

function showError(error: unknown, fallback: string) {
  pageError.value = error instanceof Error ? error.message : fallback
  ElMessage.error(fallback)
}

function tierType(tier: string) {
  if (tier === '冲') return 'danger'
  if (tier === '稳') return 'success'
  if (tier === '保') return 'warning'
  return 'info'
}
</script>
