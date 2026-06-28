<template>
  <div class="history-page">
    <div class="page-toolbar">
      <h3 class="page-title">对话历史</h3>
      <el-button size="small" :icon="Refresh" @click="loadHistory" :loading="loading">刷新</el-button>
    </div>

    <div v-if="loading" class="loading-state">
      <el-icon class="is-loading" :size="32"><Loading /></el-icon>
      <p>加载中...</p>
    </div>
    <el-empty v-else-if="histories.length === 0" description="暂无对话历史" />

    <div v-else class="history-grid">
      <div
        v-for="(item, idx) in histories"
        :key="idx"
        class="history-card"
        @click="viewHistory(item)"
      >
        <div class="history-card-body">
          <div class="history-card-top">
            <h4 class="history-title">{{ item.title }}</h4>
            <el-tag size="small" :type="item.mode === 'kb' ? 'primary' : 'success'" effect="plain">
              {{ item.mode === 'kb' ? '知识库' : 'LLM' }}
            </el-tag>
          </div>
          <div class="history-meta">
            <el-icon :size="14"><Clock /></el-icon>
            <span>{{ item.time }}</span>
          </div>
          <p class="history-preview">{{ item.preview || '暂无预览' }}</p>
        </div>
        <div class="history-card-actions" @click.stop>
          <el-button size="small" text type="primary" :icon="VideoPlay" @click="continueConversation(item)">
            继续
          </el-button>
          <el-button size="small" text type="danger" :icon="Delete" @click="deleteHistory(idx)">
            删除
          </el-button>
        </div>
      </div>
    </div>

    <!-- View History Dialog -->
    <el-dialog v-model="dialogVisible" title="对话详情" width="700px" class="history-dialog">
      <div v-if="dialogLoading" class="loading-state">
        <el-icon class="is-loading" :size="24"><Loading /></el-icon>
        <p>加载消息...</p>
      </div>
      <div v-else class="dialog-body">
        <el-empty v-if="!selectedHistory?.messages?.length" description="消息列表为空" />
        <div
          v-for="(msg, idx) in selectedHistory?.messages || []"
          :key="idx"
          :class="['dialog-msg', msg.role]"
        >
          <div class="dialog-msg-role">
            <el-icon v-if="msg.role === 'user'" :size="14"><UserFilled /></el-icon>
            <el-icon v-else :size="14"><Cpu /></el-icon>
            {{ msg.role === 'user' ? '用户' : '助手' }}
          </div>
          <div v-if="msg.docs && msg.docs.length > 0" class="dialog-msg-docs">
            <el-collapse>
              <el-collapse-item title="参考文档 ({{ msg.docs.length }})">
                <div v-for="(doc, i) in msg.docs" :key="i" class="dialog-doc-item" v-html="renderMarkdown(doc)" />
              </el-collapse-item>
            </el-collapse>
          </div>
          <div v-if="msg.tool_calls && msg.tool_calls.length > 0" class="dialog-msg-tools">
            <el-tag v-for="(tc, i) in msg.tool_calls" :key="i" type="warning" size="small" effect="plain">
              {{ tc.function?.name }}
            </el-tag>
          </div>
          <div class="dialog-msg-content" v-html="renderMarkdown(msg.content)" />
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button v-if="selectedHistory" type="primary" :icon="VideoPlay" @click="continueConversation(selectedHistory)">
          继续对话
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import { Clock, VideoPlay, Delete, Refresh, Loading, UserFilled, Cpu } from '@element-plus/icons-vue'
import type { ChatMessage } from '@/types'
import { listConversations, getConversation, deleteConversation } from '@/api/chat'

const router = useRouter()

const renderOptions = { breaks: true, gfm: true }

interface HistoryItem {
  id: string
  title: string
  mode: string
  time: string
  preview: string
  messages: ChatMessage[]
  source: 'server' | 'local'
}

const histories = ref<HistoryItem[]>([])
const dialogVisible = ref(false)
const dialogLoading = ref(false)
const selectedHistory = ref<HistoryItem | null>(null)
const loading = ref(false)

async function loadHistory() {
  loading.value = true
  const seen = new Set<string>()
  const items: HistoryItem[] = []

  try {
    const res = await listConversations()
    if (res.code === 200 && res.data) {
      for (const c of res.data) {
        items.push({
          id: c.id,
          title: c.name || '对话',
          mode: c.chat_type === 'llm_chat' ? 'llm' : 'kb',
          time: c.create_time ? new Date(c.create_time).toLocaleString() : '',
          preview: c.name || '',
          messages: [],
          source: 'server',
        })
        seen.add(c.id)
      }
    }
  } catch { /* ignore */ }

  try {
    const raw = localStorage.getItem('chat_history')
    const local: HistoryItem[] = raw ? JSON.parse(raw) : []
    for (const item of local) {
      if (!seen.has(item.id)) {
        items.push({ ...item, source: 'local' })
      }
    }
  } catch { /* ignore */ }

  histories.value = items
  loading.value = false
}

async function viewHistory(item: HistoryItem) {
  dialogVisible.value = true
  selectedHistory.value = item
  if (item.source === 'server') {
    dialogLoading.value = true
    try {
      const res = await getConversation(item.id)
      if (res.code === 200 && res.data) {
        const messages: ChatMessage[] = []
        for (const m of res.data.messages || []) {
          messages.push({ role: 'user', content: m.query, timestamp: 0 })
          if (m.response) {
            messages.push({ role: 'assistant', content: m.response, timestamp: 0 })
          }
        }
        selectedHistory.value = { ...item, messages }
      }
    } catch { /* fall through */ }
    dialogLoading.value = false
  }
}

async function deleteHistory(idx: number) {
  const item = histories.value[idx]
  if (item.source === 'server') {
    try {
      await deleteConversation(item.id)
    } catch { /* ignore */ }
  } else {
    try {
      const raw = localStorage.getItem('chat_history')
      const local: HistoryItem[] = raw ? JSON.parse(raw) : []
      const updated = local.filter((x) => x.id !== item.id)
      localStorage.setItem('chat_history', JSON.stringify(updated))
    } catch { /* ignore */ }
  }
  histories.value.splice(idx, 1)
}

function continueConversation(item: HistoryItem) {
  localStorage.setItem('continue_conversation', JSON.stringify({
    messages: item.messages,
    conversation_id: item.id,
    mode: item.mode,
  }))
  dialogVisible.value = false
  router.push(item.mode === 'kb' ? '/chat' : '/llm-chat')
}

function renderMarkdown(text: string): string {
  try {
    return marked(text, renderOptions) as string
  } catch {
    return text
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.history-page { max-width: 960px; margin: 0 auto; }
.page-toolbar {
  display: flex; justify-content: space-between; align-items: center;
  margin-bottom: 20px;
}
.page-title { margin: 0; font-size: 18px; font-weight: 600; color: #303133; }

.loading-state {
  display: flex; flex-direction: column; align-items: center;
  padding: 60px 0; color: #909399; gap: 12px;
}

.history-grid {
  display: flex; flex-direction: column; gap: 12px;
}

.history-card {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; background: #fff; border-radius: 8px;
  border: 1px solid #ebeef5; cursor: pointer;
  transition: all 0.2s ease;
}
.history-card:hover {
  border-color: #409EFF; box-shadow: 0 2px 12px rgba(64,158,255,0.12);
  transform: translateY(-1px);
}
.history-card-body { flex: 1; min-width: 0; }
.history-card-top { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; }
.history-title {
  margin: 0; font-size: 15px; font-weight: 600; color: #303133;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
}
.history-meta {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; color: #909399; margin-bottom: 6px;
}
.history-preview {
  margin: 0; font-size: 13px; color: #606266;
  overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  max-width: 600px;
}
.history-card-actions {
  display: flex; gap: 4px; flex-shrink: 0; margin-left: 16px;
}

/* Dialog */
.dialog-body { max-height: 500px; overflow-y: auto; }
.dialog-msg {
  padding: 12px 16px; margin-bottom: 10px; border-radius: 8px;
}
.dialog-msg.user { background: #ecf5ff; }
.dialog-msg.assistant { background: #f5f7fa; }
.dialog-msg-role {
  display: flex; align-items: center; gap: 4px;
  font-size: 12px; font-weight: 600; margin-bottom: 6px; color: #409EFF;
}
.dialog-msg.assistant .dialog-msg-role { color: #67C23A; }
.dialog-msg-content {
  line-height: 1.7; font-size: 13px; color: #303133;
}
.dialog-msg-content :deep(pre) {
  background: #fff; padding: 10px; border-radius: 6px; overflow-x: auto;
  font-size: 12px; border: 1px solid #ebeef5;
}
.dialog-msg-content :deep(code) { font-family: Consolas, Monaco, monospace; }
.dialog-msg-docs { margin-bottom: 6px; }
.dialog-doc-item { font-size: 12px; padding: 3px 0; }
.dialog-msg-tools { margin-bottom: 6px; display: flex; flex-wrap: wrap; gap: 6px; }
</style>
