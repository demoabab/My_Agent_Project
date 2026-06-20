import client from './client'
import type { ApiResponse, ListResponse, KnowledgeBase, KnowledgeFile, SearchDocResult } from '@/types'

export function listKbs(): Promise<ListResponse<KnowledgeBase>> {
  return client.get('/knowledge_base/list_knowledge_bases').then((r) => r.data)
}

export function createKb(params: {
  knowledge_base_name: string
  vector_store_type?: string
  embed_model?: string
}): Promise<ApiResponse> {
  const form = new URLSearchParams()
  form.append('knowledge_base_name', params.knowledge_base_name)
  if (params.vector_store_type) form.append('vector_store_type', params.vector_store_type)
  if (params.embed_model) form.append('embed_model', params.embed_model)
  return client.post('/knowledge_base/create_knowledge_base', form).then((r) => r.data)
}

export function deleteKb(kbName: string): Promise<ApiResponse> {
  const form = new URLSearchParams()
  form.append('knowledge_base_name', kbName)
  return client.post('/knowledge_base/delete_knowledge_base', form).then((r) => r.data)
}

export function listFiles(kbName: string): Promise<ListResponse<KnowledgeFile>> {
  return client.get('/knowledge_base/list_files', { params: { knowledge_base_name: kbName } }).then((r) => r.data)
}

export function uploadDocs(kbName: string, files: File[], override = false): Promise<ApiResponse> {
  const form = new FormData()
  form.append('knowledge_base_name', kbName)
  form.append('override', String(override))
  for (const file of files) {
    form.append('files', file)
  }
  return client.post('/knowledge_base/upload_docs', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }).then((r) => r.data)
}

export function deleteDocs(kbName: string, docIds: string[]): Promise<ApiResponse> {
  const form = new URLSearchParams()
  form.append('knowledge_base_name', kbName)
  for (const id of docIds) {
    form.append('doc_ids', id)
  }
  return client.post('/knowledge_base/delete_docs', form).then((r) => r.data)
}

export function updateDocs(kbName: string, files: File[]): Promise<ApiResponse> {
  const form = new FormData()
  form.append('knowledge_base_name', kbName)
  for (const file of files) {
    form.append('files', file)
  }
  return client.post('/knowledge_base/update_docs', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 120000,
  }).then((r) => r.data)
}

export function searchDocs(
  kbName: string,
  query: string,
  topK = 3,
  scoreThreshold = 0.5
): Promise<ListResponse<SearchDocResult>> {
  const form = new URLSearchParams()
  form.append('knowledge_base_name', kbName)
  form.append('query', query)
  form.append('top_k', String(topK))
  form.append('score_threshold', String(scoreThreshold))
  return client.post('/knowledge_base/search_docs', form).then((r) => r.data)
}

export function recreateVectorStore(kbName: string): Promise<ApiResponse> {
  const params = new URLSearchParams()
  params.append('knowledge_base_name', kbName)
  return client.post('/knowledge_base/recreate_vector_store', params).then((r) => r.data)
}

export function downloadDoc(kbName: string, fileName: string): Promise<Blob> {
  return client.get('/knowledge_base/download_doc', {
    params: { knowledge_base_name: kbName, file_name: fileName },
    responseType: 'blob',
  }).then((r) => r.data)
}
