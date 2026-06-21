<template>
  <div class="history-page">
    <el-card>
      <template #header>
        <div class="card-header">
          <span>对话历史</span>
          <el-button size="small" @click="loadHistory">
            <el-icon><Refresh /></el-icon>
            刷新
          </el-button>
        </div>
      </template>

      <el-empty v-if="histories.length === 0" description="暂无对话历史" />

      <div v-else class="history-list">
        <el-card
          v-for="(item, idx) in histories"
          :key="idx"
          shadow="hover"
          class="history-item"
          @click="viewHistory(item)"
        >
          <div class="history-info">
            <h4>{{ item.title }}</h4>
            <div class="history-meta">
              <el-tag size="small" :type="item.mode === 'kb' ? 'primary' : 'info'">
                {{ item.mode === 'kb' ? '知识库对话' : 'LLM 对话' }}
              </el-tag>
              <span class="history-time">{{ item.time }}</span>
              <span class="history-preview">{{ item.preview }}</span>
            </div>
          </div>
          <div class="history-actions">
            <el-button link type="primary" size="small" @click.stop="continueConversation(item)">
              <el-icon><VideoPlay /></el-icon>
              继续对话
            </el-button>
            <el-button link type="danger" size="small" @click.stop="deleteHistory(idx)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </el-card>
      </div>
    </el-card>

    <!-- View History Dialog -->
    <el-dialog v-model="dialogVisible" title="对话详情" width="700px">
      <div class="history-dialog-content">
        <div
          v-for="(msg, idx) in selectedHistory?.messages || []"
          :key="idx"
          :class="['history-msg', msg.role]"
        >
          <div class="history-msg-role">{{ msg.role === 'user' ? '用户' : '助手' }}</div>
          <div v-if="msg.docs && msg.docs.length > 0" class="history-msg-docs">
            <el-collapse>
              <el-collapse-item title="参考文档 ({{ msg.docs.length }})">
                <div v-for="(doc, i) in msg.docs" :key="i" class="history-doc-item" v-html="renderMarkdown(doc)" />
              </el-collapse-item>
            </el-collapse>
          </div>
          <div v-if="msg.tool_calls && msg.tool_calls.length > 0" class="history-msg-tools">
            <el-tag v-for="(tc, i) in msg.tool_calls" :key="i" type="warning" size="small">
              工具: {{ tc.function?.name }}
            </el-tag>
          </div>
          <div class="history-msg-content" v-html="renderMarkdown(msg.content)" />
        </div>
      </div>
      <template #footer>
        <el-button @click="dialogVisible = false">关闭</el-button>
        <el-button v-if="selectedHistory" type="primary" @click="continueConversation(selectedHistory)">继续对话</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { marked } from 'marked'
import type { ChatMessage } from '@/types'

const router = useRouter()

const renderOptions = { breaks: true, gfm: true }

interface HistoryItem {
  id: string
  title: string
  mode: string
  time: string
  preview: string
  messages: ChatMessage[]
}

const histories = ref<HistoryItem[]>([])
const dialogVisible = ref(false)
const selectedHistory = ref<HistoryItem | null>(null)

function loadHistory() {
  try {
    const raw = localStorage.getItem('chat_history')
    histories.value = raw ? JSON.parse(raw) : []
    histories.value.reverse()
  } catch {
    histories.value = []
  }
}

function viewHistory(item: HistoryItem) {
  selectedHistory.value = item
  dialogVisible.value = true
}

function deleteHistory(idx: number) {
  histories.value.splice(idx, 1)
  const reversed = [...histories.value].reverse()
  localStorage.setItem('chat_history', JSON.stringify(reversed))
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

loadHistory()
</script>

<style scoped>
.history-page {
  padding: 0;
}
.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.history-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
}
.history-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  cursor: pointer;
}
.history-actions {
  display: flex;
  gap: 4px;
  align-items: center;
  flex-shrink: 0;
}
.history-info h4 {
  margin: 0 0 6px 0;
  font-size: 15px;
}
.history-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
  color: #909399;
}
.history-preview {
  max-width: 300px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.history-dialog-content {
  max-height: 500px;
  overflow-y: auto;
}
.history-msg {
  padding: 10px;
  margin-bottom: 10px;
  border-radius: 6px;
}
.history-msg.user {
  background: #ecf5ff;
}
.history-msg.assistant {
  background: #f5f7fa;
}
.history-msg-role {
  font-size: 12px;
  font-weight: bold;
  margin-bottom: 4px;
  color: #409EFF;
}
.history-msg.assistant .history-msg-role {
  color: #67C23A;
}
.history-msg-content {
  line-height: 1.6;
  font-size: 13px;
}
.history-msg-content :deep(pre) {
  background: #fff;
  padding: 8px;
  border-radius: 4px;
  overflow-x: auto;
  font-size: 12px;
}
.history-msg-docs { margin-bottom: 6px; }
.history-doc-item { font-size: 12px; padding: 2px 0; }
.history-msg-tools { margin-bottom: 6px; display: flex; flex-wrap: wrap; gap: 4px; }
</style>
