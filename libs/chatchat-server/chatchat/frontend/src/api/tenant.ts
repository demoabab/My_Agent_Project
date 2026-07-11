import client from './client'
import type { UserTenant, TenantMember } from '@/types'

export function listTenants(): Promise<UserTenant[]> {
  return client.get('/api/v1/tenants').then((r) => r.data)
}

export function createTenant(name: string): Promise<{ tenant_id: string; name: string }> {
  const params = new URLSearchParams()
  params.append('name', name)
  return client.post('/api/v1/tenants', params).then((r) => r.data)
}

export function getMembers(tenantId: string): Promise<TenantMember[]> {
  return client.get(`/api/v1/tenants/${tenantId}/members`).then((r) => r.data)
}

export function addMember(
  tenantId: string,
  userId?: string,
  username?: string,
  role = 'member'
): Promise<{ message: string }> {
  const params = new URLSearchParams()
  if (userId) params.append('user_id', userId)
  if (username) params.append('username', username)
  params.append('role', role)
  return client.post(`/api/v1/tenants/${tenantId}/members`, params).then((r) => r.data)
}

export function removeMember(
  tenantId: string,
  userId: string
): Promise<{ message: string }> {
  return client.delete(`/api/v1/tenants/${tenantId}/members/${userId}`).then((r) => r.data)
}
