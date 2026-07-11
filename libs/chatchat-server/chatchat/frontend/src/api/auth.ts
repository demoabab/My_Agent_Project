import client from './client'
import type { LoginResponse, RegisterResponse, MeResponse } from '@/types'

export function login(username: string, password: string): Promise<LoginResponse> {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  return client.post('/api/v1/auth/login', params).then((r) => r.data)
}

export function register(
  username: string,
  password: string,
  email = '',
  full_name = ''
): Promise<RegisterResponse> {
  const params = new URLSearchParams()
  params.append('username', username)
  params.append('password', password)
  params.append('email', email)
  params.append('full_name', full_name)
  return client.post('/api/v1/auth/register', params).then((r) => r.data)
}

export function getMe(): Promise<MeResponse> {
  return client.get('/api/v1/auth/me').then((r) => r.data)
}

export function switchTenant(tenantId: string): Promise<LoginResponse> {
  const params = new URLSearchParams()
  params.append('tenant_id', tenantId)
  return client.post('/api/v1/auth/switch-tenant', params).then((r) => r.data)
}
