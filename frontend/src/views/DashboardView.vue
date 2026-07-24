<script setup lang="ts">
import { onMounted, ref } from "vue";
import { apiRequest } from "../api/client";
import EmptyState from "../components/EmptyState.vue";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { DashboardData, HealthData } from "../types/api";

const dashboard = ref<DashboardData | null>(null);
const health = ref<HealthData | null>(null);
const loading = ref(true);
const error = ref("");

const number = new Intl.NumberFormat("zh-CN");

async function load(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const [overviewResponse, healthResponse] = await Promise.all([
      apiRequest<DashboardData>("/api/v1/dashboard/overview"),
      apiRequest<HealthData>("/api/v1/system/health"),
    ]);
    dashboard.value = overviewResponse.data;
    health.value = healthResponse.data;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "工作台数据加载失败";
  } finally {
    loading.value = false;
  }
}

onMounted(load);
</script>

<template>
  <div class="stack-lg">
    <ErrorNotice v-if="error" :message="error" />
    <section class="hero-card">
      <div>
        <span class="eyebrow">业务场景</span>
        <h2>让 AI 能力真正进入业务流程</h2>
        <p>当前首先开放招聘助手，后续业务场景将在同一底座上持续接入。</p>
      </div>
      <RouterLink class="button primary" to="/recruitment">进入招聘助手</RouterLink>
    </section>

    <section>
      <div class="section-heading">
        <div><span class="eyebrow">运行概览</span><h2>今日服务状态</h2></div>
        <button class="button ghost" type="button" :disabled="loading" @click="load">刷新</button>
      </div>
      <div class="metric-grid">
        <article class="metric-card">
          <span>业务请求</span><strong>{{ number.format(dashboard?.stats.businessRequests ?? 0) }}</strong>
          <small>实际进入中台的请求</small>
        </article>
        <article class="metric-card">
          <span>上游调用</span><strong>{{ number.format(dashboard?.stats.upstreamCalls ?? 0) }}</strong>
          <small>包含格式修复与重试</small>
        </article>
        <article class="metric-card">
          <span>Token 用量</span><strong>{{ number.format(dashboard?.stats.totalTokens ?? 0) }}</strong>
          <small>输入与输出合计</small>
        </article>
        <article class="metric-card">
          <span>成功率</span><strong>{{ (dashboard?.stats.successRate ?? 100).toFixed(1) }}%</strong>
          <small class="healthy"><span class="status-dot"></span>服务运行正常</small>
        </article>
      </div>
    </section>

    <section class="two-column">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">已开放</span><h2>招聘助手</h2></div><span class="badge success">可用</span></div>
        <p class="panel-description">完成简历结构化、岗位匹配初筛和针对性面试题生成。</p>
        <div class="capability-list">
          <span>简历解析</span><span>岗位初筛</span><span>面试题生成</span>
        </div>
        <RouterLink class="text-link" to="/recruitment">开始使用 →</RouterLink>
      </article>
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">服务状态</span><h2>基础依赖</h2></div></div>
        <div class="service-list">
          <div><span>API 服务</span><span class="badge success">正常</span></div>
          <div><span>审计数据库</span><span class="badge success">{{ health?.database === "ok" ? "正常" : "检查中" }}</span></div>
          <div><span>模型调用</span><span class="badge neutral">{{ health?.llmMode === "mock" ? "模拟模式" : "上游模式" }}</span></div>
        </div>
      </article>
    </section>

    <section class="panel">
      <div class="panel-heading"><div><span class="eyebrow">最近调用</span><h2>招聘业务记录</h2></div><RouterLink class="text-link" to="/audits">查看全部</RouterLink></div>
      <div v-if="dashboard?.recentRequests.length" class="table-wrap">
        <table>
          <thead><tr><th>请求编号</th><th>能力</th><th>状态</th><th>Token</th><th>耗时</th><th>时间</th></tr></thead>
          <tbody>
            <tr v-for="item in dashboard.recentRequests" :key="item.requestId">
              <td class="mono">{{ item.requestId }}</td><td>{{ item.capabilityCode }}</td>
              <td><span class="badge" :class="item.status === 'success' ? 'success' : 'danger'">{{ item.status === "success" ? "成功" : "失败" }}</span></td>
              <td>{{ number.format(item.totalTokens) }}</td><td>{{ item.durationMs }} ms</td><td>{{ new Date(item.createdAt).toLocaleString("zh-CN") }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState v-else title="暂无调用记录" description="使用招聘助手后，调用摘要会显示在这里。" />
    </section>
  </div>
</template>
