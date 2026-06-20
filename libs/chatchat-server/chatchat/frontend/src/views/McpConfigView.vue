<template>
  <div class="mcp-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>MCP 连接管理</span>
          <el-button type="primary" size="small" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建连接
          </el-button>
        </div>
      </template>

      <el-table :data="connections" v-loading="loading" stripe>
        <el-table-column prop="server_name" label="服务器名称" min-width="160" />
        <el-table-column prop="transport" label="传输方式" width="100" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.enabled ? 'success' : 'info'" size="small">
              {{ row.enabled ? '启用' : '禁用' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200" show-overflow-tooltip />
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button link type="primary" @click="handleTest(row.id)">测试</el-button>
            <el-button link @click="handleEdit(row as unknown as McpConnection)">编辑</el-button>
            <el-button link type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && connections.length === 0" description="暂无 MCP 连接" />
    </el-card>

    <!-- Create/Edit Dialog -->
    <el-dialog
      v-model="showCreateDialog"
      :title="editing ? '编辑连接' : '新建连接'"
      width="500px"
    >
      <el-form ref="formRef" :model="form" :rules="rules" label-width="90px">
        <el-form-item label="服务器名称" prop="server_name">
          <el-input v-model="form.server_name" placeholder="例如: filesystem" />
        </el-form-item>
        <el-form-item label="传输方式" prop="transport">
          <el-select v-model="form.transport" style="width: 100%">
            <el-option label="stdio" value="stdio" />
            <el-option label="SSE" value="sse" />
          </el-select>
        </el-form-item>
        <el-form-item label="命令参数" prop="args">
          <el-input v-model="argsText" placeholder="每行一个参数" type="textarea" :rows="3" />
        </el-form-item>
        <el-form-item label="超时(秒)" prop="timeout">
          <el-input-number v-model="form.timeout" :min="1" :max="300" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" placeholder="可选描述" />
        </el-form-item>
        <el-form-item label="启用">
          <el-switch v-model="form.enabled" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import {
  listMcpConnections,
  createMcpConnection,
  updateMcpConnection,
  deleteMcpConnection,
  testMcpConnection,
} from '@/api/mcp'
import type { McpConnection } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const connections = ref<McpConnection[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const saving = ref(false)
const editing = ref<McpConnection | null>(null)
const formRef = ref<FormInstance>()

const form = ref({
  server_name: '',
  transport: 'stdio',
  args: [] as string[],
  timeout: 30,
  description: '',
  enabled: true,
  config: {} as Record<string, unknown>,
})

const argsText = ref('')

const rules: FormRules = {
  server_name: [{ required: true, message: '请输入服务器名称', trigger: 'blur' }],
  transport: [{ required: true, message: '请选择传输方式', trigger: 'change' }],
}

const argsTextComputed = computed({
  get: () => form.value.args.join('\n'),
  set: (v: string) => { form.value.args = v.split('\n').filter(Boolean) },
})

async function fetchList() {
  loading.value = true
  try {
    const res = await listMcpConnections()
    connections.value = res.connections || []
  } catch {
    ElMessage.error('获取 MCP 连接列表失败')
  } finally {
    loading.value = false
  }
}

function handleEdit(conn: McpConnection) {
  editing.value = conn
  form.value = {
    server_name: conn.server_name,
    transport: conn.transport,
    args: [],
    timeout: 30,
    description: conn.description || '',
    enabled: conn.enabled,
    config: {},
  }
  showCreateDialog.value = true
}

async function handleSave() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  saving.value = true
  try {
    if (editing.value) {
      await updateMcpConnection(editing.value.id, form.value)
      ElMessage.success('更新成功')
    } else {
      await createMcpConnection(form.value)
      ElMessage.success('创建成功')
    }
    showCreateDialog.value = false
    editing.value = null
    resetForm()
    await fetchList()
  } catch {
    ElMessage.error('保存失败')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: string) {
  try {
    await ElMessageBox.confirm('确认删除此连接？', '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteMcpConnection(id)
    ElMessage.success('删除成功')
    await fetchList()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleTest(id: string) {
  try {
    const res = await testMcpConnection(id)
    if (res.success) {
      ElMessage.success('连接测试成功')
    } else {
      ElMessage.warning(res.message || '连接测试失败')
    }
  } catch {
    ElMessage.error('连接测试失败')
  }
}

function resetForm() {
  form.value = {
    server_name: '',
    transport: 'stdio',
    args: [],
    timeout: 30,
    description: '',
    enabled: true,
    config: {},
  }
}

onMounted(fetchList)
</script>

<style scoped>
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
</style>
