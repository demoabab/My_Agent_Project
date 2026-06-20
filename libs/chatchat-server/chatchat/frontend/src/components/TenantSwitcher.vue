<template>
  <el-select
    v-model="selectedId"
    size="small"
    style="width: 200px"
    placeholder="选择租户"
    @change="handleSwitch"
  >
    <el-option
      v-for="t in tenant.tenants"
      :key="t.tenant_id"
      :label="`${t.tenant_name} (${roleLabel(t.role)})`"
      :value="t.tenant_id"
    />
  </el-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { useTenantStore } from '@/stores/tenant'

const tenant = useTenantStore()
const selectedId = ref(tenant.currentTenantId)

watch(() => tenant.currentTenantId, (v) => {
  selectedId.value = v
})

function handleSwitch(id: string) {
  tenant.switchTenant(id)
}

function roleLabel(role: string): string {
  const map: Record<string, string> = { admin: '管理员', member: '成员', viewer: '查看者' }
  return map[role] || role
}
</script>
