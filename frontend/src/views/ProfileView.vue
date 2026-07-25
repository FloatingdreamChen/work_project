<template>
  <div class="workbench">
    <section class="section-grid">
      <div class="section-heading">
        <p class="eyebrow">Profile</p>
        <h2>用户画像</h2>
        <p>仅填写岗位匹配必要条件，敏感证件号不进入系统。</p>
      </div>
      <el-form class="tool-card profile-form" label-position="top">
        <div class="form-grid">
          <el-form-item label="目标考试"><el-input v-model="profile.target_exam" placeholder="2027 国考" /></el-form-item>
          <el-form-item label="目标地区"><el-input v-model="profile.target_region" placeholder="广东 / 深圳" /></el-form-item>
          <el-form-item label="学历">
            <el-select v-model="profile.education" placeholder="请选择">
              <el-option label="本科" value="本科" />
              <el-option label="硕士研究生" value="硕士研究生" />
              <el-option label="博士研究生" value="博士研究生" />
              <el-option label="大专" value="大专" />
            </el-select>
          </el-form-item>
          <el-form-item label="学位"><el-input v-model="profile.degree" placeholder="学士 / 硕士" /></el-form-item>
          <el-form-item label="专业"><el-input v-model="profile.major" placeholder="计算机科学与技术" /></el-form-item>
          <el-form-item label="应届身份">
            <el-select v-model="profile.fresh_graduate_status" placeholder="请选择">
              <el-option label="2027 应届" value="2027 应届" />
              <el-option label="择业期应届" value="择业期应届" />
              <el-option label="非应届" value="非应届" />
            </el-select>
          </el-form-item>
          <el-form-item label="政治面貌"><el-input v-model="profile.political_status" placeholder="中共党员 / 共青团员 / 群众" /></el-form-item>
          <el-form-item label="户籍"><el-input v-model="profile.household_region" placeholder="广东深圳" /></el-form-item>
          <el-form-item label="基层经历"><el-input v-model="profile.grassroots_experience" placeholder="无 / 2 年基层工作经历" /></el-form-item>
          <el-form-item label="工作年限"><el-input-number v-model="profile.work_years" :min="0" :max="60" :step="0.5" /></el-form-item>
        </div>
        <el-button type="primary" :loading="saving" @click="save">保存画像</el-button>
      </el-form>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, reactive, ref } from 'vue'
import { ElMessage } from 'element-plus'
import { getProfile, saveProfile, type Profile } from '@/api/govExam'

const saving = ref(false)
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

onMounted(async () => {
  try {
    Object.assign(profile, await getProfile())
  } catch {
    ElMessage.warning('暂未加载到画像，可先填写后保存')
  }
})

async function save() {
  saving.value = true
  try {
    Object.assign(profile, await saveProfile(profile))
    ElMessage.success('画像已保存')
  } finally {
    saving.value = false
  }
}
</script>
