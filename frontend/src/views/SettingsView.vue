<script setup lang="ts">
import { onMounted, ref } from "vue";
import { apiRequest } from "../api/client";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { SettingsData } from "../types/api";

const settings = ref<SettingsData | null>(null);
const error = ref("");

async function load(): Promise<void> {
  try {
    settings.value = (await apiRequest<SettingsData>("/api/v1/settings")).data;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "基础配置加载失败";
  }
}

onMounted(load);
</script>

<template>
  <div class="stack-lg">
    <div class="notice"><strong>只读配置</strong><span>敏感配置只能通过后端环境变量维护，真实 API Key 永远不会返回到浏览器。</span></div>
    <ErrorNotice v-if="error" :message="error" />
    <section v-if="settings" class="settings-grid">
      <article class="panel setting-section">
        <div class="panel-heading"><div><span class="eyebrow">模型连接</span><h2>上游服务</h2></div><span class="badge success">{{ settings.mockMode || settings.apiKeyConfigured ? "已就绪" : "待配置" }}</span></div>
        <dl class="definition-list">
          <div><dt>运行模式</dt><dd>{{ settings.mockMode ? "模拟模式" : "上游模式" }}</dd></div>
          <div><dt>模型</dt><dd>{{ settings.model }}</dd></div>
          <div><dt>基础地址</dt><dd class="mono">{{ settings.baseUrl }}</dd></div>
          <div><dt>API Key</dt><dd>{{ settings.apiKeyConfigured ? "已通过环境变量配置" : "未配置" }}</dd></div>
        </dl>
      </article>
      <article class="panel setting-section">
        <div class="panel-heading"><div><span class="eyebrow">稳定性策略</span><h2>超时与重试</h2></div><span class="toggle on"><i></i></span></div>
        <dl class="definition-list">
          <div><dt>连接超时</dt><dd>{{ settings.connectTimeoutSeconds }} 秒</dd></div>
          <div><dt>读取超时</dt><dd>{{ settings.readTimeoutSeconds }} 秒</dd></div>
          <div><dt>流空闲超时</dt><dd>{{ settings.streamIdleTimeoutSeconds }} 秒</dd></div>
          <div><dt>最大重试</dt><dd>{{ settings.maxRetries }} 次</dd></div>
          <div><dt>重试间隔</dt><dd>{{ settings.retryDelaysSeconds.join("、") }} 秒</dd></div>
        </dl>
      </article>
      <article class="panel setting-section">
        <div class="panel-heading"><div><span class="eyebrow">审计策略</span><h2>数据安全</h2></div><span class="toggle on"><i></i></span></div>
        <dl class="definition-list">
          <div><dt>审计日志</dt><dd>已开启</dd></div>
          <div><dt>保留天数</dt><dd>{{ settings.auditRetentionDays }} 天</dd></div>
          <div><dt>原始业务内容</dt><dd>不保存</dd></div>
          <div><dt>内容指纹</dt><dd>SHA-256</dd></div>
        </dl>
      </article>
      <article class="panel setting-section">
        <div class="panel-heading"><div><span class="eyebrow">访问控制</span><h2>内部鉴权</h2></div><span class="toggle" :class="{ on: settings.internalAuthEnabled }"><i></i></span></div>
        <dl class="definition-list">
          <div><dt>运行环境</dt><dd>{{ settings.environment }}</dd></div>
          <div><dt>内部令牌</dt><dd>{{ settings.internalAuthEnabled ? "已启用" : "本地未启用" }}</dd></div>
          <div><dt>调用方标识</dt><dd>X-Caller-System</dd></div>
          <div><dt>请求追踪</dt><dd>X-Request-ID</dd></div>
        </dl>
      </article>
    </section>
  </div>
</template>
