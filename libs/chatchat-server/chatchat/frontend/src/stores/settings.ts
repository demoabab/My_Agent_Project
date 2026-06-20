import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useSettingsStore = defineStore('settings', () => {
  const sidebarCollapsed = ref(false)
  const darkMode = ref(localStorage.getItem('darkMode') === 'true')

  function toggleSidebar() {
    sidebarCollapsed.value = !sidebarCollapsed.value
  }

  function toggleDarkMode() {
    darkMode.value = !darkMode.value
    localStorage.setItem('darkMode', String(darkMode.value))
  }

  return {
    sidebarCollapsed,
    darkMode,
    toggleSidebar,
    toggleDarkMode,
  }
})
