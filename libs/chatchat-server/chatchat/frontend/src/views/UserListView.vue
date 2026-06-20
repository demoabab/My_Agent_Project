<template>
  <div class="user-list-page">
    <el-card>
      <template #header>
        <span>用户管理</span>
      </template>

      <el-table :data="users" v-loading="loading" stripe>
        <el-table-column prop="username" label="用户名" width="160" />
        <el-table-column prop="email" label="邮箱" min-width="200" show-overflow-tooltip />
        <el-table-column prop="full_name" label="姓名" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.is_active ? 'success' : 'danger'" size="small">
              {{ row.is_active ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="超级管理员" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.is_superuser" type="warning" size="small">是</el-tag>
            <span v-else style="color: #909399">否</span>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="180" />
        <el-table-column label="操作" width="120">
          <template #default="{ row }">
            <el-button
              v-if="!row.is_superuser"
              link
              :type="row.is_active ? 'danger' : 'success'"
              @click="toggleStatus(row as unknown as UserRecord)"
            >
              {{ row.is_active ? '禁用' : '启用' }}
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import client from '@/api/client'

interface UserRecord {
  id: string
  username: string
  email: string
  full_name: string
  is_active: boolean
  is_superuser: boolean
  create_time: string
}

const users = ref<UserRecord[]>([])
const loading = ref(false)

async function fetchUsers() {
  loading.value = true
  try {
    const res = await client.get('/api/v1/auth/users')
    users.value = res.data.users || []
  } catch {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function toggleStatus(user: UserRecord) {
  try {
    await client.put(`/api/v1/auth/users/${user.id}/status`, null, {
      params: { is_active: !user.is_active },
    })
    ElMessage.success(`用户已${user.is_active ? '禁用' : '启用'}`)
    await fetchUsers()
  } catch {
    ElMessage.error('操作失败')
  }
}

onMounted(fetchUsers)
</script>
