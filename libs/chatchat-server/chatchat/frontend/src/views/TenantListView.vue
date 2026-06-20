<template>
  <div class="tenant-list-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>租户管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建租户
          </el-button>
        </div>
      </template>

      <el-table :data="tenant.tenants" v-loading="loading" stripe>
        <el-table-column prop="tenant_name" label="租户名称" min-width="160">
          <template #default="{ row }">
            <router-link :to="`/tenants/${row.tenant_id}`" class="tenant-link">
              {{ row.tenant_name }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)" size="small">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/tenants/${row.tenant_id}`)">
              管理成员
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-dialog v-model="showCreateDialog" title="新建租户" width="400px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="80px">
        <el-form-item label="租户名称" prop="name">
          <el-input v-model="createForm.name" placeholder="请输入租户名称" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="creating" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useTenantStore } from '@/stores/tenant'
import { createTenant } from '@/api/tenant'
import type { FormInstance, FormRules } from 'element-plus'

const tenant = useTenantStore()
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()
const createForm = ref({ name: '' })

const createRules: FormRules = {
  name: [{ required: true, message: '请输入租户名称', trigger: 'blur' }],
}

async function fetchData() {
  loading.value = true
  await tenant.fetchTenants()
  loading.value = false
}

async function handleCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return
  creating.value = true
  try {
    await createTenant(createForm.value.name)
    ElMessage.success('租户创建成功')
    showCreateDialog.value = false
    createForm.value.name = ''
    await fetchData()
  } catch {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

function roleLabel(role: string): string {
  const map: Record<string, string> = { admin: '管理员', member: '成员', viewer: '查看者' }
  return map[role] || role
}

function roleType(role: string): 'primary' | 'success' | 'warning' | 'info' | 'danger' {
  const map: Record<string, 'primary' | 'success' | 'warning' | 'info' | 'danger'> = { admin: 'danger', member: 'primary', viewer: 'info' }
  return map[role] || 'info'
}

onMounted(fetchData)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.tenant-link {
  color: #409EFF;
  font-weight: 500;
}
</style>
