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
    <section v-if="settings" class="settings-grid settings-primary">
      <article class="panel setting-section">
        <div class="panel-heading"><div><h2>GPT 接口配置</h2><div class="muted">API Key 仅由后端服务读取</div></div><span class="badge success">{{ settings.mockMode || settings.apiKeyConfigured ? "已就绪" : "待配置" }}</span></div>
        <div class="settings-notice">真实 API Key 不进入前端、不写入普通日志，也不通过任何业务接口返回。</div>
        <div class="readonly-fields">
          <label><span>Base URL</span><input :value="settings.baseUrl" readonly /></label>
          <div class="field-pair">
            <label><span>模型名称</span><input :value="settings.model" readonly /></label>
            <label><span>API Key</span><input :value="settings.apiKeyConfigured ? '已在服务端环境变量中配置' : '未配置'" readonly /></label>
          </div>
          <div class="field-pair">
            <label><span>连接超时（秒）</span><input :value="settings.connectTimeoutSeconds" readonly /></label>
            <label><span>读取超时（秒）</span><input :value="settings.readTimeoutSeconds" readonly /></label>
          </div>
        </div>
      </article>
      <article class="panel setting-section">
        <div class="panel-heading"><div><h2>调用策略</h2><div class="muted">不可重试错误直接返回统一错误码</div></div></div>
        <div class="strategy-list">
          <div><span><strong>启用有限重试</strong><small>网络错误、超时、429 与上游 5xx</small></span><span class="toggle on"><i></i></span></div>
          <div><span><strong>记录 Token 用量</strong><small>记录输入、输出与总 Token</small></span><span class="toggle on"><i></i></span></div>
          <div><span><strong>记录审计日志</strong><small>不保存完整敏感业务内容</small></span><span class="toggle on"><i></i></span></div>
          <div><span><strong>内部访问控制</strong><small>{{ settings.internalAuthEnabled ? "内部令牌已启用" : "当前环境未启用内部令牌" }}</small></span><span class="toggle" :class="{ on: settings.internalAuthEnabled }"><i></i></span></div>
        </div>
        <div class="field-pair strategy-fields">
          <label><span>最大重试次数</span><input :value="settings.maxRetries" readonly /></label>
          <label><span>重试间隔</span><input :value="`${settings.retryDelaysSeconds.join(' 秒、')} 秒`" readonly /></label>
        </div>
      </article>
    </section>

    <section v-if="settings" class="settings-subgrid">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">审计策略</span><h2>数据安全</h2></div><span class="toggle on"><i></i></span></div>
        <dl class="definition-list">
          <div><dt>审计日志</dt><dd>已开启</dd></div><div><dt>保留天数</dt><dd>{{ settings.auditRetentionDays }} 天</dd></div>
          <div><dt>原始业务内容</dt><dd>不保存</dd></div><div><dt>内容指纹</dt><dd>SHA-256</dd></div>
        </dl>
      </article>
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">访问控制</span><h2>运行环境</h2></div><span class="toggle" :class="{ on: settings.internalAuthEnabled }"><i></i></span></div>
        <dl class="definition-list">
          <div><dt>环境</dt><dd>{{ settings.environment }}</dd></div><div><dt>运行模式</dt><dd>{{ settings.mockMode ? "模拟模式" : "上游模式" }}</dd></div>
          <div><dt>调用方标识</dt><dd>X-Caller-System</dd></div><div><dt>请求追踪</dt><dd>X-Request-ID</dd></div>
        </dl>
      </article>
    </section>
  </div>
</template>
