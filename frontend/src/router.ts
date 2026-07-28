import { createRouter, createWebHistory } from "vue-router";

import AuditsView from "./views/AuditsView.vue";
import DashboardView from "./views/DashboardView.vue";
import RecruitmentView from "./views/RecruitmentView.vue";
import SettingsView from "./views/SettingsView.vue";
import TtsView from "./views/TtsView.vue";

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
    {
      path: "/tts",
      name: "tts",
      component: TtsView,
      meta: { title: "文字转语音助手" },
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
  document.title = `${String(route.meta.title)} · AI Agent 中台`;
});
