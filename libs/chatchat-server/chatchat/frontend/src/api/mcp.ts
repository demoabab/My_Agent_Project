import client from './client'
import type { McpConnection, McpConnectionResponse, McpProfile, ApiResponse } from '@/types'

export function listMcpConnections(): Promise<McpConnectionResponse> {
  return client.get('/mcp/connections').then((r) => r.data)
}

export function getMcpConnection(id: string): Promise<McpConnection> {
  return client.get(`/mcp/connections/${id}`).then((r) => r.data)
}

export function createMcpConnection(data: Record<string, unknown>): Promise<McpConnection> {
  return client.post('/mcp/connections', data).then((r) => r.data)
}

export function updateMcpConnection(id: string, data: Record<string, unknown>): Promise<McpConnection> {
  return client.put(`/mcp/connections/${id}`, data).then((r) => r.data)
}

export function deleteMcpConnection(id: string): Promise<ApiResponse> {
  return client.delete(`/mcp/connections/${id}`).then((r) => r.data)
}

export function testMcpConnection(id: string): Promise<{ success: boolean; message: string }> {
  return client.post(`/mcp/connections/${id}/test`).then((r) => r.data)
}

export function getMcpProfile(): Promise<McpProfile> {
  return client.get('/mcp/profile').then((r) => r.data)
}

export function updateMcpProfile(data: Partial<McpProfile>): Promise<McpProfile> {
  return client.put('/mcp/profile', data).then((r) => r.data)
}
