import type { Position } from '@/api/govExam'

export const moduleOptions = ['行测-常识', '行测-言语理解', '行测-数量关系', '行测-判断推理', '行测-资料分析', '申论-材料阅读', '申论-小题', '申论-大作文', '面试-表达与素材']

export const samplePositions: Position[] = [
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

export function createConversationId() {
  const randomUUID = globalThis.crypto?.randomUUID
  if (typeof randomUUID === 'function') {
    return `web-${randomUUID.call(globalThis.crypto)}`
  }
  return `web-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 10)}`
}

export function splitRegions(value: string) {
  return value
    .split(/[,，、\s]+/)
    .map((item) => item.trim())
    .filter(Boolean)
}
