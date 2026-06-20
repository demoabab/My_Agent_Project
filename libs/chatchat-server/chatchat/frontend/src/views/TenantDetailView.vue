<template>
  <div class="tenant-detail-page">
    <div class="page-header">
      <el-page-header @back="$router.push('/tenants')">
        <template #content>
          <span class="tenant-title">租户成员管理</span>
        </template>
      </el-page-header>
    </div>

    <el-card>
      <template #header>
        <div class="card-header">
          <span>成员列表</span>
          <el-button type="primary" size="small" @click="showAddDialog = true">
            <el-icon><Plus /></el-icon>
            添加成员
          </el-button>
        </div>
      </template>

      <el-table :data="members" v-loading="loading" stripe>
        <el-table-column prop="user_id" label="用户ID" width="280" show-overflow-tooltip />
        <el-table-column prop="username" label="用户名" width="160" />
        <el-table-column label="角色" width="120">
          <template #default="{ row }">
            <el-tag :type="roleType(row.role)" size="small">
              {{ roleLabel(row.role) }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button link type="danger" @click="handleRemove(row.user_id)">移除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- Add Member Dialog -->
    <el-dialog v-model="showAddDialog" title="添加成员" width="450px">
      <el-form ref="addFormRef" :model="addForm" :rules="addRules" label-width="80px">
        <el-form-item label="用户ID" prop="user_id">
          <el-input v-model="addForm.user_id" placeholder="请输入用户ID" />
        </el-form-item>
        <el-form-item label="角色" prop="role">
          <el-select v-model="addForm.role" style="width: 100%">
            <el-option label="成员 (member)" value="member" />
            <el-option label="管理员 (admin)" value="admin" />
            <el-option label="查看者 (viewer)" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" :loading="adding" @click="handleAdd">确认</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getMembers, addMember, removeMember } from '@/api/tenant'
import type { TenantMember } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const route = useRoute()
const tenantId = route.params.id as string

const members = ref<TenantMember[]>([])
const loading = ref(false)
const showAddDialog = ref(false)
const adding = ref(false)
const addFormRef = ref<FormInstance>()
const addForm = ref({ user_id: '', role: 'member' })

const addRules: FormRules = {
  user_id: [{ required: true, message: '请输入用户ID', trigger: 'blur' }],
  role: [{ required: true, message: '请选择角色', trigger: 'change' }],
}

async function fetchMembers() {
  loading.value = true
  try {
    members.value = await getMembers(tenantId)
  } catch {
    ElMessage.error('获取成员列表失败')
  } finally {
    loading.value = false
  }
}

async function handleAdd() {
  const valid = await addFormRef.value?.validate().catch(() => false)
  if (!valid) return
  adding.value = true
  try {
    await addMember(tenantId, addForm.value.user_id, addForm.value.role)
    ElMessage.success('成员添加成功')
    showAddDialog.value = false
    addForm.value = { user_id: '', role: 'member' }
    await fetchMembers()
  } catch {
    ElMessage.error('添加失败')
  } finally {
    adding.value = false
  }
}

async function handleRemove(userId: string) {
  try {
    await ElMessageBox.confirm('确认移除该成员？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await removeMember(tenantId, userId)
    ElMessage.success('成员已移除')
    await fetchMembers()
  } catch {
    ElMessage.error('移除失败')
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

onMounted(fetchMembers)
</script>

<style scoped>
.page-header {
  margin-bottom: 16px;
  padding: 12px 16px;
  background: #fff;
  border-radius: 4px;
}
.tenant-title {
  font-size: 18px;
  font-weight: bold;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
