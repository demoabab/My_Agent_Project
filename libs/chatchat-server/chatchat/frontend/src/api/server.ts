import client from './client'
import type { ApiResponse, ServerInfo, ToolInfo } from '@/types'

export function getServerInfo(): Promise<ServerInfo> {
  return client.get('/server/info').then((r) => r.data)
}

export function getServerStatus(): Promise<ApiResponse> {
  return client.get('/server/health').then((r) => r.data)
}

export function getLlmModels(): Promise<ApiResponse<string[]>> {
  return client.get('/server/llm_models').then((r) => r.data)
}

export function getEmbeddingModels(): Promise<ApiResponse<string[]>> {
  return client.get('/server/embedding_models').then((r) => r.data)
}

export function listTools(): Promise<ApiResponse<Record<string, ToolInfo>>> {
  return client.get('/tools').then((r) => r.data)
}

