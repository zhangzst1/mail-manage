<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container">
      <div class="pointer-events-none absolute inset-0 overflow-hidden">
        <div class="floating-orb -left-20 top-20 h-56 w-56 bg-cyan-300/35"></div>
        <div class="floating-orb right-0 top-0 h-72 w-72 bg-emerald-300/25"></div>
        <div class="floating-orb bottom-16 left-1/3 h-64 w-64 bg-sky-400/15"></div>
      </div>

      <el-container class="app-shell">
        <el-header class="app-header">
          <div class="app-header-inner">
            <div class="shell-panel app-header-panel" :class="{ 'is-scrolled': isScrolled }">
              <div class="header-left">
                <router-link to="/" class="logo-link">
                  <div class="logo-mark">FM</div>
                  <div class="logo-copy">
                    <span class="logo-kicker">Mail Control Center</span>
                    <h1>花火邮箱助手</h1>
                  </div>
                </router-link>

                <div class="status-pill lg-only">
                  <span class="status-dot" :class="{ online: websocketConnected }"></span>
                  <span>{{ websocketConnected ? '实时连接正常' : '等待连接服务器' }}</span>
                </div>
              </div>

              <div class="header-right">
                <template v-if="!isAuthenticated">
                  <router-link to="/login">
                    <el-button class="shell-button shell-button-secondary">登录</el-button>
                  </router-link>
                  <router-link to="/register">
                    <el-button class="shell-button shell-button-primary">注册</el-button>
                  </router-link>
                </template>

                <template v-else>
                  <el-dropdown @command="handleUserCommand">
                    <span class="user-dropdown-link">
                      <span class="user-avatar">{{ userInitial }}</span>
                      <span class="user-name">{{ currentUser ? currentUser.username : '用户' }}</span>
                      <el-icon><ArrowDown /></el-icon>
                    </span>
                    <template #dropdown>
                      <el-dropdown-menu>
                        <el-dropdown-item command="account">账户设置</el-dropdown-item>
                        <el-dropdown-item v-if="isAdmin" command="admin">用户管理</el-dropdown-item>
                        <el-dropdown-item divided command="logout">退出登录</el-dropdown-item>
                      </el-dropdown-menu>
                    </template>
                  </el-dropdown>
                </template>

                <div class="connection-status">
                  <el-tag :type="websocketConnected ? 'success' : 'danger'" effect="dark" round>
                    {{ websocketConnected ? '在线' : '离线' }}
                  </el-tag>
                </div>
              </div>
            </div>

            <div v-if="isAuthenticated" class="shell-panel nav-panel">
              <el-menu
                mode="horizontal"
                :router="true"
                :default-active="$route.path"
                class="app-nav"
              >
                <el-menu-item index="/">
                  <el-icon><HomeFilled /></el-icon>
                  <span>首页</span>
                </el-menu-item>
                <el-menu-item index="/emails">
                  <el-icon><Message /></el-icon>
                  <span>邮箱管理</span>
                </el-menu-item>
                <el-menu-item index="/search">
                  <el-icon><Search /></el-icon>
                  <span>邮件搜索</span>
                </el-menu-item>
                <el-menu-item v-if="isAdmin" index="/admin/users">
                  <el-icon><UserFilled /></el-icon>
                  <span>用户管理</span>
                </el-menu-item>
                <el-menu-item index="/about">
                  <el-icon><InfoFilled /></el-icon>
                  <span>关于</span>
                </el-menu-item>
              </el-menu>
            </div>
          </div>
        </el-header>

        <el-main class="app-main">
          <div class="app-main-inner">
            <router-view v-slot="{ Component }" v-if="!initializing">
              <transition name="fade" mode="out-in">
                <component :is="Component" />
              </transition>
            </router-view>
            <div v-else class="loading-container page-shell rounded-[28px] p-6 sm:p-8">
              <el-skeleton :rows="7" animated />
            </div>
          </div>
        </el-main>

        <el-footer class="app-footer">
          <div class="shell-panel footer-panel">
            <p>花火邮箱助手</p>
            <span>更清爽的邮箱管理体验</span>
          </div>
        </el-footer>
      </el-container>

      <Notifications />

      <div v-if="showDebugTools" class="debug-tools-container">
        <DebugTools />
      </div>

      <div class="debug-tools-toggle" @click="toggleDebugTools">
        <el-tooltip content="调试工具" placement="left">
          <el-button class="debug-button" circle>
            <el-icon><Setting /></el-icon>
          </el-button>
        </el-tooltip>
      </div>
    </div>
  </el-config-provider>
</template>

<script setup>
import { computed, onMounted, onUnmounted, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { ElConfigProvider, ElMessage } from 'element-plus'
import {
  ArrowDown,
  HomeFilled,
  InfoFilled,
  Message,
  Search,
  Setting,
  UserFilled
} from '@element-plus/icons-vue'
import { useRouter } from 'vue-router'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'
import websocket from '@/services/websocket'
import DebugTools from '@/components/DebugTools.vue'
import Notifications from '@/components/Notifications.vue'

const initializing = ref(true)
const isScrolled = ref(false)
const showDebugTools = ref(false)

const store = useStore()
const router = useRouter()

const websocketConnected = computed(() => store.state.websocketConnected)
const isAuthenticated = computed(() => store.getters['auth/isAuthenticated'])
const currentUser = computed(() => store.getters['auth/currentUser'])
const isAdmin = computed(() => store.getters['auth/isAdmin'])
const userInitial = computed(() => {
  const username = currentUser.value?.username || 'U'
  return username.slice(0, 1).toUpperCase()
})

const handleScroll = () => {
  isScrolled.value = window.scrollY > 8
}

const toggleDebugTools = () => {
  showDebugTools.value = !showDebugTools.value
  localStorage.setItem('show_debug_tools', showDebugTools.value ? 'true' : 'false')
}

const initializeAuth = async () => {
  initializing.value = true

  if (isAuthenticated.value) {
    try {
      await store.dispatch('auth/getCurrentUser')
    } catch (error) {
      console.error('获取用户信息失败:', error)
    }
  }

  initializing.value = false
}

const handleUserCommand = (command) => {
  if (command === 'account') {
    router.push('/account')
    return
  }

  if (command === 'admin') {
    router.push('/admin/users')
    return
  }

  if (command === 'logout') {
    handleLogout()
  }
}

const handleLogout = async () => {
  try {
    await store.dispatch('auth/logout')
    router.push('/login')
    ElMessage({
      type: 'success',
      message: '已退出登录'
    })
  } catch (error) {
    console.error('退出登录失败:', error)
    ElMessage.error('退出登录失败')
  }
}

const handleConnect = () => {
  store.commit('SET_WEBSOCKET_CONNECTED', true)
}

const handleDisconnect = () => {
  store.commit('SET_WEBSOCKET_CONNECTED', false)
}

watch(isAuthenticated, (newValue) => {
  if (newValue) {
    if (!websocket.isConnected) {
      websocket.connect()
    }
    return
  }

  websocket.disconnect()
})

onMounted(async () => {
  await initializeAuth()

  websocket.onConnect(handleConnect)
  websocket.onDisconnect(handleDisconnect)

  if (isAuthenticated.value && !websocket.isConnected) {
    websocket.connect()
  }

  window.addEventListener('scroll', handleScroll)
  showDebugTools.value = localStorage.getItem('show_debug_tools') === 'true'

  if (!document.cookie.includes('CookieConsent')) {
    document.cookie = 'CookieConsent=true; SameSite=None; Secure; Partitioned; Path=/;'
  }
})

onUnmounted(() => {
  websocket.offConnect(handleConnect)
  websocket.offDisconnect(handleDisconnect)
  websocket.disconnect()
  window.removeEventListener('scroll', handleScroll)
})
</script>

<style scoped>
.app-container {
  position: relative;
  min-height: 100vh;
  overflow: hidden;
}

.app-shell {
  position: relative;
  min-height: 100vh;
  background: transparent;
}

.app-header {
  height: auto !important;
  padding: 0 !important;
  background: transparent;
}

.app-header-inner,
.app-main-inner,
.app-footer {
  width: min(1440px, 100%);
  margin: 0 auto;
  padding-left: 1rem;
  padding-right: 1rem;
}

.app-header-inner {
  padding-top: 1rem;
  padding-bottom: 0.35rem;
}

.app-main {
  padding: 0 0 1.75rem !important;
  background: transparent;
}

.app-main-inner {
  padding-top: 0.5rem;
}

.shell-panel {
  border: 1px solid rgba(255, 255, 255, 0.72);
  background:
    linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(248, 250, 252, 0.76)),
    radial-gradient(circle at top right, rgba(56, 189, 248, 0.15), transparent 30%);
  box-shadow: 0 30px 80px -40px rgba(15, 23, 42, 0.42);
  backdrop-filter: blur(18px);
}

.app-header-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  border-radius: 1.75rem;
  padding: 1rem 1.2rem;
  transition: box-shadow var(--transition-normal), transform var(--transition-normal);
}

.app-header-panel.is-scrolled {
  box-shadow: 0 34px 95px -46px rgba(15, 23, 42, 0.5);
}

.header-left,
.header-right {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.header-left {
  min-width: 0;
}

.logo-link {
  display: flex;
  align-items: center;
  gap: 0.9rem;
}

.logo-mark {
  display: grid;
  height: 3rem;
  width: 3rem;
  place-items: center;
  border-radius: 1rem;
  background: linear-gradient(135deg, #0f172a 0%, #0f766e 55%, #67e8f9 100%);
  color: white;
  font-size: 0.95rem;
  font-weight: 800;
  letter-spacing: 0.08em;
  box-shadow: 0 18px 30px -18px rgba(15, 118, 110, 0.7);
}

.logo-copy {
  min-width: 0;
}

.logo-kicker {
  display: block;
  margin-bottom: 0.2rem;
  font-size: 0.68rem;
  font-weight: 700;
  letter-spacing: 0.24em;
  text-transform: uppercase;
  color: #64748b;
}

.logo-copy h1 {
  font-size: 1.18rem;
  font-weight: 700;
  color: #0f172a;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.22);
  background: rgba(255, 255, 255, 0.65);
  padding: 0.65rem 0.95rem;
  color: #475569;
  font-size: 0.9rem;
}

.status-dot {
  width: 0.65rem;
  height: 0.65rem;
  border-radius: 999px;
  background: #f97316;
  box-shadow: 0 0 0 0.35rem rgba(249, 115, 22, 0.12);
}

.status-dot.online {
  background: #22c55e;
  box-shadow: 0 0 0 0.35rem rgba(34, 197, 94, 0.12);
}

.shell-button {
  border: none;
  border-radius: 999px;
  padding: 0.85rem 1.15rem;
  font-weight: 600;
  box-shadow: none;
}

.shell-button-primary {
  background: linear-gradient(135deg, #0f766e, #0891b2);
  color: white;
}

.shell-button-secondary {
  background: rgba(255, 255, 255, 0.9);
  color: #0f172a;
  border: 1px solid rgba(148, 163, 184, 0.22);
}

.user-dropdown-link {
  display: inline-flex;
  align-items: center;
  gap: 0.65rem;
  cursor: pointer;
  border-radius: 999px;
  border: 1px solid rgba(148, 163, 184, 0.18);
  background: rgba(255, 255, 255, 0.78);
  padding: 0.45rem 0.85rem 0.45rem 0.45rem;
  color: #0f172a;
  transition: transform var(--transition-fast), box-shadow var(--transition-fast);
}

.user-dropdown-link:hover {
  transform: translateY(-1px);
  box-shadow: 0 16px 28px -24px rgba(15, 23, 42, 0.42);
}

.user-avatar {
  display: grid;
  height: 2rem;
  width: 2rem;
  place-items: center;
  border-radius: 999px;
  background: linear-gradient(135deg, #cffafe, #99f6e4);
  color: #0f172a;
  font-size: 0.82rem;
  font-weight: 800;
}

.user-name {
  max-width: 12rem;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  font-weight: 600;
}

.connection-status {
  display: flex;
  align-items: center;
}

.nav-panel {
  margin-top: 0.9rem;
  overflow-x: auto;
  border-radius: 1.5rem;
  padding: 0.45rem 0.55rem;
}

.app-nav {
  --el-menu-bg-color: transparent;
  --el-menu-hover-bg-color: rgba(226, 232, 240, 0.55);
  --el-menu-active-color: #0f172a;
  --el-menu-text-color: #475569;
  border-bottom: none !important;
  background: transparent !important;
}

:deep(.app-nav.el-menu--horizontal) {
  display: flex;
  flex-wrap: wrap;
  gap: 0.35rem;
  border-bottom: none;
}

:deep(.app-nav.el-menu--horizontal > .el-menu-item) {
  height: 2.85rem;
  line-height: 2.85rem;
  border-bottom: none !important;
  border-radius: 999px;
  margin: 0;
  color: #475569;
  font-weight: 600;
  transition: background-color var(--transition-fast), transform var(--transition-fast), color var(--transition-fast);
}

:deep(.app-nav.el-menu--horizontal > .el-menu-item:hover) {
  transform: translateY(-1px);
}

:deep(.app-nav.el-menu--horizontal > .el-menu-item.is-active) {
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.12), rgba(8, 145, 178, 0.16));
  color: #0f172a;
  box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.12);
}

:deep(.app-nav .el-icon) {
  margin-right: 0.45rem;
}

.loading-container {
  min-height: 20rem;
}

.footer-panel {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 1.25rem;
  border-radius: 1.5rem;
  padding: 1rem 1.2rem;
  color: #475569;
}

.footer-panel p {
  font-weight: 700;
  color: #0f172a;
}

.footer-panel span {
  font-size: 0.92rem;
}

.debug-tools-container {
  position: fixed;
  right: 1.2rem;
  bottom: 5.25rem;
  z-index: 2000;
  width: min(420px, 92vw);
  border-radius: 1.5rem;
  border: 1px solid rgba(255, 255, 255, 0.72);
  background: rgba(255, 255, 255, 0.84);
  box-shadow: 0 26px 90px -38px rgba(15, 23, 42, 0.5);
  backdrop-filter: blur(18px);
}

.debug-tools-toggle {
  position: fixed;
  right: 1.25rem;
  bottom: 1.35rem;
  z-index: 2001;
}

.debug-button {
  border: none;
  background: linear-gradient(135deg, #0f172a, #0f766e) !important;
  color: white !important;
  box-shadow: 0 24px 50px -26px rgba(15, 118, 110, 0.8);
}

.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
  transform: translateY(6px);
}

@media (max-width: 1024px) {
  .lg-only {
    display: none;
  }
}

@media (max-width: 768px) {
  .app-header-inner,
  .app-main-inner,
  .app-footer {
    padding-left: 0.85rem;
    padding-right: 0.85rem;
  }

  .app-header-panel,
  .footer-panel {
    border-radius: 1.35rem;
  }

  .app-header-panel {
    flex-direction: column;
    align-items: stretch;
  }

  .header-left,
  .header-right {
    justify-content: space-between;
    flex-wrap: wrap;
  }

  .header-right {
    gap: 0.75rem;
  }

  .connection-status {
    margin-left: auto;
  }

  .footer-panel {
    flex-direction: column;
    align-items: flex-start;
  }
}

@media (max-width: 576px) {
  .logo-copy h1 {
    font-size: 1rem;
  }

  .header-right {
    align-items: center;
  }

  .connection-status {
    margin-left: 0;
  }

  :deep(.app-nav.el-menu--horizontal) {
    flex-wrap: nowrap;
    width: max-content;
  }
}
</style>
