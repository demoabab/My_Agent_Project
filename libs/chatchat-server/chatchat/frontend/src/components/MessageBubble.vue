<template>
  <div :class="['message-bubble', role]">
    <div class="message-avatar">
      <el-avatar v-if="role === 'user'" :size="32" icon="UserFilled" />
      <el-avatar v-else :size="32" icon="Cpu" style="background: #409EFF" />
    </div>
    <div class="message-content">
      <div v-if="isRef" class="ref-badge">
        <el-tag size="small" type="info">参考文档</el-tag>
      </div>
      <!-- Reference docs in saved messages -->
      <div v-if="docs && docs.length > 0" class="msg-docs">
        <el-collapse>
          <el-collapse-item title="参考文档 ({{ docs.length }})">
            <div v-for="(doc, i) in docs" :key="i" class="msg-doc-item" v-html="renderedDoc(doc)" />
          </el-collapse-item>
        </el-collapse>
      </div>
      <!-- Tool calls in saved messages -->
      <div v-if="toolCalls && toolCalls.length > 0" class="msg-tool-calls">
        <div v-for="(tc, i) in toolCalls" :key="i" class="msg-tool-call-item">
          <el-tag type="warning" size="small">工具: {{ tc.function?.name }}</el-tag>
          <span v-if="tc.tool_output" class="msg-tool-output">{{ tc.tool_output.substring(0, 200) }}...</span>
        </div>
      </div>
      <div class="markdown-body" v-html="renderedContent" />
      <div v-if="timestamp" class="message-time">{{ formatTime(timestamp) }}</div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { marked } from 'marked'
import type { ToolCall } from '@/types'

const renderOptions = { breaks: true, gfm: true }

const props = defineProps<{
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
  isRef?: boolean
  docs?: string[]
  toolCalls?: ToolCall[]
}>()

const renderedContent = computed(() => {
  try {
    return marked(props.content, renderOptions) as string
  } catch {
    return props.content
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
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}
.message-bubble.user {
  flex-direction: row-reverse;
}
.message-avatar {
  flex-shrink: 0;
}
.message-content {
  max-width: 70%;
  padding: 10px 14px;
  border-radius: 8px;
  background: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.08);
}
.user .message-content {
  background: #409EFF;
  color: #fff;
}
.ref-badge {
  margin-bottom: 4px;
}
.markdown-body {
  line-height: 1.6;
  word-break: break-word;
}
.markdown-body :deep(pre) {
  background: #f5f7fa;
  padding: 12px;
  border-radius: 6px;
  overflow-x: auto;
}
.markdown-body :deep(code) {
  font-family: Consolas, Monaco, monospace;
  font-size: 13px;
}
.user .markdown-body :deep(pre) {
  background: rgba(255,255,255,0.15);
}
.message-time {
  font-size: 11px;
  color: #999;
  margin-top: 4px;
}
.user .message-time {
  color: rgba(255,255,255,0.7);
}
.msg-docs { margin-bottom: 8px; }
.msg-doc-item { font-size: 12px; color: #606266; padding: 4px 0; border-bottom: 1px solid #ebeef5; }
.msg-tool-calls { margin-bottom: 8px; }
.msg-tool-call-item { margin-bottom: 4px; display: flex; align-items: center; gap: 8px; }
.msg-tool-output { font-size: 12px; color: #606266; }
</style>
