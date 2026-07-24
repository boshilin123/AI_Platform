<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();
const pageTitle = computed(() => String(route.meta.title ?? "AI 能力中台"));

const navigation = [
  { to: "/", label: "工作台", icon: "⌂" },
  { to: "/recruitment", label: "招聘助手", icon: "人" },
  { to: "/audits", label: "调用审计", icon: "记" },
  { to: "/settings", label: "基础配置", icon: "设" },
];
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-mark" aria-hidden="true"><span></span><span></span><span></span></div>
        <strong>AI 能力中台</strong>
      </div>
      <nav class="navigation" aria-label="主导航">
        <RouterLink v-for="item in navigation" :key="item.to" :to="item.to">
          <span class="nav-icon">{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>
      <div class="sidebar-footer">
        <span class="status-dot"></span>
        <span>内部服务</span>
      </div>
    </aside>
    <section class="content-shell">
      <header class="topbar">
        <h1>{{ pageTitle }}</h1>
        <div class="topbar-meta"><span class="status-dot"></span>GPT 服务正常</div>
      </header>
      <main class="page-content">
        <RouterView />
      </main>
    </section>
  </div>
</template>
