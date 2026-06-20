<template>
  <el-container class="app-layout">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="app-sidebar">
      <div class="sidebar-header">
        <span v-if="!sidebarCollapsed" class="logo-text">ChatChat</span>
        <span v-else class="logo-text-short">CC</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        router
        background-color="#304156"
        text-color="#bfcbd9"
        active-text-color="#409EFF"
      >
        <el-menu-item index="/chat">
          <el-icon><ChatDotRound /></el-icon>
          <span>知识库对话</span>
        </el-menu-item>
        <el-menu-item index="/llm-chat">
          <el-icon><ChatLineSquare /></el-icon>
          <span>LLM 对话</span>
        </el-menu-item>
        <el-menu-item index="/kb">
          <el-icon><FolderOpened /></el-icon>
          <span>知识库管理</span>
        </el-menu-item>
        <el-menu-item index="/tenants">
          <el-icon><OfficeBuilding /></el-icon>
          <span>租户管理</span>
        </el-menu-item>
        <el-menu-item v-if="auth.isSuperuser" index="/users">
          <el-icon><User /></el-icon>
          <span>用户管理</span>
        </el-menu-item>
        <el-menu-item index="/mcp">
          <el-icon><Connection /></el-icon>
          <span>MCP 配置</span>
        </el-menu-item>
        <el-menu-item index="/history">
          <el-icon><Clock /></el-icon>
          <span>对话历史</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-button
            :icon="sidebarCollapsed ? Expand : Fold"
            text
            @click="settings.toggleSidebar()"
          />
          <TenantSwitcher />
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <span class="user-info">
              <el-icon><UserFilled /></el-icon>
              {{ auth.user?.username || '用户' }}
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  {{ auth.user?.username }}
                </el-dropdown-item>
                <el-dropdown-item divided @click="auth.logout(); $router.push('/login')">
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { Expand, Fold } from '@element-plus/icons-vue'
import { useAuthStore } from '@/stores/auth'
import { useSettingsStore } from '@/stores/settings'
import TenantSwitcher from './TenantSwitcher.vue'

const route = useRoute()
const auth = useAuthStore()
const settings = useSettingsStore()

const sidebarCollapsed = computed(() => settings.sidebarCollapsed)
const activeMenu = computed(() => {
  const name = route.name
  if (name === 'KbDetail') return '/kb'
  if (name === 'TenantDetail') return '/tenants'
  return route.path
})
</script>

<style scoped>
.app-layout {
  height: 100vh;
}
.app-sidebar {
  background-color: #304156;
  overflow: hidden;
  transition: width 0.3s;
}
.sidebar-header {
  height: 60px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 20px;
  font-weight: bold;
}
.logo-text-short {
  font-size: 16px;
}
.app-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid #e6e6e6;
  padding: 0 16px;
}
.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}
.header-right {
  display: flex;
  align-items: center;
}
.user-info {
  display: flex;
  align-items: center;
  gap: 6px;
  cursor: pointer;
}
.app-main {
  background: #f5f7fa;
  padding: 16px;
  overflow: auto;
}
.el-menu {
  border-right: none;
}
</style>
