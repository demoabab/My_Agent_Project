import type { StreamChunk } from '@/types'

export function parseSSELine(line: string): StreamChunk | null {
  const trimmed = line.trim()
  if (!trimmed || !trimmed.startsWith('data: ')) return null
  const data = trimmed.slice(6)
  if (data === '[DONE]') return null
  try {
    return JSON.parse(data) as StreamChunk
  } catch {
    return null
  }
}

export async function* sseIterator(response: Response): AsyncGenerator<StreamChunk> {
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
      const chunk = parseSSELine(line)
      if (chunk) yield chunk
    }
  }

  // flush remaining buffer
  for (const line of buffer.split('\n')) {
    const chunk = parseSSELine(line)
    if (chunk) yield chunk
  }
}
