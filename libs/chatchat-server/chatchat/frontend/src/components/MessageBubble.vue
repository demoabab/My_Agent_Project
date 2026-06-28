<template>
  <div :class="['message-bubble', role]">
    <div class="message-avatar">
      <el-avatar v-if="role === 'user'" :size="34" icon="UserFilled" />
      <el-avatar v-else :size="34" icon="Cpu" style="background: linear-gradient(135deg, #409EFF, #6366f1)" />
    </div>
    <div class="message-body">
      <div v-if="isRef" class="ref-badge">
        <el-tag size="small" type="info" effect="plain">参考文档</el-tag>
      </div>

      <div v-if="docs && docs.length > 0" class="msg-docs">
        <el-collapse>
          <el-collapse-item title="参考文档 ({{ docs.length }})">
            <div v-for="(doc, i) in docs" :key="i" class="msg-doc-item" v-html="renderedDoc(doc)" />
          </el-collapse-item>
        </el-collapse>
      </div>

      <div v-if="thinking" class="msg-thinking">
        <el-collapse>
          <el-collapse-item title="思考过程">
            <div class="msg-thinking-content" v-html="renderedThinking" />
          </el-collapse-item>
        </el-collapse>
      </div>

      <div v-if="toolCalls && toolCalls.length > 0" class="msg-tool-calls">
        <div v-for="(tc, i) in toolCalls" :key="i" class="msg-tool-call-item">
          <el-tag type="warning" size="small" effect="plain">
            <el-icon :size="12"><Tools /></el-icon>
            {{ tc.function?.name }}
          </el-tag>
          <span v-if="tc.tool_output" class="msg-tool-output">{{ tc.tool_output.substring(0, 200) }}...</span>
        </div>
      </div>

      <div v-if="content" class="markdown-body" v-html="renderedContent" />
      <div v-if="timestamp" class="message-time">{{ formatTime(timestamp) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import { Tools } from '@element-plus/icons-vue'
import type { ToolCall } from '@/types'

const renderOptions = { breaks: true, gfm: true }

const props = defineProps<{
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
  isRef?: boolean
  docs?: string[]
  toolCalls?: ToolCall[]
  thinking?: string
}>()

const renderedContent = computed(() => {
  try {
    return marked(props.content, renderOptions) as string
  } catch {
    return props.content
  }
})

const renderedThinking = computed(() => {
  try {
    return marked(props.thinking || '', renderOptions) as string
  } catch {
    return props.thinking || ''
  }
})

function renderedDoc(doc: string): string {
  try { return marked(doc, renderOptions) as string } catch { return doc }
}

function formatTime(ts: number): string {
  return new Date(ts).toLocaleTimeString()
}
</script>

<style scoped>
.message-bubble {
  display: flex; gap: 10px; margin-bottom: 20px; align-items: flex-start;
}
.message-bubble.user { flex-direction: row-reverse; }
.message-avatar { flex-shrink: 0; padding-top: 2px; }

.message-body {
  max-width: 72%; padding: 12px 16px; border-radius: 10px;
  background: #fff; box-shadow: 0 1px 4px rgba(0,0,0,0.06);
}
.user .message-body {
  background: linear-gradient(135deg, #409EFF, #6366f1);
  color: #fff;
}

.ref-badge { margin-bottom: 6px; }

/* Markdown */
.markdown-body { line-height: 1.7; font-size: 14px; word-break: break-word; }
.markdown-body :deep(p) { margin: 0 0 8px; }
.markdown-body :deep(p:last-child) { margin-bottom: 0; }
.markdown-body :deep(pre) {
  background: #f5f7fa; padding: 12px; border-radius: 6px; overflow-x: auto;
  border: 1px solid #ebeef5;
}
.markdown-body :deep(code) {
  font-family: Consolas, Monaco, 'Courier New', monospace; font-size: 13px;
}
.user .message-body .markdown-body :deep(pre) {
  background: rgba(255,255,255,0.12); border-color: rgba(255,255,255,0.15);
}
.user .message-body .markdown-body :deep(code) { color: #fff; }

/* Timestamp */
.message-time {
  font-size: 11px; color: #c0c4cc; margin-top: 8px; text-align: right;
}
.user .message-time { color: rgba(255,255,255,0.6); }

/* Docs */
.msg-docs { margin-bottom: 8px; }
.msg-doc-item { font-size: 12px; color: #606266; padding: 4px 0; border-bottom: 1px solid #ebeef5; }
.msg-doc-item:last-child { border-bottom: none; }

/* Tool calls */
.msg-tool-calls { margin-bottom: 8px; }
.msg-tool-call-item { margin-bottom: 5px; display: flex; align-items: center; gap: 8px; }
.msg-tool-output { font-size: 12px; color: #606266; }

/* Thinking */
.msg-thinking { margin-bottom: 8px; }
.msg-thinking-content {
  font-size: 13px; color: #606266; line-height: 1.65;
}
.msg-thinking-content :deep(pre) {
  background: #f0f2f5; padding: 8px; border-radius: 4px; font-size: 12px;
}
</style>
