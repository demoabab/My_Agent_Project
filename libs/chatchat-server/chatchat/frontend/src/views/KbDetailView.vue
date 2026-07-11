<template>
  <div class="kb-detail-page">
    <div class="page-header">
      <el-page-header @back="$router.push('/kb')">
        <template #content>
          <span class="kb-title">{{ kbName }}</span>
        </template>
      </el-page-header>
      <div class="header-actions">
        <el-upload
          :http-request="handleUpload"
          :show-file-list="false"
          multiple
          accept=".txt,.pdf,.md,.docx,.pptx,.xlsx,.html,.csv,.json"
        >
          <el-button type="primary" :icon="Upload">
            上传文件
          </el-button>
        </el-upload>
        <el-button :icon="Refresh" @click="handleRecreate" :loading="recreating">
          重建向量库
        </el-button>
      </div>
    </div>

    <div class="search-bar">
      <el-input
        v-model="searchQuery"
        placeholder="搜索文档内容..."
        clearable
        style="width: 360px"
        :prefix-icon="Search"
        @keyup.enter="handleSearch"
      />
    </div>

    <el-row :gutter="16">
      <el-col :span="16">
        <el-card shadow="never" class="content-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">文件列表</span>
              <span class="card-count">{{ fileList.length }} 个文件</span>
            </div>
          </template>
          <el-table :data="fileList" v-loading="loadingFiles" stripe>
            <el-table-column prop="file_name" label="文件名" min-width="200" show-overflow-tooltip />
            <el-table-column prop="file_ext" label="类型" width="80" />
            <el-table-column label="大小" width="100" align="center">
              <template #default="{ row }">
                {{ formatSize(row.file_size) }}
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100" align="center">
              <template #default="{ row }">
                <el-tag :type="row.status === 'green' ? 'success' : 'warning'" size="small" effect="plain">
                  {{ statusLabel(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <el-button link type="primary" size="small" @click="handleDownload(row.file_name)">下载</el-button>
                <el-button link type="danger" size="small" @click="handleDeleteFile(row.file_name)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!loadingFiles && fileList.length === 0" description="暂无文件，请上传" />
        </el-card>
      </el-col>

      <el-col :span="8">
        <el-card shadow="never" class="content-card">
          <template #header>
            <div class="card-header">
              <span class="card-title">搜索结果</span>
            </div>
          </template>
          <div v-if="searchResults.length === 0" class="no-results">
            <el-icon :size="36" color="#dcdfe6"><Search /></el-icon>
            <p>输入关键词搜索文档</p>
          </div>
          <div v-else class="search-results">
            <div
              v-for="(doc, idx) in searchResults"
              :key="idx"
              class="search-result-item"
            >
              <div class="result-header">
                <span class="result-file">{{ doc.file_name }}</span>
                <el-tag size="small" effect="plain">{{ doc.score?.toFixed(3) }}</el-tag>
              </div>
              <div class="result-content">{{ doc.content?.substring(0, 200) }}...</div>
            </div>
          </div>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Upload, Refresh, Search } from '@element-plus/icons-vue'
import {
  listFiles,
  uploadDocs,
  deleteDocs,
  searchDocs,
  recreateVectorStore,
  downloadDoc,
} from '@/api/kb'
import type { KnowledgeFile, SearchDocResult } from '@/types'

const route = useRoute()
const kbName = route.params.name as string

const fileList = ref<KnowledgeFile[]>([])
const loadingFiles = ref(false)
const recreating = ref(false)
const searchQuery = ref('')
const searchResults = ref<SearchDocResult[]>([])

async function fetchFiles() {
  loadingFiles.value = true
  try {
    const res = await listFiles(kbName)
    fileList.value = res.data || []
  } catch {
    ElMessage.error('获取文件列表失败')
  } finally {
    loadingFiles.value = false
  }
}

async function handleUpload(options: { file: File }) {
  try {
    await uploadDocs(kbName, [options.file])
    ElMessage.success('文件上传成功')
    await fetchFiles()
  } catch (err: any) {
    const detail = err?.response?.data?.detail
    ElMessage.error(typeof detail === 'string' ? detail : '文件上传失败')
  }
}

async function handleDeleteFile(fileName: string) {
  try {
    await ElMessageBox.confirm(`确认删除文件 "${fileName}"？`, '提示', {
      confirmButtonText: '确认',
      cancelButtonText: '取消',
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await deleteDocs(kbName, [fileName])
    ElMessage.success('删除成功')
    await fetchFiles()
  } catch {
    ElMessage.error('删除失败')
  }
}

async function handleRecreate() {
  recreating.value = true
  try {
    await recreateVectorStore(kbName)
    ElMessage.success('向量库重建完成')
    await fetchFiles()
  } catch {
    ElMessage.error('重建失败')
  } finally {
    recreating.value = false
  }
}

async function handleSearch() {
  if (!searchQuery.value.trim()) {
    searchResults.value = []
    return
  }
  try {
    const res = await searchDocs(kbName, searchQuery.value)
    searchResults.value = res.data || []
  } catch {
    ElMessage.error('搜索失败')
  }
}

async function handleDownload(fileName: string) {
  try {
    const blob = await downloadDoc(kbName, fileName)
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = fileName.split('/').pop() || fileName
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    ElMessage.error('下载失败')
  }
}

function formatSize(bytes: number): string {
  if (!bytes) return '0 B'
  const units = ['B', 'KB', 'MB', 'GB']
  let i = 0
  let size = bytes
  while (size >= 1024 && i < units.length - 1) {
    size /= 1024
    i++
  }
  return `${size.toFixed(1)} ${units[i]}`
}

function statusLabel(status: string): string {
  const map: Record<string, string> = { green: '就绪', yellow: '处理中', red: '失败' }
  return map[status] || status
}

onMounted(fetchFiles)
</script>

<style scoped>
.page-header {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 16px; padding: 12px 20px;
  background: #fff; border-radius: 8px; border: 1px solid #ebeef5;
}
.kb-title { font-size: 18px; font-weight: 700; }
.header-actions { display: flex; gap: 8px; }

.search-bar { margin-bottom: 16px; }

.content-card { border: 1px solid #ebeef5; border-radius: 8px; }
.card-header { display: flex; justify-content: space-between; align-items: center; }
.card-title { font-size: 14px; font-weight: 600; }
.card-count { font-size: 12px; color: #909399; }

.no-results {
  display: flex; flex-direction: column; align-items: center;
  padding: 40px 0; color: #c0c4cc; gap: 8px;
}

.search-results { max-height: 520px; overflow-y: auto; }
.search-result-item {
  padding: 10px 0; border-bottom: 1px solid #ebeef5;
}
.search-result-item:last-child { border-bottom: none; }
.result-header {
  display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;
}
.result-file { font-size: 13px; font-weight: 600; color: #409EFF; }
.result-content { font-size: 12px; color: #606266; line-height: 1.6; }
</style>
