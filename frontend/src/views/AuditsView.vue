<script setup lang="ts">
import { onMounted, ref } from "vue";
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

function query(includePage = true): string {
  const params = new URLSearchParams();
  if (includePage) {
    params.set("page", String(data.value.page));
    params.set("pageSize", String(data.value.pageSize));
  }
  if (status.value) params.set("status", status.value);
  if (capabilityCode.value.trim()) params.set("capabilityCode", capabilityCode.value.trim());
  if (requestId.value.trim() && includePage) params.set("requestId", requestId.value.trim());
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

onMounted(() => load());
</script>

<template>
  <div class="stack-lg">
    <section class="panel filter-panel">
      <div class="filter-grid">
        <label class="field compact"><span>请求编号</span><input v-model="requestId" placeholder="精确查询 requestId" /></label>
        <label class="field compact"><span>状态</span><select v-model="status"><option value="">全部状态</option><option value="success">成功</option><option value="failed">失败</option></select></label>
        <label class="field compact"><span>能力编号</span><input v-model="capabilityCode" placeholder="如 recruitment.resume.parse" /></label>
        <button class="button primary filter-action" type="button" :disabled="loading" @click="load(true)">查询</button>
        <button class="button ghost filter-action" type="button" @click="downloadAuditCsv(query(false))">导出记录</button>
      </div>
    </section>
    <ErrorNotice v-if="error" :message="error" />
    <section class="panel">
      <div class="panel-heading">
        <div><span class="eyebrow">业务请求与上游消耗</span><h2>审计记录</h2></div>
        <span class="muted">共 {{ data.total.toLocaleString() }} 条</span>
      </div>
      <div v-if="data.items.length" class="table-wrap">
        <table>
          <thead><tr><th>请求编号</th><th>业务能力</th><th>状态</th><th>调用 / 重试</th><th>Token</th><th>耗时</th><th>时间</th></tr></thead>
          <tbody>
            <tr v-for="item in data.items" :key="item.requestId">
              <td><span class="mono">{{ item.requestId }}</span><small class="cell-note">{{ item.callerSystem }}</small></td>
              <td>{{ item.capabilityCode }}<small class="cell-note">{{ item.model }}</small></td>
              <td><span class="badge" :class="item.status === 'success' ? 'success' : 'danger'">{{ item.status === "success" ? "成功" : "失败" }}</span><small v-if="item.errorCode" class="cell-note error-text">{{ item.errorCode }}</small></td>
              <td>{{ item.upstreamCallCount }} / {{ item.retryCount }}</td>
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
