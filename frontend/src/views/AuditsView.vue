<script setup lang="ts">
import { computed, onMounted, ref } from "vue";
import { apiRequest, downloadAuditCsv } from "../api/client";
import EmptyState from "../components/EmptyState.vue";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { AuditListData } from "../types/api";

const data = ref<AuditListData>({ items: [], page: 1, pageSize: 20, total: 0 });
const status = ref("");
const capabilityCode = ref("");
const requestId = ref("");
const loading = ref(false);
const error = ref("");
const pageUpstreamCalls = computed(() => data.value.items.reduce((sum, item) => sum + item.upstreamCallCount, 0));
const pageTokens = computed(() => data.value.items.reduce((sum, item) => sum + item.totalTokens, 0));
const pageFailures = computed(() => data.value.items.filter((item) => item.status !== "success").length);

function query(includePage = true): string {
  const params = new URLSearchParams();
  if (includePage) {
    params.set("page", String(data.value.page));
    params.set("pageSize", String(data.value.pageSize));
  }
  if (status.value) params.set("status", status.value);
  if (capabilityCode.value.trim()) params.set("capabilityCode", capabilityCode.value.trim());
  if (requestId.value.trim()) params.set("requestId", requestId.value.trim());
  const value = params.toString();
  return value ? `?${value}` : "";
}

async function load(reset = false): Promise<void> {
  if (reset) data.value.page = 1;
  loading.value = true;
  error.value = "";
  try {
    const response = await apiRequest<AuditListData>(`/api/v1/audits${query()}`);
    data.value = response.data;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "调用记录加载失败";
  } finally {
    loading.value = false;
  }
}

async function changePage(delta: number): Promise<void> {
  data.value.page += delta;
  await load();
}

async function reset(): Promise<void> {
  status.value = "";
  capabilityCode.value = "";
  requestId.value = "";
  await load(true);
}

onMounted(() => load());
</script>

<template>
  <div class="stack-lg">
    <div class="audit-actions"><button class="button" type="button" @click="downloadAuditCsv(query(false))">导出记录</button></div>

    <section class="metric-grid" aria-label="审计统计">
      <article class="metric-card"><span class="metric-label">筛选结果请求</span><strong>{{ data.total.toLocaleString() }}</strong><small>符合当前条件的业务请求</small></article>
      <article class="metric-card"><span class="metric-label">本页上游调用</span><strong>{{ pageUpstreamCalls.toLocaleString() }}</strong><small>包含传输重试与格式修复</small></article>
      <article class="metric-card"><span class="metric-label">本页总 Token</span><strong>{{ pageTokens.toLocaleString() }}</strong><small>输入与输出 Token 合计</small></article>
      <article class="metric-card"><span class="metric-label">本页失败请求</span><strong>{{ pageFailures.toLocaleString() }}</strong><small>可按状态继续筛选</small></article>
    </section>

    <ErrorNotice v-if="error" :message="error" />

    <section class="panel table-panel">
      <div class="filter-row">
        <div class="filters">
          <select v-model="capabilityCode" aria-label="能力编号">
            <option value="">全部能力</option>
            <option value="recruitment.resume.parse">简历解析</option>
            <option value="recruitment.screening.evaluate">岗位初筛</option>
            <option value="recruitment.interview-kit.generate">面试题生成</option>
          </select>
          <select v-model="status" aria-label="调用状态">
            <option value="">全部状态</option>
            <option value="success">成功</option>
            <option value="failed">失败</option>
          </select>
          <input v-model="requestId" placeholder="搜索 Request ID" aria-label="请求编号" @keyup.enter="load(true)" />
          <button class="button primary" type="button" :disabled="loading" @click="load(true)">查询</button>
        </div>
        <button class="button" type="button" :disabled="loading" @click="reset">重置</button>
      </div>
      <div v-if="data.items.length" class="table-wrap">
        <table>
          <thead><tr><th>Request ID</th><th>业务 / 能力</th><th>模式</th><th>状态</th><th>上游调用</th><th>Token</th><th>耗时</th><th>时间</th></tr></thead>
          <tbody>
            <tr v-for="item in data.items" :key="item.requestId">
              <td><span class="mono">{{ item.requestId }}</span><small class="cell-note">{{ item.callerSystem }}</small></td>
              <td>{{ item.capabilityCode }}<small class="cell-note">{{ item.model }}</small></td>
              <td><span class="badge neutral">{{ item.requestMode === "stream" ? "流式" : "非流式" }}</span></td>
              <td><span class="badge" :class="item.status === 'success' ? 'success' : 'danger'">{{ item.status === "success" ? "成功" : "失败" }}</span><small v-if="item.errorCode" class="cell-note error-text">{{ item.errorCode }}</small></td>
              <td>{{ item.upstreamCallCount }}<span v-if="item.retryCount">（重试 {{ item.retryCount }}）</span></td>
              <td>{{ item.totalTokens.toLocaleString() }}</td><td>{{ item.durationMs }} ms</td>
              <td>{{ new Date(item.createdAt).toLocaleString("zh-CN") }}</td>
            </tr>
          </tbody>
        </table>
      </div>
      <EmptyState v-else title="没有匹配的调用记录" description="调整筛选条件，或先在招聘助手中提交一次任务。" />
      <div class="pagination">
        <button class="button ghost" type="button" :disabled="data.page <= 1 || loading" @click="changePage(-1)">上一页</button>
        <span>第 {{ data.page }} 页</span>
        <button class="button ghost" type="button" :disabled="data.page * data.pageSize >= data.total || loading" @click="changePage(1)">下一页</button>
      </div>
    </section>
  </div>
</template>
