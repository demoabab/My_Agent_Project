<template>
  <div class="kb-file-tree">
    <el-input
      v-model="searchText"
      placeholder="搜索文件..."
      size="small"
      clearable
      style="margin-bottom: 8px"
    />
    <el-tree
      :data="treeData"
      node-key="id"
      :props="treeProps"
      :filter-node-method="filterNode"
      :expand-on-click-node="false"
      highlight-current
      ref="treeRef"
    >
      <template #default="{ node, data }">
        <span class="tree-node">
          <el-icon v-if="data.isFolder" color="#409EFF"><Folder /></el-icon>
          <el-icon v-else color="#67C23A"><Document /></el-icon>
          <span style="margin-left: 6px">{{ node.label }}</span>
          <el-button
            v-if="!data.isFolder"
            link
            size="small"
            type="danger"
            @click.stop="$emit('delete', data.fileName)"
          >
            <el-icon><Delete /></el-icon>
          </el-button>
        </span>
      </template>
    </el-tree>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type { KnowledgeFile } from '@/types'

interface TreeNode {
  id: string
  label: string
  isFolder: boolean
  fileName?: string
  children?: TreeNode[]
}

const props = defineProps<{
  files: KnowledgeFile[]
}>()

defineEmits<{
  delete: [fileName: string]
}>()

const searchText = ref('')
const treeRef = ref()

const treeProps = { children: 'children', label: 'label' }

const treeData = computed(() => {
  const folderMap = new Map<string, TreeNode>()
  const roots: TreeNode[] = []

  for (const f of props.files) {
    const parts = f.file_name.replace(/\\/g, '/').split('/')
    let parent: TreeNode | null = null
    let parentPath = ''

    for (let i = 0; i < parts.length; i++) {
      const isFolder = i < parts.length - 1
      const fullPath = parts.slice(0, i + 1).join('/')

      if (folderMap.has(fullPath)) {
        parent = folderMap.get(fullPath)!
        continue
      }

      const node: TreeNode = {
        id: fullPath,
        label: parts[i],
        isFolder: isFolder || false,
        fileName: isFolder ? undefined : f.file_name,
        children: isFolder ? [] : undefined,
      }

      folderMap.set(fullPath, node)

      if (parent && parent.children) {
        parent.children.push(node)
      } else if (!parent) {
        roots.push(node)
      }

      if (isFolder) {
        parent = node
      }
    }
  }

  return roots
})

watch(searchText, (v) => {
  treeRef.value?.filter(v)
})

function filterNode(value: string, data: TreeNode): boolean {
  if (!value) return true
  return data.label.toLowerCase().includes(value.toLowerCase())
}
</script>

<style scoped>
.tree-node {
  display: flex;
  align-items: center;
  width: 100%;
  font-size: 13px;
}
</style>
