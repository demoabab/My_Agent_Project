<template>
  <div class="llm-chat-page">
    <div class="chat-sidebar">
      <div class="sidebar-section">
        <h4>工具选择 (Agent)</h4>
        <el-empty v-if="Object.keys(availableTools).length === 0" description="无可用工具" :image-size="40" />
        <el-checkbox-group v-else v-model="selectedTools" class="tool-checkbox-group">
          <el-checkbox v-for="(info, name) in availableTools" :key="name" :value="name" :label="name">
            <el-tooltip :content="info.description" placement="left">
              <span>{{ info.title || name }}</span>
            </el-tooltip>
          </el-checkbox>
        </el-checkbox-group>
      </div>
      <div class="sidebar-section">
        <el-checkbox v-model="useMcp" border size="small" style="width: 100%">
          MCP 模式
        </el-checkbox>
      </div>
      <div class="sidebar-section">
        <el-button size="small" @click="newConversation" style="width: 100%">新对话</el-button>
        <el-button size="small" @click="clearMessages" style="width: 100%; margin-top: 6px">清空消息</el-button>
      </div>
      <div class="sidebar-footer">
        <el-tag v-if="conversationId" size="small" type="info">会话: {{ conversationId.substring(0, 8) }}...</el-tag>
      </div>
    </div>

    <div class="chat-main">
      <div ref="chatContainer" class="chat-messages">
        <div v-if="messages.length === 0 && !isStreaming" class="chat-placeholder">
          <el-icon :size="48" color="#c0c4cc"><ChatLineSquare /></el-icon>
          <p>开始 LLM 对话</p>
          <p v-if="selectedTools.length > 0" style="font-size: 12px; color: #909399">
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
          />
        </template>

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
            <el-select v-model="selectedModel" size="small" placeholder="模型" style="width: 160px" clearable>
              <el-option label="默认" value="" />
              <el-option v-for="m in availableModels" :key="m" :label="m" :value="m" />
            </el-select>
            <el-input-number v-model="temperature" :min="0" :max="2" :step="0.1" size="small" style="width: 100px" controls-position="right" />
            <span class="param-label-small">温度</span>
          </div>
          <div>
            <el-button v-if="isStreaming" type="danger" @click="stopStreaming">停止</el-button>
            <el-button v-else type="primary" :disabled="!inputText.trim()" @click="sendMessage">发送</el-button>
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
  sendLlmQuery,
  stopStreaming,
  clearMessages,
  newConversation,
} = useChat()

const inputText = ref('')
const selectedModel = ref('')
const temperature = ref(0.7)
const availableModels = ref<string[]>([])
const availableTools = ref<Record<string, { name: string; title: string; description: string; args: Record<string, unknown>; config: Record<string, unknown> }>>({})
const selectedTools = ref<string[]>([])
const useMcp = ref(false)

onMounted(async () => {
  try {
    const [modelRes, toolRes] = await Promise.all([
      getLlmModels(),
      listTools(),
    ])
    availableModels.value = modelRes.data || []
    availableTools.value = (toolRes.data as Record<string, never>) || {}
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
.chat-sidebar {
  width: 220px; background: #fff; border-right: 1px solid #e6e6e6;
  display: flex; flex-direction: column; padding: 12px; overflow-y: auto;
}
.sidebar-section { margin-bottom: 16px; }
.sidebar-section h4 { margin: 0 0 8px 0; font-size: 13px; color: #303133; }
.sidebar-footer { margin-top: auto; padding-top: 12px; border-top: 1px solid #e6e6e6; }
.tool-checkbox-group { display: flex; flex-direction: column; gap: 6px; }
.chat-main { flex: 1; display: flex; flex-direction: column; background: #f5f7fa; }
.chat-messages { flex: 1; overflow-y: auto; padding: 16px 24px; }
.chat-placeholder {
  display: flex; flex-direction: column; align-items: center;
  justify-content: center; height: 100%; color: #c0c4cc; gap: 12px;
}
.chat-input-area { padding: 16px 24px; background: #fff; border-top: 1px solid #e6e6e6; }
.input-actions { display: flex; justify-content: space-between; align-items: center; margin-top: 8px; }
.input-left { display: flex; align-items: center; gap: 8px; }
.param-label-small { font-size: 12px; color: #909399; }

.message-bubble { display: flex; gap: 10px; margin-bottom: 16px; }
.message-bubble.user { flex-direction: row-reverse; }
.message-avatar { flex-shrink: 0; }
.message-content {
  max-width: 70%; padding: 10px 14px; border-radius: 8px;
  background: #fff; box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.markdown-body { line-height: 1.6; }
.markdown-body :deep(pre) {
  background: #f5f7fa; padding: 12px; border-radius: 6px; overflow-x: auto;
}
.markdown-body :deep(code) { font-family: Consolas, Monaco, monospace; font-size: 13px; }
.streaming-cursor { animation: blink 1s infinite; color: #409EFF; }
@keyframes blink { 50% { opacity: 0; } }
.thinking-indicator { display: flex; align-items: center; gap: 8px; padding: 8px 0; color: #909399; font-size: 13px; }
.tool-calls-block { padding: 8px 0; }
.tool-call-item { margin-bottom: 6px; display: flex; align-items: center; gap: 8px; }
.tool-output { font-size: 12px; color: #606266; }
</style>
