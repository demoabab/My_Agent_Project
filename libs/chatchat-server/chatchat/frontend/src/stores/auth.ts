import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import { login as apiLogin, register as apiRegister, getMe } from '@/api/auth'
import type { UserInfo } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)
  const isAuthenticated = computed(() => !!token.value)
  const isSuperuser = computed(() => user.value?.is_superuser === true)

  watch(token, (v) => {
    if (v) {
      localStorage.setItem('token', v)
    } else {
      localStorage.removeItem('token')
    }
  })

  async function loginAction(username: string, password: string) {
    const res = await apiLogin(username, password)
    token.value = res.access_token
    user.value = {
      user_id: res.user_id,
      username: res.username,
      tenant_id: null,
      is_superuser: false,
    }
    return res
  }

  async function registerAction(
    username: string,
    password: string,
    email = '',
    full_name = ''
  ) {
    const res = await apiRegister(username, password, email, full_name)
    token.value = res.access_token
    user.value = {
      user_id: res.user_id,
      username: res.username,
      tenant_id: res.tenant_id || null,
      is_superuser: false,
    }
    return res
  }

  async function fetchUser() {
    try {
      const res = await getMe()
      user.value = {
        user_id: res.user_id,
        username: res.username,
        tenant_id: res.tenant_id,
        is_superuser: res.is_superuser,
      }
    } catch {
      token.value = ''
      user.value = null
    }
  }

  function logout() {
    token.value = ''
    user.value = null
  }

  return {
    token,
    user,
    isAuthenticated,
    isSuperuser,
    login: loginAction,
    register: registerAction,
    fetchUser,
    logout,
  }
})
