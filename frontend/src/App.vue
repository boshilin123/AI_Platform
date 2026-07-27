<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";
import companyLogo from "./assets/company-logo.png";

const route = useRoute();
const pageTitle = computed(() => String(route.meta.title ?? "AI Agent 中台"));

const navigation = [
  { to: "/", label: "工作台", group: "工作空间", icon: "home" },
  { to: "/recruitment", label: "招聘助手", group: "工作空间", icon: "recruitment" },
  { to: "/audits", label: "调用审计", group: "管理", icon: "audit" },
  { to: "/settings", label: "基础配置", group: "管理", icon: "settings" },
] as const;

const groups = ["工作空间", "管理"] as const;
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-logo">
          <img :src="companyLogo" alt="公司 Logo" />
        </div>
        <strong>AI Agent 中台</strong>
      </div>

      <nav class="navigation" aria-label="主导航">
        <section v-for="group in groups" :key="group" class="nav-group">
          <div class="nav-label">{{ group }}</div>
          <RouterLink
            v-for="item in navigation.filter((entry) => entry.group === group)"
            :key="item.to"
            :to="item.to"
          >
            <svg v-if="item.icon === 'home'" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M3 11.2 12 4l9 7.2" /><path d="M5.5 10v9h13v-9" /><path d="M9.5 19v-5h5v5" />
            </svg>
            <svg v-else-if="item.icon === 'recruitment'" viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="10" cy="8" r="3.5" /><path d="M3.5 20c.8-4 3-6 6.5-6 2.1 0 3.8.7 4.9 2" /><circle cx="18" cy="18" r="3" /><path d="m20.2 20.2 1.8 1.8" />
            </svg>
            <svg v-else-if="item.icon === 'audit'" viewBox="0 0 24 24" aria-hidden="true">
              <path d="M5 4h14v16H5z" /><path d="M8 8h8M8 12h8M8 16h5" />
            </svg>
            <svg v-else viewBox="0 0 24 24" aria-hidden="true">
              <circle cx="12" cy="12" r="3" /><path d="M19.4 15a1.8 1.8 0 0 0 .4 2l.1.1-2.8 2.8-.1-.1a1.8 1.8 0 0 0-2-.4 1.8 1.8 0 0 0-1.1 1.6V21H10v-.1A1.8 1.8 0 0 0 8.9 19a1.8 1.8 0 0 0-2 .4l-.1.1L4 16.7l.1-.1a1.8 1.8 0 0 0 .4-2A1.8 1.8 0 0 0 3 13.5H3v-4h.1a1.8 1.8 0 0 0 1.6-1.1 1.8 1.8 0 0 0-.4-2l-.1-.1L7 3.5l.1.1a1.8 1.8 0 0 0 2 .4A1.8 1.8 0 0 0 10.2 2H14v.1A1.8 1.8 0 0 0 15.1 4a1.8 1.8 0 0 0 2-.4l.1-.1L20 6.3l-.1.1a1.8 1.8 0 0 0-.4 2 1.8 1.8 0 0 0 1.6 1.1h.1v4H21a1.8 1.8 0 0 0-1.6 1.5Z" />
            </svg>
            <span>{{ item.label }}</span>
          </RouterLink>
        </section>
      </nav>

      <div class="sidebar-footer">
        <span class="avatar">管</span>
        <span>
          <strong>平台管理员</strong>
          <small>系统管理与审计</small>
        </span>
      </div>
    </aside>

    <section class="content-shell">
      <header class="topbar">
        <h1>{{ pageTitle }}</h1>
        <div class="top-actions">
          <div class="service-pill"><span class="status-dot"></span>GPT 服务正常</div>
          <button class="icon-button" type="button" title="通知" aria-label="通知">
            <svg viewBox="0 0 24 24" aria-hidden="true">
              <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 8h18c0-1-3-1-3-8" /><path d="M10 21h4" />
            </svg>
          </button>
        </div>
      </header>
      <main class="page-content">
        <RouterView v-slot="{ Component }">
          <KeepAlive include="RecruitmentView">
            <component :is="Component" />
          </KeepAlive>
        </RouterView>
      </main>
    </section>
  </div>
</template>
