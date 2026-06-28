<template>
  <div class="chat-page">
    <div class="chat-sidebar">
      <div class="sidebar-section">
        <div class="section-label">
          <el-icon :size="14"><FolderOpened /></el-icon>
          <span>知识库</span>
        </div>
        <el-select v-model="selectedKb" placeholder="选择知识库" size="small" style="width: 100%">
          <el-option v-for="kb in kbList" :key="kb.kb_name" :label="kb.kb_name" :value="kb.kb_name" />
        </el-select>
      </div>

      <div class="sidebar-section">
        <div class="section-label">
          <el-icon :size="14"><Upload /></el-icon>
          <span>文件上传</span>
        </div>
        <el-upload
          :http-request="handleUpload" :show-file-list="false" drag multiple
          accept=".txt,.pdf,.md,.docx,.pptx,.xlsx,.html,.csv"
          class="upload-box"
        >
          <el-icon class="upload-icon" :size="28"><UploadFilled /></el-icon>
          <div class="upload-text">拖拽文件上传</div>
        </el-upload>
      </div>

      <div class="sidebar-section">
        <div class="section-label">
          <el-icon :size="14"><Setting /></el-icon>
          <span>检索参数</span>
        </div>
        <div class="param-row">
          <span class="param-name">Top K</span>
          <span class="param-value">{{ topK }}</span>
        </div>
        <el-slider v-model="topK" :min="1" :max="20" size="small" />
        <div class="param-row">
          <span class="param-name">相似度阈值</span>
          <span class="param-value">{{ scoreThreshold }}</span>
        </div>
        <el-slider v-model="scoreThreshold" :min="0" :max="1" :step="0.05" size="small" />
      </div>

      <div class="sidebar-section">
        <div class="section-label">
          <el-icon :size="14"><Switch /></el-icon>
          <span>对话模式</span>
        </div>
        <el-radio-group v-model="chatMode" class="mode-group">
          <el-radio value="local_kb" size="small">本地知识库</el-radio>
          <el-radio value="temp_kb" size="small">临时文件</el-radio>
          <el-radio value="search_engine" size="small">搜索引擎</el-radio>
        </el-radio-group>
      </div>

      <div class="sidebar-actions">
        <el-button :icon="Plus" @click="newConversation" plain>新对话</el-button>
        <el-button :icon="Delete" @click="clearMessages" plain>清空消息</el-button>
      </div>

      <div class="sidebar-footer">
        <div v-if="conversationId" class="conv-info">
          <el-icon :size="12"><ChatDotRound /></el-icon>
          <span>{{ conversationId.substring(0, 8) }}...</span>
        </div>
        <div v-else class="conv-info dim">
          <el-icon :size="12"><ChatDotRound /></el-icon>
          <span>暂无会话</span>
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div ref="chatContainer" class="chat-messages">
        <div v-if="messages.length === 0 && !isStreaming" class="chat-placeholder">
          <el-icon :size="52" color="#dcdfe6"><ChatDotRound /></el-icon>
          <p class="placeholder-title">选择知识库，开始对话</p>
          <p class="placeholder-hint">上传文档后即可基于知识库进行问答</p>
        </div>

        <template v-for="(msg, idx) in messages" :key="idx">
          <MessageBubble
            :role="msg.role"
            :content="msg.content"
            :timestamp="msg.timestamp"
            :is-ref="msg.is_ref"
            :docs="msg.docs"
            :tool-calls="msg.tool_calls"
            :thinking="msg.thinking"
          />
        </template>

        <div v-if="isStreaming && streamDocs.length > 0" class="ref-docs-block">
          <el-collapse>
            <el-collapse-item title="参考文档 ({{ streamDocs.length }})">
              <div v-for="(doc, i) in streamDocs" :key="i" class="ref-doc-item" v-html="renderMarkdown(doc)" />
            </el-collapse-item>
          </el-collapse>
        </div>

        <div v-if="isStreaming && currentThinking" class="thinking-indicator">
          <el-icon class="is-loading"><Loading /></el-icon>
          <span>{{ currentThinking }}</span>
        </div>

        <div v-if="isStreaming && streamToolCalls.length > 0" class="tool-calls-block">
          <div v-for="(tc, i) in streamToolCalls" :key="i" class="tool-call-item">
            <el-tag type="warning" size="small" effect="plain">工具: {{ tc.function?.name }}</el-tag>
            <span v-if="tc.tool_output" class="tool-output">{{ tc.tool_output.substring(0, 200) }}...</span>
          </div>
        </div>

        <div v-if="isStreaming && thinkingContent" class="message-bubble assistant">
          <div class="message-avatar">
            <el-avatar :size="32" icon="Cpu" style="background: #E6A23C" />
          </div>
          <div class="message-content">
            <el-collapse>
              <el-collapse-item title="思考过程">
                <div class="markdown-body" v-html="renderMarkdown(thinkingContent)" />
              </el-collapse-item>
            </el-collapse>
          </div>
        </div>

        <div v-if="isStreaming && (streamingContent || currentThinking)" class="message-bubble assistant">
          <div class="message-avatar">
            <el-avatar :size="32" icon="Cpu" style="background: #409EFF" />
          </div>
          <div class="message-content">
            <div v-if="streamingContent" class="markdown-body" v-html="renderMarkdown(streamingContent)" />
            <span v-if="streamingContent" class="streaming-cursor">|</span>
          </div>
        </div>

        <div v-if="error" class="error-block">
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
            <el-tag v-if="conversationId" size="small" type="info" effect="plain">
              会话: {{ conversationId.substring(0, 8) }}...
            </el-tag>
          </div>
          <div class="input-right">
            <el-button v-if="isStreaming" type="danger" :icon="VideoPause" @click="stopStreaming">停止</el-button>
            <el-button v-else type="primary" :icon="Promotion" :disabled="!inputText.trim() || !selectedKb" @click="sendMessage">发送</el-button>
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
import { FolderOpened, Upload, UploadFilled, Setting, Switch, Plus, Delete, Loading, VideoPause, Promotion, ChatDotRound, Cpu } from '@element-plus/icons-vue'

const renderOptions = { breaks: true, gfm: true }

const {
  messages,
  streamingContent,
  thinkingContent,
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
  restoreSession,
} = useChat()

const selectedKb = ref('')
const kbList = ref<KnowledgeBase[]>([])
const chatMode = ref<'local_kb' | 'temp_kb' | 'search_engine'>('local_kb')
const topK = ref(3)
const scoreThreshold = ref(0.5)
const inputText = ref('')
const uploading = ref(false)

onMounted(async () => {
  restoreSession('kb')
  try {
    const res = await listKbs()
    kbList.value = res.data || []
    if (kbList.value.length > 0 && !selectedKb.value) selectedKb.value = kbList.value[0].kb_name
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

/* ---- Sidebar ---- */
.chat-sidebar {
  width: 240px; background: #fff; border-right: 1px solid #ebeef5;
  display: flex; flex-direction: column; padding: 16px 12px; overflow-y: auto; gap: 4px;
}
.sidebar-section {
  background: #fafbfc; border: 1px solid #ebeef5; border-radius: 8px;
  padding: 12px; margin-bottom: 4px;
}
.section-label {
  display: flex; align-items: center; gap: 6px;
  font-size: 13px; font-weight: 600; color: #303133; margin-bottom: 10px;
}

/* Upload */
.upload-box { width: 100%; }
.upload-box :deep(.el-upload-dragger) {
  padding: 16px 8px; border-radius: 6px;
}
.upload-icon { color: #c0c4cc; }
.upload-text { font-size: 12px; color: #909399; margin-top: 4px; }

/* Params */
.param-row {
  display: flex; justify-content: space-between; align-items: center;
  margin: 4px 0 2px;
}
.param-name { font-size: 12px; color: #606266; }
.param-value { font-size: 12px; color: #409EFF; font-weight: 500; }

/* Mode */
.mode-group { display: flex; flex-direction: column; gap: 4px; }
.mode-group .el-radio { margin-right: 0; }

/* Action buttons */
.sidebar-actions {
  display: flex; flex-direction: column; gap: 6px; padding: 4px 0;
}
.sidebar-actions .el-button {
  justify-content: center; height: 34px;
  border-radius: 6px; font-size: 13px;
}

/* Footer */
.sidebar-footer { margin-top: auto; padding-top: 12px; }
.conv-info {
  display: flex; align-items: center; gap: 6px;
  font-size: 12px; color: #606266; padding: 8px 10px;
  background: #f5f7fa; border-radius: 6px;
}
.conv-info.dim { color: #c0c4cc; }

/* ---- Main Chat ---- */
.chat-main { flex: 1; display: flex; flex-direction: column; background: #f5f7fa; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px 28px; }
.chat-placeholder {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; color: #c0c4cc; gap: 10px;
}
.placeholder-title { font-size: 15px; color: #909399; margin: 0; }
.placeholder-hint { font-size: 12px; color: #c0c4cc; margin: 0; }

/* Input */
.chat-input-area {
  padding: 14px 24px 16px; background: #fff;
  border-top: 1px solid #ebeef5;
}
.input-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }
.input-left { display: flex; align-items: center; gap: 8px; }

/* Message bubbles */
.message-bubble { display: flex; gap: 10px; margin-bottom: 18px; }
.message-bubble.user { flex-direction: row-reverse; }
.message-avatar { flex-shrink: 0; }
.message-content {
  max-width: 72%; padding: 12px 16px; border-radius: 10px;
  background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
  line-height: 1.65;
}
.markdown-body { line-height: 1.7; font-size: 14px; }
.markdown-body :deep(pre) {
  background: #f5f7fa; padding: 12px; border-radius: 6px; overflow-x: auto;
  border: 1px solid #ebeef5;
}
.markdown-body :deep(code) { font-family: Consolas, Monaco, monospace; font-size: 13px; }
.streaming-cursor { animation: blink 1s infinite; color: #409EFF; font-weight: bold; }
@keyframes blink { 50% { opacity: 0; } }

.ref-docs-block { margin: 8px 0; padding: 0 40px; }
.ref-doc-item { font-size: 12px; color: #606266; padding: 4px 0; border-bottom: 1px solid #ebeef5; }
.thinking-indicator { display: flex; align-items: center; gap: 8px; padding: 8px 40px; color: #909399; font-size: 13px; }
.tool-calls-block { padding: 8px 40px; }
.tool-call-item { margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
.tool-output { font-size: 12px; color: #606266; }
.error-block { padding: 12px 0; }
</style>
