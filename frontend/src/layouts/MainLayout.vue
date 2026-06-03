<template>
  <el-container class="dq-shell">
    <el-aside width="232px" class="dq-aside">
      <div class="logo">数据查询中台</div>
      <div class="logo-sub">内部查询 · 分析</div>
      <el-menu router :default-active="$route.name as string" class="dq-menu" background-color="transparent" text-color="#cbd5e1" active-text-color="#ffffff">
        <el-menu-item index="dashboard" :route="{ name: 'dashboard' }">
          <span>总览</span>
        </el-menu-item>
        <el-menu-item index="interfaces" :route="{ name: 'interfaces' }">
          <span>接口与模板</span>
        </el-menu-item>
        <el-menu-item index="query-execute" :route="{ name: 'query-execute' }">
          <span>查询工作台</span>
        </el-menu-item>
        <el-menu-item index="query-history" :route="{ name: 'query-history' }">
          <span>查询历史</span>
        </el-menu-item>
      </el-menu>
    </el-aside>
    <el-container>
      <el-header class="dq-header">
        <div class="breadcrumb-slot">
          <span class="env-hint">内部使用 · 请勿对公网暴露管理入口</span>
        </div>
        <div class="user" v-if="auth.user">
          <span class="name">{{ auth.user.realName || auth.user.username }}</span>
          <el-button link type="primary" @click="onLogout">退出</el-button>
        </div>
      </el-header>
      <el-main class="dq-main">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { useRouter } from "vue-router";
import { useAuthStore } from "@/store/auth";

const auth = useAuthStore();
const router = useRouter();

function onLogout() {
  auth.logout();
  router.push({ name: "login" });
}
</script>

<style scoped>
.dq-shell {
  height: 100vh;
  background: var(--dq-page-bg, #f3f4f6);
}
.dq-aside {
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  color: #e2e8f0;
  display: flex;
  flex-direction: column;
  border-right: 1px solid rgba(255, 255, 255, 0.06);
}
.logo {
  height: 52px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 700;
  font-size: 15px;
  letter-spacing: 0.02em;
  color: #fff;
  padding-top: 12px;
}
.logo-sub {
  text-align: center;
  font-size: 11px;
  color: #94a3b8;
  padding-bottom: 8px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  margin-bottom: 8px;
}
.dq-menu {
  border-right: none;
  flex: 1;
  padding: 4px 8px 16px;
}
.dq-menu :deep(.el-menu-item) {
  border-radius: 6px;
  margin: 2px 0;
}
.dq-menu :deep(.el-menu-item.is-active) {
  background: rgba(59, 130, 246, 0.35) !important;
}
.dq-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color-lighter);
  height: 52px !important;
}
.env-hint {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
.user {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
}
.dq-main {
  padding: 20px 24px 32px;
  overflow: auto;
}
</style>
