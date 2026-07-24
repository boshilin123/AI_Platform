import { createRouter, createWebHistory } from "vue-router";

import AuditsView from "./views/AuditsView.vue";
import DashboardView from "./views/DashboardView.vue";
import RecruitmentView from "./views/RecruitmentView.vue";
import SettingsView from "./views/SettingsView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", name: "dashboard", component: DashboardView, meta: { title: "工作台" } },
    {
      path: "/recruitment",
      name: "recruitment",
      component: RecruitmentView,
      meta: { title: "招聘助手" },
    },
    { path: "/audits", name: "audits", component: AuditsView, meta: { title: "调用审计" } },
    {
      path: "/settings",
      name: "settings",
      component: SettingsView,
      meta: { title: "基础配置" },
    },
  ],
});

router.afterEach((route) => {
  document.title = `${String(route.meta.title)} · AI 能力中台`;
});
