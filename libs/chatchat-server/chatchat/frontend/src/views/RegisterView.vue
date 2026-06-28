<template>
  <div class="register-wrapper">
    <div class="register-card-container">
      <div class="register-brand">
        <div class="brand-icon">CC</div>
        <h1 class="brand-name">ChatChat</h1>
      </div>
      <el-card shadow="never" class="register-card">
        <h2 class="register-title">注册账号</h2>
        <el-form
          ref="formRef"
          :model="form"
          :rules="rules"
          label-position="top"
          @submit.prevent="handleRegister"
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
            />
          </el-form-item>
          <el-form-item label="确认密码" prop="confirmPassword">
            <el-input
              v-model="form.confirmPassword"
              type="password"
              placeholder="请再次输入密码"
              show-password
              size="large"
            />
          </el-form-item>
          <el-form-item label="邮箱" prop="email">
            <el-input v-model="form.email" placeholder="请输入邮箱（选填）" size="large" />
          </el-form-item>
          <el-form-item label="姓名" prop="fullName">
            <el-input v-model="form.fullName" placeholder="请输入姓名（选填）" size="large" />
          </el-form-item>
          <el-form-item>
            <el-button
              type="primary"
              size="large"
              style="width: 100%"
              :loading="loading"
              @click="handleRegister"
            >
              注册
            </el-button>
          </el-form-item>
        </el-form>
        <div class="register-footer">
          <span>已有账号？</span>
          <router-link to="/login">立即登录</router-link>
        </div>
        <div v-if="error" class="register-error">
          <el-alert :title="error" type="error" :closable="false" />
        </div>
      </el-card>
    </div>
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
  confirmPassword: '',
  email: '',
  fullName: '',
})

const validateConfirmPassword = (_rule: unknown, value: string, callback: (err?: Error) => void) => {
  if (value !== form.password) {
    callback(new Error('两次输入的密码不一致'))
  } else {
    callback()
  }
}

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 个字符', trigger: 'blur' },
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    { validator: validateConfirmPassword, trigger: 'blur' },
  ],
}

async function handleRegister() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  loading.value = true
  error.value = ''

  try {
    await auth.register(form.username, form.password, form.email, form.fullName)
    await auth.fetchUser()
    await tenant.fetchTenants()
    router.push('/')
  } catch (err: unknown) {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail
    error.value = typeof msg === 'string' ? msg : '注册失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-wrapper {
  display: flex; justify-content: center; align-items: center;
  min-height: 100vh;
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 40%, #0f3460 100%);
}
.register-card-container {
  width: 420px; text-align: center;
}
.register-brand { margin-bottom: 24px; }
.brand-icon {
  width: 48px; height: 48px; border-radius: 12px;
  background: linear-gradient(135deg, #409EFF, #6366f1);
  color: #fff; font-size: 18px; font-weight: 700;
  display: inline-flex; align-items: center; justify-content: center;
  margin-bottom: 10px;
}
.brand-name { margin: 0; font-size: 22px; color: #fff; letter-spacing: 1px; }

.register-card {
  border-radius: 10px; border: none;
  box-shadow: 0 4px 24px rgba(0,0,0,0.25);
}
.register-title {
  text-align: center; margin: 0 0 20px; font-size: 20px; color: #303133;
}
.register-footer {
  text-align: center; font-size: 13px; color: #909399;
}
.register-footer a { color: #409EFF; margin-left: 4px; }
.register-error { margin-top: 12px; }
</style>
