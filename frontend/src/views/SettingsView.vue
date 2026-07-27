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
    <div class="notice">
      <strong>运行配置状态</strong>
      <span>本页用于核对当前 API 容器实际生效的安全配置。修改请在服务器端维护环境变量并重新部署，浏览器不提供写入能力。</span>
    </div>
    <ErrorNotice v-if="error" :message="error" />
    <section v-if="settings" class="settings-grid settings-primary">
      <article class="panel setting-section">
        <div class="panel-heading"><div><h2>GPT 接口配置</h2><div class="muted">API Key 仅由后端服务读取</div></div><span class="badge success">{{ settings.mockMode || settings.apiKeyConfigured ? "已就绪" : "待配置" }}</span></div>
        <div class="settings-notice">真实 API Key 不进入前端、不写入普通日志，也不通过任何业务接口返回。</div>
        <dl class="runtime-config-list">
          <div class="wide"><dt>Base URL</dt><dd class="mono">{{ settings.baseUrl }}</dd></div>
          <div><dt>模型名称</dt><dd>{{ settings.model }}</dd></div>
          <div><dt>API Key 状态</dt><dd>{{ settings.apiKeyConfigured ? "服务端已配置" : "未配置" }}</dd></div>
          <div><dt>连接超时</dt><dd>{{ settings.connectTimeoutSeconds }} 秒</dd></div>
          <div><dt>读取超时</dt><dd>{{ settings.readTimeoutSeconds }} 秒</dd></div>
        </dl>
      </article>
      <article class="panel setting-section">
        <div class="panel-heading"><div><h2>调用策略</h2><div class="muted">当前服务端实际执行策略</div></div></div>
        <div class="strategy-list">
          <div><span><strong>有限重试</strong><small>网络错误、超时、429 与上游 5xx</small></span><span class="config-state" :class="{ enabled: settings.maxRetries > 0 }">{{ settings.maxRetries > 0 ? "已启用" : "未启用" }}</span></div>
          <div><span><strong>Token 用量记录</strong><small>记录输入、输出与总 Token</small></span><span class="config-state enabled">已启用</span></div>
          <div><span><strong>业务调用审计</strong><small>不保存完整敏感业务内容</small></span><span class="config-state enabled">已启用</span></div>
          <div><span><strong>内部访问控制</strong><small>{{ settings.internalAuthEnabled ? "内部令牌已启用" : "当前环境未启用内部令牌" }}</small></span><span class="config-state" :class="{ enabled: settings.internalAuthEnabled }">{{ settings.internalAuthEnabled ? "已启用" : "未启用" }}</span></div>
        </div>
        <dl class="strategy-values">
          <div><dt>最大重试次数</dt><dd>{{ settings.maxRetries }} 次</dd></div>
          <div><dt>重试间隔</dt><dd>{{ settings.retryDelaysSeconds.join(" 秒、") }} 秒</dd></div>
          <div><dt>流空闲超时</dt><dd>{{ settings.streamIdleTimeoutSeconds }} 秒</dd></div>
        </dl>
      </article>
    </section>

    <section v-if="settings" class="settings-subgrid">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">审计策略</span><h2>数据安全</h2></div><span class="config-state enabled">已启用</span></div>
        <dl class="definition-list">
          <div><dt>审计日志</dt><dd>已开启</dd></div><div><dt>配置保留天数</dt><dd>{{ settings.auditRetentionDays }} 天</dd></div>
          <div><dt>原始业务内容</dt><dd>不保存</dd></div><div><dt>内容指纹</dt><dd>SHA-256</dd></div>
        </dl>
      </article>
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">访问控制</span><h2>运行环境</h2></div><span class="config-state" :class="{ enabled: settings.internalAuthEnabled }">{{ settings.internalAuthEnabled ? "受保护" : "未启用鉴权" }}</span></div>
        <dl class="definition-list">
          <div><dt>环境</dt><dd>{{ settings.environment }}</dd></div><div><dt>运行模式</dt><dd>{{ settings.mockMode ? "模拟模式" : "上游模式" }}</dd></div>
          <div><dt>调用方标识</dt><dd>X-Caller-System</dd></div><div><dt>请求追踪</dt><dd>X-Request-ID</dd></div>
        </dl>
      </article>
    </section>

    <section v-if="settings" class="panel configuration-guide">
      <div>
        <span class="eyebrow">配置说明</span>
        <h2>为什么不能在浏览器中直接修改？</h2>
        <p>模型地址、API Key、超时、重试和内部鉴权属于服务端运行策略。禁止浏览器写入可以避免密钥进入前端状态，并确保配置变更经过部署检查和容器重启。</p>
      </div>
      <div class="configuration-guide-grid">
        <div><strong>页面用途</strong><span>发布后核对实际模型、超时、重试、审计与鉴权状态。</span></div>
        <div><strong>修改入口</strong><span>在服务器受控环境中维护 <code>deploy/.env</code>。</span></div>
        <div><strong>生效方式</strong><span>校验 Compose 配置后重新构建并更新 API 容器。</span></div>
      </div>
    </section>
  </div>
</template>
