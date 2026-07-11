import { defineStore } from 'pinia'
import { ref, watch } from 'vue'
import { listTenants } from '@/api/tenant'
import { switchTenant as switchTenantApi } from '@/api/auth'
import { useAuthStore } from '@/stores/auth'
import type { UserTenant } from '@/types'

export const useTenantStore = defineStore('tenant', () => {
  const tenants = ref<UserTenant[]>([])
  const currentTenantId = ref(localStorage.getItem('tenantId') || '')
  const currentRole = ref('')

  watch(currentTenantId, (v) => {
    if (v) {
      localStorage.setItem('tenantId', v)
    } else {
      localStorage.removeItem('tenantId')
    }
    const t = tenants.value.find((x) => x.tenant_id === v)
    currentRole.value = t?.role || ''
  })

  async function fetchTenants() {
    try {
      const data = await listTenants()
      tenants.value = Array.isArray(data) ? data : []
      if (!currentTenantId.value && tenants.value.length > 0) {
        currentTenantId.value = tenants.value[0].tenant_id
      }
    } catch {
      tenants.value = []
    }
  }

  async function switchTenant(tenantId: string) {
    const auth = useAuthStore()
    try {
      const res = await switchTenantApi(tenantId)
      auth.token = res.access_token
    } catch {
      // API call failed — fall back to local-only switch
    }
    currentTenantId.value = tenantId
  }

  function isTenantAdmin(): boolean {
    return currentRole.value === 'admin'
  }

  return {
    tenants,
    currentTenantId,
    currentRole,
    fetchTenants,
    switchTenant,
    isTenantAdmin,
  }
})
