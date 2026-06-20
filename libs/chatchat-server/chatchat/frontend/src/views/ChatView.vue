<template>
  <div class="chat-page">
    <div class="chat-sidebar">
      <el-tabs v-model="sidebarTab">
        <el-tab-pane label="知识库" name="kb">
          <div class="sidebar-section">
            <el-select v-model="selectedKb" placeholder="选择知识库" style="width: 100%">
              <el-option v-for="kb in kbList" :key="kb.kb_name" :label="kb.kb_name" :value="kb.kb_name" />
            </el-select>
          </div>
          <div class="sidebar-section">
            <el-upload
              :http-request="handleUpload" :show-file-list="false" drag multiple
              accept=".txt,.pdf,.md,.docx,.pptx,.xlsx,.html,.csv"
            >
              <el-icon class="upload-icon"><UploadFilled /></el-icon>
              <div class="upload-text">拖拽文件到此处上传</div>
            </el-upload>
          </div>
          <div class="sidebar-section">
            <div class="kb-params">
              <span class="param-label">Top K: {{ topK }}</span>
              <el-slider v-model="topK" :min="1" :max="20" size="small" />
              <span class="param-label">阈值: {{ scoreThreshold }}</span>
              <el-slider v-model="scoreThreshold" :min="0" :max="1" :step="0.05" size="small" />
            </div>
          </div>
        </el-tab-pane>
        <el-tab-pane label="模式" name="mode">
          <div class="sidebar-section">
            <el-radio-group v-model="chatMode" style="display: flex; flex-direction: column; gap: 8px">
              <el-radio value="local_kb">本地知识库</el-radio>
              <el-radio value="temp_kb">临时文件</el-radio>
              <el-radio value="search_engine">搜索引擎</el-radio>
            </el-radio-group>
          </div>
        </el-tab-pane>
      </el-tabs>
      <div class="sidebar-actions">
        <el-button size="small" @click="newConversation">新对话</el-button>
        <el-button size="small" @click="clearMessages">清空消息</el-button>
      </div>
    </div>

    <div class="chat-main">
      <div ref="chatContainer" class="chat-messages">
        <div v-if="messages.length === 0 && !isStreaming" class="chat-placeholder">
          <el-icon :size="48" color="#c0c4cc"><ChatDotRound /></el-icon>
          <p>选择知识库，开始对话</p>
        </div>

        <template v-for="(msg, idx) in messages" :key="idx">
          <MessageBubble
            :role="msg.role"
            :content="msg.content"
            :timestamp="msg.timestamp"
            :is-ref="msg.is_ref"
            :docs="msg.docs"
            :tool-calls="msg.tool_calls"
          />
        </template>

        <!-- Streaming: reference docs -->
        <div v-if="isStreaming && streamDocs.length > 0" class="ref-docs-block">
          <el-collapse>
            <el-collapse-item title="参考文档 ({{ streamDocs.length }})">
              <div v-for="(doc, i) in streamDocs" :key="i" class="ref-doc-item" v-html="renderMarkdown(doc)" />
            </el-collapse-item>
          </el-collapse>
        </div>

        <!-- Streaming: thinking status -->
        <div v-if="isStreaming && currentThinking" class="thinking-indicator">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>{{ currentThinking }}</span>
        </div>

        <!-- Streaming: tool calls -->
        <div v-if="isStreaming && streamToolCalls.length > 0" class="tool-calls-block">
          <div v-for="(tc, i) in streamToolCalls" :key="i" class="tool-call-item">
            <el-tag type="warning" size="small">工具: {{ tc.function?.name }}</el-tag>
            <span v-if="tc.tool_output" class="tool-output">{{ tc.tool_output.substring(0, 200) }}...</span>
          </div>
        </div>

        <!-- Streaming: text -->
        <div v-if="isStreaming && (streamingContent || currentThinking)" class="message-bubble assistant">
          <div class="message-avatar">
            <el-avatar :size="32" icon="Cpu" style="background: #409EFF" />
          </div>
          <div class="message-content">
            <div v-if="streamingContent" class="markdown-body" v-html="renderMarkdown(streamingContent)" />
            <span v-if="streamingContent" class="streaming-cursor">|</span>
          </div>
        </div>

        <div v-if="error" style="padding: 16px">
          <el-alert :title="error" type="error" show-icon :closable="false" />
        </div>
      </div>

      <div class="chat-input-area">
        <el-input
          v-model="inputText" type="textarea" :rows="3"
          placeholder="输入问题，按 Enter 发送，Shift+Enter 换行"
          :disabled="isStreaming" resize="none"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <div class="input-actions">
          <div class="input-left">
            <el-tag v-if="conversationId" size="small" type="info">会话: {{ conversationId.substring(0, 8) }}...</el-tag>
          </div>
          <div>
            <el-button v-if="isStreaming" type="danger" @click="stopStreaming">停止</el-button>
            <el-button v-else type="primary" :disabled="!inputText.trim() || !selectedKb" @click="sendMessage">发送</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useChat } from '@/composables/useChat'
import { listKbs, uploadDocs } from '@/api/kb'
import MessageBubble from '@/components/MessageBubble.vue'
import type { KnowledgeBase } from '@/types'
import { marked } from 'marked'

const renderOptions = { breaks: true, gfm: true }

const {
  messages,
  streamingContent,
  streamDocs,
  streamToolCalls,
  currentThinking,
  isStreaming,
  error,
  conversationId,
  chatContainer,
  sendKbQuery,
  stopStreaming,
  clearMessages,
  newConversation,
} = useChat()

const selectedKb = ref('')
const kbList = ref<KnowledgeBase[]>([])
const sidebarTab = ref('kb')
const chatMode = ref<'local_kb' | 'temp_kb' | 'search_engine'>('local_kb')
const topK = ref(3)
const scoreThreshold = ref(0.5)
const inputText = ref('')
const uploading = ref(false)

onMounted(async () => {
  try {
    const res = await listKbs()
    kbList.value = res.data || []
    if (kbList.value.length > 0) selectedKb.value = kbList.value[0].kb_name
  } catch { /* ignore */ }
})

function renderMarkdown(text: string): string {
  try { return marked(text, renderOptions) as string } catch { return text }
}

async function sendMessage() {
  if (!inputText.value.trim() || isStreaming.value) return
  const query = inputText.value.trim()
  inputText.value = ''
  await sendKbQuery(query, selectedKb.value, chatMode.value)
}

async function handleUpload(options: { file: File }) {
  if (!selectedKb.value) { ElMessage.warning('请先选择知识库'); return }
  uploading.value = true
  try {
    await uploadDocs(selectedKb.value, [options.file])
    ElMessage.success('文件上传成功')
  } catch { ElMessage.error('文件上传失败') }
  finally { uploading.value = false }
}
</script>

<style scoped>
.chat-page { display: flex; height: calc(100vh - 92px); }
.chat-sidebar {
  width: 260px; background: #fff; border-right: 1px solid #e6e6e6;
  display: flex; flex-direction: column; padding: 12px; overflow-y: auto;
}
.sidebar-section { margin-bottom: 16px; }
.sidebar-actions {
  margin-top: auto; padding-top: 12px; border-top: 1px solid #e6e6e6;
  display: flex; gap: 8px;
}
.kb-params { padding: 8px 0; }
.param-label { font-size: 12px; color: #909399; }
.upload-icon { font-size: 32px; color: #c0c4cc; }
.upload-text { font-size: 12px; color: #909399; margin-top: 8px; }
.chat-main { flex: 1; display: flex; flex-direction: column; background: #f5f7fa; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px 24px; }
.chat-placeholder {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; color: #c0c4cc; gap: 12px;
}
.chat-input-area { padding: 16px 24px; background: #fff; border-top: 1px solid #e6e6e6; }
.input-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
.input-left { display: flex; align-items: center; gap: 8px; }

.message-bubble { display: flex; gap: 10px; margin-bottom: 16px; }
.message-bubble.user { flex-direction: row-reverse; }
.message-avatar { flex-shrink: 0; }
.message-content {
  max-width: 70%; padding: 10px 14px; border-radius: 8px;
  background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.markdown-body { line-height: 1.6; }
.streaming-cursor { animation: blink 1s infinite; color: #409EFF; }
@keyframes blink { 50% { opacity: 0; } }

.ref-docs-block { margin: 8px 0; padding: 0 40px; }
.ref-doc-item { font-size: 12px; color: #606266; padding: 4px 0; border-bottom: 1px solid #ebeef5; }
.thinking-indicator { display: flex; align-items: center; gap: 8px; padding: 8px 40px; color: #909399; font-size: 13px; }
.tool-calls-block { padding: 8px 40px; }
.tool-call-item { margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
.tool-output { font-size: 12px; color: #606266; }
</style>
