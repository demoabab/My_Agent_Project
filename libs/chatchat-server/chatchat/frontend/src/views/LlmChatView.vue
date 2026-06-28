<template>
  <div class="llm-chat-page">
    <div class="chat-sidebar">
      <div class="sidebar-section">
        <div class="section-label">
          <el-icon :size="14"><Tools /></el-icon>
          <span>工具选择 (Agent)</span>
        </div>
        <el-empty v-if="Object.keys(availableTools).length === 0" description="无可用工具" :image-size="40" />
        <el-checkbox-group v-else v-model="selectedTools" class="tool-list">
          <div v-for="(info, name) in availableTools" :key="name" class="tool-item">
            <el-checkbox :value="name" :label="name">
              <el-tooltip :content="info.description" placement="left" :show-after="300">
                <span class="tool-name">{{ info.title || name }}</span>
              </el-tooltip>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </div>

      <div class="sidebar-section">
        <div class="section-label">
          <el-icon :size="14"><Connection /></el-icon>
          <span>扩展功能</span>
        </div>
        <div class="mcp-row" :class="{ active: useMcp }" @click="useMcp = !useMcp">
          <span class="mcp-label">MCP 模式</span>
          <el-switch v-model="useMcp" size="small" @click.stop />
        </div>
      </div>

      <div class="sidebar-actions">
        <el-button :icon="Plus" @click="newConversation" plain>
          新对话
        </el-button>
        <el-button :icon="Delete" @click="clearMessages" plain>
          清空消息
        </el-button>
      </div>

      <div class="sidebar-footer">
        <div v-if="conversationId" class="conv-info">
          <el-icon :size="12"><ChatLineSquare /></el-icon>
          <span>{{ conversationId.substring(0, 8) }}...</span>
        </div>
        <div v-else class="conv-info dim">
          <el-icon :size="12"><ChatLineSquare /></el-icon>
          <span>暂无会话</span>
        </div>
      </div>
    </div>

    <div class="chat-main">
      <div ref="chatContainer" class="chat-messages">
        <div v-if="messages.length === 0 && !isStreaming" class="chat-placeholder">
          <el-icon :size="52" color="#dcdfe6"><ChatLineSquare /></el-icon>
          <p class="placeholder-title">开始 LLM 对话</p>
          <p v-if="selectedTools.length > 0" class="placeholder-hint">
            已选择工具: {{ selectedTools.join(', ') }}
          </p>
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
          v-model="inputText"
          type="textarea"
          :rows="3"
          placeholder="输入问题，按 Enter 发送，Shift+Enter 换行"
          :disabled="isStreaming"
          resize="none"
          @keydown.enter.exact.prevent="sendMessage"
        />
        <div class="input-actions">
          <div class="input-left">
            <el-select v-model="selectedModel" size="small" placeholder="选择模型" style="width: 160px" clearable>
              <el-option label="默认模型" value="" />
              <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
            </el-select>
            <div class="temp-control">
              <span class="param-label">温度</span>
              <el-input-number v-model="temperature" :min="0" :max="2" :step="0.1" size="small" style="width: 90px" controls-position="right" />
            </div>
          </div>
          <div class="input-right">
            <el-button v-if="isStreaming" type="danger" :icon="VideoPause" @click="stopStreaming">停止</el-button>
            <el-button v-else type="primary" :icon="Promotion" :disabled="!inputText.trim()" @click="sendMessage">发送</el-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useChat } from '@/composables/useChat'
import { getLlmModels, listTools } from '@/api/server'
import MessageBubble from '@/components/MessageBubble.vue'
import { marked } from 'marked'
import { Tools, Connection, Plus, Delete, Loading, VideoPause, Promotion, ChatLineSquare, Cpu } from '@element-plus/icons-vue'

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
  sendLlmQuery,
  stopStreaming,
  clearMessages,
  newConversation,
  restoreSession,
} = useChat()

const inputText = ref('')
const selectedModel = ref('')
const temperature = ref(0.7)
const availableModels = ref<string[]>([])
const availableTools = ref<Record<string, { name: string; title: string; description: string; args: Record<string, unknown>; config: Record<string, unknown> }>>({})
const selectedTools = ref<string[]>([])
const useMcp = ref(false)

onMounted(async () => {
  restoreSession('llm')
  try {
    const res = await getLlmModels()
    availableModels.value = res.data || []
  } catch { /* ignore */ }
  try {
    const res = await listTools()
    availableTools.value = (res.data as Record<string, never>) || {}
  } catch { /* ignore */ }
})

function renderMarkdown(text: string): string {
  try { return marked(text, renderOptions) as string } catch { return text }
}

async function sendMessage() {
  if (!inputText.value.trim() || isStreaming.value) return
  const query = inputText.value.trim()
  inputText.value = ''
  await sendLlmQuery(
    query,
    selectedTools.value.length > 0 ? selectedTools.value : undefined,
    selectedModel.value || undefined,
    useMcp.value
  )
}
</script>

<style scoped>
.llm-chat-page { display: flex; height: calc(100vh - 92px); }

/* ---- Sidebar ---- */
.chat-sidebar {
  width: 230px; background: #fff; border-right: 1px solid #ebeef5;
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

/* Tool list */
.tool-list { display: flex; flex-direction: column; gap: 2px; }
.tool-item {
  padding: 5px 8px; border-radius: 6px;
  transition: background 0.15s;
}
.tool-item:hover { background: #f0f5ff; }
.tool-name { font-size: 13px; color: #303133; }

/* MCP row */
.mcp-row {
  display: flex; align-items: center; justify-content: space-between;
  padding: 8px 10px; border-radius: 6px; cursor: pointer;
  transition: background 0.15s;
}
.mcp-row:hover { background: #f0f5ff; }
.mcp-row.active { background: #ecf5ff; }
.mcp-label { font-size: 13px; color: #303133; }

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

/* ---- Main Chat Area ---- */
.chat-main { flex: 1; display: flex; flex-direction: column; background: #f5f7fa; }
.chat-messages { flex: 1; overflow-y: auto; padding: 20px 28px; }
.chat-placeholder {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; color: #c0c4cc; gap: 10px;
}
.placeholder-title { font-size: 15px; color: #909399; margin: 0; }
.placeholder-hint { font-size: 12px; color: #c0c4cc; margin: 0; }

/* Input area */
.chat-input-area {
  padding: 14px 24px 16px; background: #fff;
  border-top: 1px solid #ebeef5;
}
.input-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 10px; }
.input-left { display: flex; align-items: center; gap: 10px; }
.temp-control { display: flex; align-items: center; gap: 6px; }
.param-label { font-size: 12px; color: #909399; }

/* Message bubbles (shared) */
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

.thinking-indicator { display: flex; align-items: center; gap: 8px; padding: 8px 0; color: #909399; font-size: 13px; }
.tool-calls-block { padding: 8px 0; }
.tool-call-item { margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
.tool-output { font-size: 12px; color: #606266; }
.error-block { padding: 12px 0; }
</style>
