<template>
  <el-container class="app-layout">
    <el-aside :width="sidebarCollapsed ? '64px' : '220px'" class="app-sidebar">
      <div class="sidebar-header">
        <div class="logo-icon">CC</div>
        <span v-show="!sidebarCollapsed" class="logo-text">ChatChat</span>
      </div>
      <el-menu
        :default-active="activeMenu"
        :collapse="sidebarCollapsed"
        router
        background-color="#1d1e2c"
        text-color="#a6a9b6"
        active-text-color="#fff"
        class="side-menu"
      >
        <el-menu-item index="/chat">
          <template #title>
            <el-icon><ChatDotRound /></el-icon>
            <span>知识库对话</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/llm-chat">
          <template #title>
            <el-icon><ChatLineSquare /></el-icon>
            <span>LLM 对话</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/kb">
          <template #title>
            <el-icon><FolderOpened /></el-icon>
            <span>知识库管理</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/tenants">
          <template #title>
            <el-icon><OfficeBuilding /></el-icon>
            <span>租户管理</span>
          </template>
        </el-menu-item>
        <el-menu-item v-if="auth.isSuperuser" index="/users">
          <template #title>
            <el-icon><User /></el-icon>
            <span>用户管理</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/mcp">
          <template #title>
            <el-icon><Connection /></el-icon>
            <span>MCP 配置</span>
          </template>
        </el-menu-item>
        <el-menu-item index="/history">
          <template #title>
            <el-icon><Clock /></el-icon>
            <span>对话历史</span>
          </template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container>
      <el-header class="app-header">
        <div class="header-left">
          <el-button
            :icon="sidebarCollapsed ? Expand : Fold"
            text
            class="collapse-btn"
            @click="settings.toggleSidebar()"
          />
          <TenantSwitcher />
        </div>
        <div class="header-right">
          <el-dropdown trigger="click">
            <div class="user-badge">
              <el-avatar :size="28" icon="UserFilled" />
              <span class="user-name">{{ auth.user?.username || '用户' }}</span>
              <el-icon class="arrow-icon"><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item disabled>
                  <div class="dropdown-user-info">
                    <el-avatar :size="32" icon="UserFilled" />
                    <div>
                      <div class="dropdown-username">{{ auth.user?.username }}</div>
                      <div class="dropdown-role">{{ auth.isSuperuser ? '超级管理员' : '用户' }}</div>
                    </div>
                  </div>
                </el-dropdown-item>
                <el-dropdown-item divided @click="auth.logout(); $router.push('/login')">
                  <el-icon><SwitchButton /></el-icon>
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
import { Expand, Fold, SwitchButton, ArrowDown } from '@element-plus/icons-vue'
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
.app-layout { height: 100vh; }

/* ---- Sidebar ---- */
.app-sidebar {
  background-color: #1d1e2c;
  overflow: hidden;
  transition: width 0.25s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex; flex-direction: column;
}
.sidebar-header {
  height: 60px; display: flex; align-items: center; gap: 10px;
  padding: 0 18px; border-bottom: 1px solid rgba(255,255,255,0.06);
  flex-shrink: 0;
}
.logo-icon {
  width: 32px; height: 32px; border-radius: 8px;
  background: linear-gradient(135deg, #409EFF, #6366f1);
  color: #fff; font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.logo-text {
  font-size: 17px; font-weight: 700; color: #fff; white-space: nowrap;
  letter-spacing: 0.5px;
}

.side-menu { border-right: none; flex: 1; overflow-y: auto; }
.side-menu .el-menu-item {
  margin: 2px 8px; border-radius: 6px; height: 42px; line-height: 42px;
  transition: all 0.15s;
}
.side-menu .el-menu-item:hover { background: rgba(255,255,255,0.06); }
.side-menu .el-menu-item.is-active {
  background: linear-gradient(135deg, #409EFF, #6366f1) !important;
  color: #fff !important;
}

/* ---- Header ---- */
.app-header {
  display: flex; align-items: center; justify-content: space-between;
  background: #fff; border-bottom: 1px solid #ebeef5;
  padding: 0 20px; height: 52px;
  box-shadow: 0 1px 4px rgba(0,0,0,0.04);
  z-index: 1;
}
.header-left { display: flex; align-items: center; gap: 12px; }
.collapse-btn { color: #606266; font-size: 18px; }
.header-right { display: flex; align-items: center; }

.user-badge {
  display: flex; align-items: center; gap: 8px;
  padding: 4px 10px 4px 4px; border-radius: 20px;
  cursor: pointer; transition: background 0.15s;
}
.user-badge:hover { background: #f5f7fa; }
.user-name { font-size: 13px; color: #303133; }
.arrow-icon { font-size: 12px; color: #909399; transition: transform 0.2s; }

.dropdown-user-info {
  display: flex; align-items: center; gap: 10px; padding: 4px 0;
}
.dropdown-username { font-size: 14px; font-weight: 600; color: #303133; }
.dropdown-role { font-size: 12px; color: #909399; margin-top: 2px; }

/* ---- Main ---- */
.app-main {
  background: #f0f2f5; padding: 16px; overflow: auto;
}
</style>
