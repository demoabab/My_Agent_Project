<template>
  <div class="login-wrapper">
    <el-card class="login-card">
      <h2 class="login-title">Langchain ChatChat</h2>
      <p class="login-subtitle">企业级 AI 知识库问答系统</p>
      <el-form
        ref="formRef"
        :model="form"
        :rules="rules"
        label-position="top"
        @submit.prevent="handleLogin"
      >
        <el-form-item label="用户名" prop="username">
          <el-input v-model="form.username" placeholder="请输入用户名" size="large" />
        </el-form-item>
        <el-form-item label="密码" prop="password">
          <el-input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            show-password
            size="large"
            @keyup.enter="handleLogin"
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            style="width: 100%"
            :loading="loading"
            @click="handleLogin"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
      <div class="login-footer">
        <span>还没有账号？</span>
        <router-link to="/register">立即注册</router-link>
      </div>
      <div v-if="error" class="login-error">
        <el-alert :title="error" type="error" :closable="false" />
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useTenantStore } from '@/stores/tenant'
import type { FormInstance, FormRules } from 'element-plus'

const router = useRouter()
const auth = useAuthStore()
const tenant = useTenantStore()

const formRef = ref<FormInstance>()
const loading = ref(false)
const error = ref('')

const form = reactive({
  username: '',
  password: '',
})

const rules: FormRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}

async function handleLogin() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  error.value = ''

  try {
    await auth.login(form.username, form.password)
    await auth.fetchUser()
    await tenant.fetchTenants()
    router.push('/')
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = typeof msg === 'string' ? msg : '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}
.login-card {
  width: 400px;
  padding: 8px;
}
.login-title {
  text-align: center;
  margin-bottom: 4px;
  font-size: 24px;
  color: #303133;
}
.login-subtitle {
  text-align: center;
  margin-bottom: 24px;
  color: #909399;
  font-size: 13px;
}
.login-footer {
  text-align: center;
  font-size: 13px;
  color: #909399;
}
.login-footer a {
  color: #409EFF;
  margin-left: 4px;
}
.login-error {
  margin-top: 12px;
}
</style>
