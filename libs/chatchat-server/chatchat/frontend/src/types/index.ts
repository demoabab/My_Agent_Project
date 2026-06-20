export interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

export interface ListResponse<T = unknown> {
  code: number
  msg: string
  data: T[]
}

export interface UserInfo {
  user_id: string
  username: string
  tenant_id: string | null
  is_superuser: boolean
}

export interface UserTenant {
  tenant_id: string
  tenant_name: string
  role: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
  user_id: string
  username: string
  tenants: UserTenant[]
}

export interface RegisterResponse {
  access_token: string
  token_type: string
  user_id: string
  username: string
  tenant_id: string
}

export interface MeResponse extends UserInfo {
  tenants: UserTenant[]
}

export interface TenantInfo {
  tenant_id: string
  name: string
  status: string
  create_time: string
}

export interface TenantMember {
  user_id: string
  username: string
  role: string
}

export interface KnowledgeBase {
  kb_name: string
  vs_type: string
  embed_model: string
  file_count: number
  create_time: string
}

export interface KnowledgeFile {
  file_name: string
  file_ext: string
  file_version: number
  file_size: number
  status: string
  create_time: string
}

export interface DocumentInfo {
  doc_id: string
  file_name: string
  status: string
}

export interface ToolCall {
  index: number
  id?: string
  type: string
  function: {
    name: string
    arguments: string | Record<string, unknown>
  }
  tool_output?: string | null
  is_error?: boolean
}

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp?: number
  message_id?: string
  is_ref?: boolean
  tool_calls?: ToolCall[]
  docs?: string[]
  status?: number
}

export interface ChatRequest {
  query: string
  knowledge_base_name?: string
  top_k?: number
  score_threshold?: number
  history?: ChatMessage[]
  stream?: boolean
  conversation_id?: string
  model?: string
  temperature?: number
  max_tokens?: number
  metadata?: Record<string, unknown>
}

export interface OpenAIChoice {
  delta?: { content?: string; tool_calls?: unknown[] }
  message?: { role: string; content: string; tool_calls?: unknown[] }
  finish_reason?: string | null
  index: number
}

export interface StreamChunk {
  id?: string
  object: string
  created: number
  model?: string
  choices: OpenAIChoice[]
  status?: number
  message_type?: number
  message_id?: string
  is_ref?: boolean
  docs?: string[]
  tool_calls?: ToolCall[]
}

export interface ToolInfo {
  name: string
  title: string
  description: string
  args: Record<string, unknown>
  config: Record<string, unknown>
}

export interface Conversation {
  conversation_id: string
  title: string
  chat_type: string
  create_time: string
  message_count?: number
}

export interface McpConnection {
  id: string
  server_name: string
  transport: string
  enabled: boolean
  description?: string
  create_time: string
}

export interface McpConnectionResponse {
  connections: McpConnection[]
  total: number
}

export interface McpProfile {
  timeout: number
  working_dir: string
  env_vars: Record<string, string>
  update_time: string
}

export interface ServerInfo {
  version: string
  status: string
}

export interface SearchDocResult {
  doc_id: string
  file_name: string
  content: string
  score: number
}
