<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { apiRequest } from "../api/client";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { DashboardData, HealthData, SettingsData } from "../types/api";

const dashboard = ref<DashboardData | null>(null);
const health = ref<HealthData | null>(null);
const runtimeSettings = ref<SettingsData | null>(null);
const loading = ref(true);
const error = ref("");
const number = new Intl.NumberFormat("zh-CN");
const CHART_LEFT = 68;
const CHART_RIGHT = 742;
const CHART_TOP = 20;
const CHART_BOTTOM = 205;

const averageDuration = computed(() => {
  const milliseconds = dashboard.value?.stats.averageDurationMs ?? 0;
  return milliseconds >= 1000 ? `${(milliseconds / 1000).toFixed(1)}s` : `${milliseconds}ms`;
});

const chartItems = computed(() => dashboard.value?.usageTrend ?? []);
const usageTotal = computed(() =>
  chartItems.value.reduce((total, item) => total + item.requestCount, 0),
);
const chartMaximum = computed(() => {
  const maximum = Math.max(...chartItems.value.map((item) => item.requestCount), 0);
  return Math.max(4, Math.ceil(maximum / 4) * 4);
});
const chartPointItems = computed(() => {
  const items = chartItems.value;
  return items.map((item, index) => {
    const ratio = items.length === 1 ? 0.5 : index / (items.length - 1);
    const x = CHART_LEFT + ratio * (CHART_RIGHT - CHART_LEFT);
    const y = CHART_BOTTOM - (item.requestCount / chartMaximum.value) * (CHART_BOTTOM - CHART_TOP);
    return {
      item,
      x,
      y,
      labelAnchor: index === 0 ? "start" : index === items.length - 1 ? "end" : "middle",
    };
  });
});
const chartPoints = computed(() => chartPointItems.value.map((point) => `${point.x},${point.y}`).join(" "));
const chartAreaPoints = computed(() =>
  chartPointItems.value.length
    ? `${CHART_LEFT},${CHART_BOTTOM} ${chartPoints.value} ${CHART_RIGHT},${CHART_BOTTOM}`
    : "",
);
const chartYTicks = computed(() => [1, 0.75, 0.5, 0.25, 0].map((ratio) => ({
  value: Math.round(chartMaximum.value * ratio),
  y: CHART_BOTTOM - ratio * (CHART_BOTTOM - CHART_TOP),
})));

function formatTrendDate(value: string): string {
  const [, month, day] = value.split("-");
  return `${Number(month)}/${Number(day)}`;
}

async function load(): Promise<void> {
  loading.value = true;
  error.value = "";
  try {
    const [overviewResponse, healthResponse, settingsResponse] = await Promise.all([
      apiRequest<DashboardData>("/api/v1/dashboard/overview"),
      apiRequest<HealthData>("/api/v1/system/health"),
      apiRequest<SettingsData>("/api/v1/settings"),
    ]);
    dashboard.value = overviewResponse.data;
    health.value = healthResponse.data;
    runtimeSettings.value = settingsResponse.data;
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

    <section class="metric-grid" aria-label="今日运行指标">
      <article class="metric-card">
        <div class="metric-head">
          <span class="metric-label">今日业务请求</span>
          <span class="metric-icon"><svg viewBox="0 0 24 24"><path d="m6 15 6-6 6 6" /></svg></span>
        </div>
        <strong>{{ number.format(dashboard?.stats.businessRequests ?? 0) }}</strong>
        <small>上游调用 {{ number.format(dashboard?.stats.upstreamCalls ?? 0) }} 次</small>
      </article>
      <article class="metric-card">
        <div class="metric-head">
          <span class="metric-label">今日 Token</span>
          <span class="metric-icon"><svg viewBox="0 0 24 24"><path d="M7 5h10M12 5v14M8 19h8" /></svg></span>
        </div>
        <strong>{{ number.format(dashboard?.stats.totalTokens ?? 0) }}</strong>
        <small>输入与输出 Token 合计</small>
      </article>
      <article class="metric-card">
        <div class="metric-head">
          <span class="metric-label">调用成功率</span>
          <span class="metric-icon"><svg viewBox="0 0 24 24"><path d="m5 12 4 4L19 6" /></svg></span>
        </div>
        <strong>{{ (dashboard?.stats.successRate ?? 100).toFixed(1) }}%</strong>
        <small>{{ number.format(dashboard?.stats.retryCount ?? 0) }} 次自动重试</small>
      </article>
      <article class="metric-card">
        <div class="metric-head">
          <span class="metric-label">平均响应耗时</span>
          <span class="metric-icon"><svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="9" /><path d="M12 7v5l3 2" /></svg></span>
        </div>
        <strong>{{ averageDuration }}</strong>
        <small class="healthy"><span class="status-dot"></span>服务运行正常</small>
      </article>
    </section>

    <section>
      <div class="section-title-row">
        <h2>业务场景</h2>
        <span>当前已接入 2 个场景</span>
      </div>
      <div class="scenario-layout">
        <article class="panel scenario-card">
          <div class="scenario-card-top">
            <span class="scene-icon">
              <svg viewBox="0 0 24 24"><rect x="3" y="7" width="18" height="13" rx="2" /><path d="M8 7V5h8v2M3 12h18M10 12v2h4v-2" /></svg>
            </span>
            <span class="status-tag">已上线</span>
          </div>
          <h2>招聘助手</h2>
          <p>面向招聘流程提供简历信息提取、岗位匹配分析与针对性面试题生成，所有调用统一记录审计日志和 Token 用量。</p>
          <div class="scene-tags"><span>简历解析</span><span>岗位初筛</span><span>面试题生成</span></div>
          <div class="scene-actions">
            <RouterLink class="button primary" to="/recruitment">
              进入招聘助手
              <svg width="15" height="15" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
            </RouterLink>
          </div>
        </article>

        <article class="panel scenario-card">
          <div class="scenario-card-top">
            <span class="scene-icon">
              <svg viewBox="0 0 24 24"><path d="M4 14h3l4 4V6L7 10H4z" /><path d="M15 9c1.7 1.6 1.7 4.4 0 6M18 6c3.4 3.2 3.4 8.8 0 12" /></svg>
            </span>
            <span class="status-tag">已上线</span>
          </div>
          <h2>文字转语音助手</h2>
          <p>通过独立的语音合成能力将通知、培训材料和办公文本转换为可试听、可下载的音频，并复用中台凭据与统一审计。</p>
          <div class="scene-tags"><span>tts-1</span><span>多声音</span><span>MP3 / WAV</span></div>
          <div class="scene-actions">
            <RouterLink class="button primary" to="/tts">
              进入语音助手
              <svg width="15" height="15" viewBox="0 0 24 24"><path d="M5 12h14M13 6l6 6-6 6" /></svg>
            </RouterLink>
          </div>
        </article>

        <article class="panel future-card scenario-future-wide">
          <div class="future-head"><strong>后续业务接入</strong><span class="status-tag">规划中</span></div>
          <div class="future-list">
            <div class="future-item">
              <span class="future-item-icon"><svg viewBox="0 0 24 24"><path d="M4 5.5A3.5 3.5 0 0 1 7.5 2H11v17H7.5A3.5 3.5 0 0 0 4 22zM20 5.5A3.5 3.5 0 0 0 16.5 2H13v17h3.5A3.5 3.5 0 0 1 20 22z" /></svg></span>
              <span class="future-item-name">培训助手</span><span class="future-item-state">待接入</span>
            </div>
            <div class="future-item">
              <span class="future-item-icon"><svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="6" rx="2" /><rect x="3" y="14" width="18" height="6" rx="2" /></svg></span>
              <span class="future-item-name">运维助手</span><span class="future-item-state">待接入</span>
            </div>
            <div class="future-item">
              <span class="future-item-icon"><svg viewBox="0 0 24 24"><path d="M6 3h8l4 4v14H6zM14 3v5h5M9 12h6M9 16h6" /></svg></span>
              <span class="future-item-name">文档助手</span><span class="future-item-state">待接入</span>
            </div>
          </div>
        </article>
      </div>
    </section>

    <section>
      <div class="section-title-row">
        <h2>用量趋势</h2>
        <RouterLink class="button" to="/audits">查看调用审计</RouterLink>
      </div>
      <div class="overview-grid">
        <article class="panel chart-card">
          <div class="panel-heading">
            <div><strong>API 调用次数</strong><div class="muted">按北京时间统计近 7 天业务请求</div></div>
            <div class="usage-chart-summary">
              <span><strong>{{ number.format(usageTotal) }}</strong><small>7 日累计</small></span>
              <button class="button" type="button" :disabled="loading" @click="load">{{ loading ? "刷新中" : "刷新" }}</button>
            </div>
          </div>
          <div class="chart-placeholder">
            <svg viewBox="0 0 760 266" role="img" aria-labelledby="usage-chart-title usage-chart-description">
              <title id="usage-chart-title">近 7 天 API 调用次数</title>
              <desc id="usage-chart-description">横轴为北京时间日期，纵轴为当天业务请求次数。</desc>
              <g v-for="tick in chartYTicks" :key="tick.y" class="chart-grid-line">
                <line :x1="CHART_LEFT" :x2="CHART_RIGHT" :y1="tick.y" :y2="tick.y" />
                <text :x="CHART_LEFT - 10" :y="tick.y + 4" text-anchor="end">{{ number.format(tick.value) }}</text>
              </g>
              <line class="chart-axis" :x1="CHART_LEFT" :x2="CHART_LEFT" :y1="CHART_TOP" :y2="CHART_BOTTOM" />
              <line class="chart-axis" :x1="CHART_LEFT" :x2="CHART_RIGHT" :y1="CHART_BOTTOM" :y2="CHART_BOTTOM" />
              <polygon v-if="chartPointItems.length > 1" class="chart-area" :points="chartAreaPoints" />
              <polyline v-if="chartPointItems.length > 1" class="chart-line" :points="chartPoints" />
              <g v-for="point in chartPointItems" :key="point.item.date">
                <circle class="chart-point" :cx="point.x" :cy="point.y" r="4">
                  <title>{{ point.item.date }}，{{ number.format(point.item.requestCount) }} 次</title>
                </circle>
                <text
                  class="chart-date-label"
                  :x="point.x"
                  y="233"
                  :text-anchor="point.labelAnchor"
                >
                  {{ formatTrendDate(point.item.date) }}
                </text>
              </g>
              <text class="chart-axis-title" x="405" y="260" text-anchor="middle">日期</text>
              <text class="chart-axis-title" x="13" y="113" text-anchor="middle" transform="rotate(-90 13 113)">调用次数</text>
            </svg>
            <div v-if="usageTotal === 0 && !loading" class="chart-empty">近 7 天暂无调用数据</div>
          </div>
        </article>
        <article class="panel health-card">
          <div class="panel-heading"><div><strong>基础服务</strong><div class="muted">当前依赖健康状态</div></div></div>
          <div class="health-list">
            <div class="health-item"><span class="health-badge">API</span><span class="health-copy"><strong>中台服务</strong><small>FastAPI 接口服务</small></span><span class="health-state">正常</span></div>
            <div class="health-item"><span class="health-badge">DB</span><span class="health-copy"><strong>审计数据库</strong><small>MySQL 数据持久化</small></span><span class="health-state">{{ health?.database === "ok" ? "正常" : "检查中" }}</span></div>
            <div class="health-item">
              <span class="health-badge">AI</span>
              <span class="health-copy">
                <strong>当前模型</strong>
                <small>{{ runtimeSettings?.model ?? "读取中" }} · {{ health?.llmMode === "mock" ? "模拟模式" : "上游模式" }}</small>
              </span>
              <span class="health-state">
                {{ runtimeSettings?.mockMode || runtimeSettings?.apiKeyConfigured ? "已配置" : "待配置" }}
              </span>
            </div>
          </div>
        </article>
      </div>
    </section>
  </div>
</template>
