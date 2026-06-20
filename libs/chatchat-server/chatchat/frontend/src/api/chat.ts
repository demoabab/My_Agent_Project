import type { ChatMessage, StreamChunk } from '@/types'

export interface KbChatParams {
  query: string
  mode: 'local_kb' | 'temp_kb' | 'search_engine'
  knowledge_base_name?: string
  top_k?: number
  score_threshold?: number
  history?: ChatMessage[]
  stream?: boolean
  conversation_id?: string
  model?: string
  temperature?: number
  max_tokens?: number
}

export interface LlmChatParams {
  query: string
  messages?: ChatMessage[]
  stream?: boolean
  conversation_id?: string
  model?: string
  temperature?: number
  max_tokens?: number
  tools?: string[]
  use_mcp?: boolean
  metadata?: Record<string, unknown>
}

export async function chatKb(
  params: KbChatParams,
  onChunk: (chunk: StreamChunk) => void,
  abortSignal?: AbortSignal
): Promise<void> {
  const mode = params.mode || 'local_kb'
  const param = params.knowledge_base_name || 'default'
  const body: Record<string, unknown> = {
    messages: [
      ...(params.history || []).map((m) => ({ role: m.role, content: m.content })),
      { role: 'user', content: params.query },
    ],
    stream: params.stream !== false,
  }
  if (params.model) body.model = params.model
  if (params.temperature !== undefined) body.temperature = params.temperature
  if (params.max_tokens !== undefined) body.max_tokens = params.max_tokens
  body.extra_body = {
    knowledge_base_name: params.knowledge_base_name,
    top_k: params.top_k || 3,
    score_threshold: params.score_threshold || 0.5,
    conversation_id: params.conversation_id || '',
  }

  const response = await fetch(`/knowledge_base/${mode}/${param}/chat/completions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
    body: JSON.stringify(body),
    signal: abortSignal,
  })

  const reader = response.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('data: ')) {
        const data = trimmed.slice(6)
        if (data === '[DONE]') return
        try {
          const chunk: StreamChunk = JSON.parse(data)
          onChunk(chunk)
        } catch {
          // skip invalid JSON
        }
      }
    }
  }
}

export async function chatLlm(
  params: LlmChatParams,
  onChunk: (chunk: StreamChunk) => void,
  abortSignal?: AbortSignal
): Promise<void> {
  const messages = params.messages || [{ role: 'user' as const, content: params.query }]

  const body: Record<string, unknown> = {
    messages,
    stream: params.stream !== false,
  }
  if (params.model) body.model = params.model
  if (params.temperature !== undefined) body.temperature = params.temperature
  if (params.max_tokens !== undefined) body.max_tokens = params.max_tokens
  if (params.tools?.length) {
    body.tools = params.tools
  }
  const extra_body: Record<string, unknown> = {}
  if (params.conversation_id) extra_body.conversation_id = params.conversation_id
  if (params.use_mcp) extra_body.use_mcp = true
  if (params.metadata) extra_body.metadata = params.metadata
  body.extra_body = extra_body

  const response = await fetch('/chat/chat/completions', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
    body: JSON.stringify(body),
    signal: abortSignal,
  })

  const reader = response.body?.getReader()
  if (!reader) return

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''
    for (const line of lines) {
      const trimmed = line.trim()
      if (trimmed.startsWith('data: ')) {
        const data = trimmed.slice(6)
        if (data === '[DONE]') return
        try {
          const chunk: StreamChunk = JSON.parse(data)
          onChunk(chunk)
        } catch {
          // skip invalid JSON
        }
      }
    }
  }
}

export function chatFeedback(messageId: string, rating: number): Promise<unknown> {
  return fetch('/chat/feedback', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${localStorage.getItem('token')}` },
    body: JSON.stringify({ message_id: messageId, rating }),
  }).then((r) => r.json())
}

export function chatFile(
  files: File[],
  query: string,
  onChunk: (chunk: StreamChunk) => void,
  abortSignal?: AbortSignal
): Promise<void> {
  const form = new FormData()
  for (const file of files) {
    form.append('files', file)
  }
  form.append('query', query)

  return fetch('/chat/file_chat', {
    method: 'POST',
    headers: { Authorization: `Bearer ${localStorage.getItem('token')}` },
    body: form,
    signal: abortSignal,
  }).then(async (response) => {
    const reader = response.body?.getReader()
    if (!reader) return

    const decoder = new TextDecoder()
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() || ''
      for (const line of lines) {
        const trimmed = line.trim()
        if (trimmed.startsWith('data: ')) {
          const data = trimmed.slice(6)
          if (data === '[DONE]') return
          try {
            const chunk: StreamChunk = JSON.parse(data)
            onChunk(chunk)
          } catch {
            // skip invalid JSON
          }
        }
      }
    }
  })
}
