import { ref, nextTick, computed } from 'vue'
import { chatKb, chatLlm, chatFile } from '@/api/chat'
import type { ChatMessage, StreamChunk, ToolCall } from '@/types'

function genId(): string {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 10)
}

export function useChat() {
  const messages = ref<ChatMessage[]>([])
  const streamingContent = ref('')
  const thinkingContent = ref('')  // Agent intermediate reasoning (collapsible)
  const streamDocs = ref<string[]>([])
  const streamToolCalls = ref<ToolCall[]>([])
  const streamStatus = ref(-1)
  const isStreaming = ref(false)
  const abortController = ref<AbortController | null>(null)
  const chatContainer = ref<HTMLElement | null>(null)
  const error = ref('')
  const conversationId = ref(localStorage.getItem('current_conv_id') || '')
  const currentMode = ref<'kb' | 'llm'>('kb')
  let lastToolCallIdx = 0  // Track when tool calls happen for thinking/answer separation

  const currentThinking = computed(() => {
    switch (streamStatus.value) {
      case 0: return '初始化...'
      case 1: return '思考中...'
      case 2: return '生成中...'
      case 4: return '调用工具...'
      case 7: return '执行工具...'
      case 8: return '工具完成'
      default: return ''
    }
  })

  function scrollToBottom() {
    nextTick(() => {
      if (chatContainer.value) {
        chatContainer.value.scrollTop = chatContainer.value.scrollHeight
      }
    })
  }

  function addMessage(role: 'user' | 'assistant' | 'system', content: string, extra?: Partial<ChatMessage>) {
    messages.value.push({ role, content, timestamp: Date.now(), ...extra })
    scrollToBottom()
  }

  function handleChunk(chunk: StreamChunk) {
    streamStatus.value = chunk.status ?? -1

    // Capture reference documents (KB chat first chunk)
    if (chunk.docs && chunk.docs.length > 0) {
      streamDocs.value = chunk.docs
    }

    // When new tool calls appear, move current answer text to thinking
    const hasNewToolCalls = (chunk.choices?.[0]?.delta?.tool_calls?.length || chunk.tool_calls?.length || 0) > 0
    const isToolStart = chunk.status === 4 || chunk.status === 7
    if ((hasNewToolCalls || isToolStart) && streamingContent.value) {
      if (thinkingContent.value) thinkingContent.value += '\n\n'
      thinkingContent.value += streamingContent.value
      streamingContent.value = ''
    }

    // Capture tool calls from choices
    if (chunk.choices?.[0]?.delta?.tool_calls?.length) {
      for (const tc of chunk.choices[0].delta.tool_calls as unknown as ToolCall[]) {
        const existing = streamToolCalls.value.find(
          (x) => x.id && tc.id && x.id === tc.id
        )
        if (existing) {
          Object.assign(existing, tc)
        } else {
          streamToolCalls.value.push(tc)
        }
      }
    }

    // Also check top-level tool_calls
    if (chunk.tool_calls?.length) {
      for (const tc of chunk.tool_calls) {
        const existing = streamToolCalls.value.find(
          (x) => x.id && tc.id && x.id === tc.id
        )
        if (existing) {
          Object.assign(existing, tc)
        } else {
          streamToolCalls.value.push(tc)
        }
      }
    }

    // Streaming text content (with dedup: skip if new text is already contained)
    const text = chunk.choices?.[0]?.delta?.content || ''
    if (text) {
      const combined = streamingContent.value + text
      // Check if the new text would create a repetition pattern
      if (!isRepeating(streamingContent.value, text)) {
        streamingContent.value = combined
      }
    }

    scrollToBottom()
  }

  // Detect if appending `addition` to `base` creates repetition
  function isRepeating(base: string, addition: string): boolean {
    if (!addition || base.length === 0) return false
    // If addition content is already fully contained in base, skip
    if (base.includes(addition)) return true
    // Check for sentence-level repetition: last N chars of base vs first N chars of addition
    const checkLen = Math.min(addition.length, 100)
    if (checkLen < 20) return false
    const tail = base.slice(-checkLen)
    const head = addition.slice(0, checkLen)
    return tail === head
  }

  function finishStream() {
    // If there's thinking content and no streaming content, promote thinking to answer
    const answer = streamingContent.value || thinkingContent.value
    const thinking = thinkingContent.value && streamingContent.value ? thinkingContent.value : ''

    const finalMsg: ChatMessage = {
      role: 'assistant',
      content: answer,
      timestamp: Date.now(),
      is_ref: false,
    }

    if (thinking) {
      finalMsg.thinking = thinking
    }
    if (streamDocs.value.length > 0) {
      finalMsg.docs = [...streamDocs.value]
    }
    if (streamToolCalls.value.length > 0) {
      finalMsg.tool_calls = [...streamToolCalls.value]
    }
    finalMsg.status = streamStatus.value

    if (finalMsg.content || finalMsg.tool_calls?.length || finalMsg.thinking) {
      messages.value.push(finalMsg)
    }

    streamingContent.value = ''
    thinkingContent.value = ''
    streamDocs.value = []
    streamToolCalls.value = []
    streamStatus.value = -1
    isStreaming.value = false
    abortController.value = null
    scrollToBottom()
    saveLocalHistory()
    persistSession()
  }

  function ensureConversation() {
    if (!conversationId.value) {
      conversationId.value = genId()
      localStorage.setItem('current_conv_id', conversationId.value)
    }
    return conversationId.value
  }

  function newConversation() {
    conversationId.value = genId()
    localStorage.setItem('current_conv_id', conversationId.value)
    messages.value = []
    thinkingContent.value = ''
    persistSession()
  }

  function saveLocalHistory() {
    if (messages.value.length < 2) return
    try {
      const raw = localStorage.getItem('chat_history')
      const list = raw ? JSON.parse(raw) : []
      const lastUser = [...messages.value].reverse().find((m) => m.role === 'user')
      const title = lastUser?.content?.substring(0, 50) || '对话'
      // Replace existing entry with same conversation_id
      const existingIdx = list.findIndex((x: { id: string }) => x.id === conversationId.value)
      const entry = {
        id: conversationId.value,
        title,
        mode: currentMode.value,
        time: new Date().toLocaleString(),
        preview: lastUser?.content?.substring(0, 100) || '',
        messages: messages.value.map((m) => ({ ...m })),
      }
      if (existingIdx >= 0) {
        list[existingIdx] = entry
      } else {
        list.push(entry)
      }
      if (list.length > 50) list.splice(0, list.length - 50)
      localStorage.setItem('chat_history', JSON.stringify(list))
    } catch { /* ignore */ }
  }

  // Session persistence (survive page navigation)
  function persistSession() {
    try {
      const session = {
        messages: messages.value.map((m) => ({ ...m })),
        conversationId: conversationId.value,
        mode: currentMode.value,
      }
      localStorage.setItem('current_chat_session', JSON.stringify(session))
    } catch { /* ignore */ }
  }

  function restoreSession(mode: 'kb' | 'llm'): boolean {
    try {
      // Check for "continue from history" first
      const continueData = localStorage.getItem('continue_conversation')
      if (continueData) {
        const data = JSON.parse(continueData)
        if (data.mode === mode) {
          messages.value = data.messages || []
          conversationId.value = data.conversation_id || data.id || ''
          localStorage.removeItem('continue_conversation')
          localStorage.setItem('current_conv_id', conversationId.value)
          return true
        }
      }
      // Restore current session for this mode
      const raw = localStorage.getItem('current_chat_session')
      if (raw) {
        const session = JSON.parse(raw)
        if (session.mode === mode && session.messages?.length > 0) {
          messages.value = session.messages
          conversationId.value = session.conversationId || ''
          localStorage.setItem('current_conv_id', conversationId.value)
          return true
        }
      }
    } catch { /* ignore */ }
    return false
  }

  async function sendKbQuery(
    query: string,
    kbName?: string,
    mode: 'local_kb' | 'temp_kb' | 'search_engine' = 'local_kb'
  ) {
    error.value = ''
    currentMode.value = 'kb'
    const convId = ensureConversation()
    addMessage('user', query)

    isStreaming.value = true
    streamingContent.value = ''
    thinkingContent.value = ''
    streamDocs.value = []
    streamToolCalls.value = []
    streamStatus.value = -1
    abortController.value = new AbortController()

    try {
      await chatKb(
        {
          query,
          mode,
          knowledge_base_name: kbName || 'default',
          history: messages.value.slice(0, -1),
          conversation_id: convId,
        },
        handleChunk,
        abortController.value.signal
      )
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        if (streamingContent.value) {
          addMessage('assistant', streamingContent.value, { docs: [...streamDocs.value] })
        }
      } else {
        error.value = err instanceof Error ? err.message : '请求失败'
      }
    } finally {
      finishStream()
    }
  }

  async function sendLlmQuery(
    query: string,
    tools?: string[],
    model?: string,
    useMcp?: boolean
  ) {
    error.value = ''
    currentMode.value = 'llm'
    const convId = ensureConversation()
    addMessage('user', query)

    isStreaming.value = true
    streamingContent.value = ''
    thinkingContent.value = ''
    streamDocs.value = []
    streamToolCalls.value = []
    streamStatus.value = -1
    abortController.value = new AbortController()

    try {
      await chatLlm(
        {
          query,
          messages: messages.value.map((m) => ({ role: m.role, content: m.content })),
          model,
          tools: tools?.length ? tools : undefined,
          conversation_id: convId,
          stream: true,
          use_mcp: useMcp,
        },
        handleChunk,
        abortController.value.signal
      )
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        if (streamingContent.value) {
          addMessage('assistant', streamingContent.value, { tool_calls: [...streamToolCalls.value] })
        }
      } else {
        error.value = err instanceof Error ? err.message : '请求失败'
      }
    } finally {
      finishStream()
    }
  }

  async function sendFileQuery(files: File[], query: string) {
    error.value = ''
    currentMode.value = 'kb'
    addMessage('user', query)

    isStreaming.value = true
    streamingContent.value = ''
    thinkingContent.value = ''
    streamDocs.value = []
    streamToolCalls.value = []
    streamStatus.value = -1
    abortController.value = new AbortController()

    try {
      await chatFile(files, query, handleChunk, abortController.value.signal)
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        if (streamingContent.value) addMessage('assistant', streamingContent.value)
      } else {
        error.value = err instanceof Error ? err.message : '请求失败'
      }
    } finally {
      finishStream()
    }
  }

  function stopStreaming() {
    abortController.value?.abort()
  }

  function clearMessages() {
    messages.value = []
    streamingContent.value = ''
    thinkingContent.value = ''
    streamDocs.value = []
    streamToolCalls.value = []
    streamStatus.value = -1
    error.value = ''
    isStreaming.value = false
    persistSession()
  }

  return {
    messages,
    streamingContent,
    thinkingContent,
    streamDocs,
    streamToolCalls,
    streamStatus,
    currentThinking,
    isStreaming,
    error,
    conversationId,
    chatContainer,
    sendKbQuery,
    sendLlmQuery,
    sendFileQuery,
    stopStreaming,
    clearMessages,
    newConversation,
    ensureConversation,
    persistSession,
    restoreSession,
  }
}
