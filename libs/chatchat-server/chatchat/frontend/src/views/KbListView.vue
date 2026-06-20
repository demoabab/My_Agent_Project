<template>
  <div class="kb-list-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>知识库管理</span>
          <el-button type="primary" @click="showCreateDialog = true">
            <el-icon><Plus /></el-icon>
            新建知识库
          </el-button>
        </div>
      </template>

      <el-table :data="kbList" v-loading="loading" stripe>
        <el-table-column prop="kb_name" label="知识库名称" min-width="180">
          <template #default="{ row }">
            <router-link :to="`/kb/${row.kb_name}`" class="kb-link">
              {{ row.kb_name }}
            </router-link>
          </template>
        </el-table-column>
        <el-table-column prop="vs_type" label="向量库类型" width="120" />
        <el-table-column prop="embed_model" label="嵌入模型" min-width="160" />
        <el-table-column prop="file_count" label="文件数" width="100" align="center" />
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button link type="primary" @click="$router.push(`/kb/${row.kb_name}`)">管理</el-button>
            <el-button link type="danger" @click="handleDelete(row.kb_name)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-empty v-if="!loading && kbList.length === 0" description="暂无知识库，请新建" />
    </el-card>

    <!-- Create Dialog -->
    <el-dialog v-model="showCreateDialog" title="新建知识库" width="450px">
      <el-form ref="createFormRef" :model="createForm" :rules="createRules" label-width="100px">
        <el-form-item label="知识库名称" prop="knowledge_base_name">
          <el-input v-model="createForm.knowledge_base_name" placeholder="请输入名称" />
        </el-form-item>
        <el-form-item label="向量库类型" prop="vector_store_type">
          <el-select v-model="createForm.vector_store_type" style="width: 100%">
            <el-option label="FAISS" value="faiss" />
            <el-option label="Chroma" value="chroma" />
          </el-select>
        </el-form-item>
        <el-form-item label="嵌入模型">
          <el-input v-model="createForm.embed_model" placeholder="默认模型" />
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
import { ElMessage, ElMessageBox } from 'element-plus'
import { listKbs, createKb, deleteKb } from '@/api/kb'
import type { KnowledgeBase } from '@/types'
import type { FormInstance, FormRules } from 'element-plus'

const kbList = ref<KnowledgeBase[]>([])
const loading = ref(false)
const showCreateDialog = ref(false)
const creating = ref(false)
const createFormRef = ref<FormInstance>()

const createForm = ref({
  knowledge_base_name: '',
  vector_store_type: 'faiss',
  embed_model: '',
})

const createRules: FormRules = {
  knowledge_base_name: [{ required: true, message: '请输入知识库名称', trigger: 'blur' }],
  vector_store_type: [{ required: true, message: '请选择向量库类型', trigger: 'change' }],
}

async function fetchList() {
  loading.value = true
  try {
    const res = await listKbs()
    kbList.value = res.data || []
  } catch {
    ElMessage.error('获取知识库列表失败')
  } finally {
    loading.value = false
  }
}

async function handleCreate() {
  const valid = await createFormRef.value?.validate().catch(() => false)
  if (!valid) return

  creating.value = true
  try {
    await createKb(createForm.value)
    ElMessage.success('知识库创建成功')
    showCreateDialog.value = false
    createForm.value = { knowledge_base_name: '', vector_store_type: 'faiss', embed_model: '' }
    await fetchList()
  } catch {
    ElMessage.error('创建失败')
  } finally {
    creating.value = false
  }
}

async function handleDelete(name: string) {
  try {
    await ElMessageBox.confirm(`确认删除知识库 "${name}"？此操作不可恢复。`, '警告', {
      confirmButtonText: '确认删除',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteKb(name)
    ElMessage.success('删除成功')
    await fetchList()
  } catch {
    ElMessage.error('删除失败')
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
.kb-link {
  color: #409EFF;
  font-weight: 500;
}
</style>
