<script setup lang="ts">
import { computed, onMounted, reactive, ref } from "vue";
import {
  adminApiRequest,
  apiRequest,
  clearAdminToken,
  readAdminToken,
  saveAdminToken,
} from "../api/client";
import ErrorNotice from "../components/ErrorNotice.vue";
import type {
  AdminOperationAuditList,
  AdminSessionData,
  AdminSessionStatus,
  ModelListData,
  SettingsData,
} from "../types/api";
import { formatBeijingDateTime } from "../utils/datetime";

const settings = ref<SettingsData | null>(null);
const adminSession = ref<AdminSessionStatus | null>(null);
const modelOptions = ref<string[]>([]);
const audits = ref<AdminOperationAuditList | null>(null);
const loginForm = reactive({ username: "", password: "" });
const configurationForm = reactive({ baseUrl: "", model: "" });
const error = ref("");
const success = ref("");
const loading = ref(false);
const modelsLoading = ref(false);
const saving = ref(false);

const isAdmin = computed(() => Boolean(adminSession.value));

function syncConfigurationForm(data: SettingsData): void {
  configurationForm.baseUrl = data.baseUrl;
  configurationForm.model = data.model;
}

async function loadSettings(): Promise<void> {
  settings.value = (await apiRequest<SettingsData>("/api/v1/settings")).data;
  syncConfigurationForm(settings.value);
}

async function restoreAdminSession(): Promise<void> {
  if (!readAdminToken()) return;
  try {
    adminSession.value = (
      await adminApiRequest<AdminSessionStatus>("/api/v1/admin/session")
    ).data;
    await Promise.all([loadModels(false), loadAudits()]);
  } catch {
    clearAdminToken();
    adminSession.value = null;
  }
}

async function login(): Promise<void> {
  loading.value = true;
  error.value = "";
  success.value = "";
  try {
    const response = await apiRequest<AdminSessionData>("/api/v1/admin/login", {
      method: "POST",
      body: JSON.stringify(loginForm),
    });
    saveAdminToken(response.data.accessToken);
    adminSession.value = {
      username: response.data.username,
      expiresAt: response.data.expiresAt,
    };
    loginForm.password = "";
    success.value = "管理员登录成功，现在可以修改全局模型配置。";
    await Promise.all([loadModels(false), loadAudits()]);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "管理员登录失败";
  } finally {
    loading.value = false;
  }
}

async function logout(): Promise<void> {
  try {
    if (readAdminToken()) {
      await adminApiRequest<{ loggedOut: boolean }>("/api/v1/admin/session", {
        method: "DELETE",
      });
    }
  } catch {
    // The local session is cleared even if the server session already expired.
  } finally {
    clearAdminToken();
    adminSession.value = null;
    modelOptions.value = [];
    audits.value = null;
    success.value = "已退出管理员登录。";
  }
}

async function loadModels(showMessage = true): Promise<void> {
  if (!isAdmin.value) return;
  modelsLoading.value = true;
  error.value = "";
  if (showMessage) success.value = "";
  try {
    const query = new URLSearchParams({ baseUrl: configurationForm.baseUrl });
    const data = (
      await adminApiRequest<ModelListData>(`/api/v1/settings/models?${query.toString()}`)
    ).data;
    configurationForm.baseUrl = data.baseUrl;
    modelOptions.value = data.models;
    if (!data.models.includes(configurationForm.model)) {
      configurationForm.model = data.models[0] ?? "";
    }
    if (showMessage) success.value = `已从上游读取 ${data.models.length} 个可用模型。`;
    await loadAudits();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "模型列表读取失败";
  } finally {
    modelsLoading.value = false;
  }
}

async function saveConfiguration(): Promise<void> {
  if (!isAdmin.value) return;
  saving.value = true;
  error.value = "";
  success.value = "";
  try {
    const data = (
      await adminApiRequest<SettingsData>("/api/v1/settings/llm", {
        method: "PUT",
        body: JSON.stringify(configurationForm),
      })
    ).data;
    settings.value = data;
    syncConfigurationForm(data);
    window.dispatchEvent(new Event("runtime-llm-config-updated"));
    success.value = "配置已保存并立即生效，后续 AI 请求将使用新的 Base URL 和模型。";
    await Promise.all([loadModels(false), loadAudits()]);
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "配置保存失败";
    await loadAudits();
  } finally {
    saving.value = false;
  }
}

async function loadAudits(): Promise<void> {
  if (!isAdmin.value) return;
  try {
    audits.value = (
      await adminApiRequest<AdminOperationAuditList>(
        "/api/v1/settings/audits?page=1&pageSize=10",
      )
    ).data;
  } catch (reason) {
    if (!error.value) {
      error.value = reason instanceof Error ? reason.message : "配置审计加载失败";
    }
  }
}

function resetConfiguration(): void {
  if (!settings.value) return;
  syncConfigurationForm(settings.value);
  modelOptions.value = [];
  success.value = "已恢复为当前生效值，尚未保存任何修改。";
}

onMounted(async () => {
  loading.value = true;
  try {
    await loadSettings();
    await restoreAdminSession();
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "基础配置加载失败";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div class="stack-lg">
    <div class="notice">
      <strong>安全配置</strong>
      <span>API Key 始终只由后端环境变量读取；管理员登录后可修改受信任 Base URL 和当前使用模型。</span>
    </div>
    <ErrorNotice v-if="error" :message="error" />
    <div v-if="success" class="notice"><strong>操作完成</strong><span>{{ success }}</span></div>

    <section v-if="settings" class="settings-grid settings-primary">
      <article class="panel setting-section">
        <div class="panel-heading">
          <div><h2>GPT 接口配置</h2><div class="muted">数据库配置保存后立即覆盖环境默认值</div></div>
          <span class="badge success">{{ settings.mockMode || settings.apiKeyConfigured ? "已就绪" : "待配置" }}</span>
        </div>
        <div class="settings-notice">真实 API Key 不进入前端、不写入普通日志，也不通过任何接口返回。Base URL 仅允许服务端允许列表中的 HTTPS 域名。</div>

        <form v-if="isAdmin" class="configuration-form" @submit.prevent="saveConfiguration">
          <label class="field">
            <span>Base URL</span>
            <input
              v-model.trim="configurationForm.baseUrl"
              type="url"
              required
              autocomplete="url"
              placeholder="https://api.example.com/v1"
              @input="modelOptions = []"
            />
          </label>
          <label class="field">
            <span>模型名称</span>
            <select v-model="configurationForm.model" required :disabled="modelsLoading || !modelOptions.length">
              <option v-if="!modelOptions.length" :value="configurationForm.model">
                {{ modelsLoading ? "正在读取模型列表…" : "请先读取可用模型" }}
              </option>
              <option v-for="model in modelOptions" :key="model" :value="model">{{ model }}</option>
            </select>
            <small>招聘助手依赖文本对话和结构化 JSON 输出，建议优先选择 GPT 系列模型。</small>
          </label>
          <div class="configuration-actions">
            <button class="button" type="button" :disabled="modelsLoading" @click="loadModels()">
              {{ modelsLoading ? "读取中" : "读取可用模型" }}
            </button>
            <button class="button" type="button" :disabled="saving" @click="resetConfiguration">恢复当前值</button>
            <button class="button primary" type="submit" :disabled="saving || modelsLoading || !modelOptions.length">
              {{ saving ? "保存中" : "保存并立即生效" }}
            </button>
          </div>
        </form>

        <dl v-else class="runtime-config-list">
          <div class="wide"><dt>Base URL</dt><dd class="mono">{{ settings.baseUrl }}</dd></div>
          <div><dt>模型名称</dt><dd>{{ settings.model }}</dd></div>
          <div><dt>API Key 状态</dt><dd>{{ settings.apiKeyConfigured ? "服务端已配置" : "未配置" }}</dd></div>
          <div><dt>配置来源</dt><dd>{{ settings.configurationSource === "database" ? "数据库运行配置" : "部署环境默认值" }}</dd></div>
          <div><dt>最近修改</dt><dd>{{ settings.updatedAt ? formatBeijingDateTime(settings.updatedAt) : "尚未在页面修改" }}</dd></div>
        </dl>
      </article>

      <article class="panel setting-section">
        <div class="panel-heading">
          <div><h2>管理员验证</h2><div class="muted">只有管理员可以修改全局模型配置</div></div>
          <span class="config-state" :class="{ enabled: isAdmin }">{{ isAdmin ? "已登录" : "未登录" }}</span>
        </div>
        <form v-if="!isAdmin" class="admin-login-form" @submit.prevent="login">
          <div class="settings-notice">
            登录凭据仅发送到同源 API，密码不会写入浏览器存储。登录成功后只保存短期会话令牌。
          </div>
          <label class="field"><span>管理员账号</span><input v-model.trim="loginForm.username" required autocomplete="username" /></label>
          <label class="field"><span>管理员密码</span><input v-model="loginForm.password" type="password" required autocomplete="current-password" /></label>
          <button class="button primary wide" type="submit" :disabled="loading || !settings.adminAuthConfigured">
            {{ loading ? "登录中" : settings.adminAuthConfigured ? "管理员登录" : "服务端尚未配置管理员凭据" }}
          </button>
        </form>
        <div v-else class="admin-session-card">
          <span class="avatar">管</span>
          <div><strong>{{ adminSession?.username }}</strong><small>会话有效至 {{ adminSession ? formatBeijingDateTime(adminSession.expiresAt) : "" }}</small></div>
          <button class="button" type="button" @click="logout">退出登录</button>
        </div>
        <div v-if="isAdmin" class="model-verification-panel">
          <div class="model-verification-heading">
            <span>
              <small>当前生效模型</small>
              <strong>{{ settings.model }}</strong>
            </span>
            <span class="config-state enabled">配置已加载</span>
          </div>
          <h3>如何确认模型真实生效？</h3>
          <ol>
            <li>保存模型配置后，进入招聘助手完成一次 AI 调用。</li>
            <li>记录返回结果对应的 Request ID。</li>
            <li>在调用审计中搜索该 ID，核对“调用模型”是否与当前模型一致。</li>
          </ol>
          <div class="model-verification-actions">
            <RouterLink class="button" to="/recruitment">发起验证调用</RouterLink>
            <RouterLink class="button" to="/audits">查看调用审计</RouterLink>
          </div>
        </div>
      </article>
    </section>

    <section v-if="settings" class="settings-subgrid">
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">调用策略</span><h2>运行参数</h2></div><span class="config-state enabled">服务端控制</span></div>
        <dl class="definition-list">
          <div><dt>连接超时</dt><dd>{{ settings.connectTimeoutSeconds }} 秒</dd></div>
          <div><dt>读取超时</dt><dd>{{ settings.readTimeoutSeconds }} 秒</dd></div>
          <div><dt>最大重试次数</dt><dd>{{ settings.maxRetries }} 次</dd></div>
          <div><dt>重试间隔</dt><dd>{{ settings.retryDelaysSeconds.join(" 秒、") }} 秒</dd></div>
        </dl>
      </article>
      <article class="panel">
        <div class="panel-heading"><div><span class="eyebrow">访问控制</span><h2>运行环境</h2></div><span class="config-state" :class="{ enabled: settings.internalAuthEnabled }">{{ settings.internalAuthEnabled ? "受保护" : "未启用鉴权" }}</span></div>
        <dl class="definition-list">
          <div><dt>环境</dt><dd>{{ settings.environment }}</dd></div>
          <div><dt>运行模式</dt><dd>{{ settings.mockMode ? "模拟模式" : "上游模式" }}</dd></div>
          <div><dt>配置来源</dt><dd>{{ settings.configurationSource === "database" ? "数据库" : "环境变量" }}</dd></div>
          <div><dt>最近修改人</dt><dd>{{ settings.updatedBy ?? "部署配置" }}</dd></div>
        </dl>
      </article>
    </section>

    <section v-if="isAdmin" class="panel table-panel">
      <div class="filter-row">
        <div><span class="eyebrow">管理审计</span><h2 class="settings-audit-title">最近配置操作</h2></div>
        <button class="button" type="button" @click="loadAudits">刷新审计</button>
      </div>
      <div class="table-wrap">
        <table>
          <thead><tr><th>操作</th><th>状态</th><th>操作者</th><th>配置变化</th><th>耗时</th><th>时间</th><th>Request ID</th></tr></thead>
          <tbody>
            <tr v-for="item in audits?.items ?? []" :key="`${item.requestId}-${item.action}-${item.createdAt}`">
              <td>{{ item.action === "settings.llm.update" ? "保存模型配置" : "读取模型列表" }}</td>
              <td><span class="badge" :class="item.status === 'success' ? 'success' : 'danger'">{{ item.status === "success" ? "成功" : "失败" }}</span></td>
              <td>{{ item.actor }}</td>
              <td>
                <span v-if="item.action === 'settings.llm.update'" class="audit-change">
                  {{ item.oldModel ?? "—" }} → {{ item.newModel ?? "—" }}
                </span>
                <span v-else class="mono">{{ item.newBaseUrl }}</span>
              </td>
              <td>{{ item.durationMs }} ms</td>
              <td>{{ formatBeijingDateTime(item.createdAt) }}</td>
              <td class="mono">{{ item.requestId }}</td>
            </tr>
            <tr v-if="!(audits?.items.length)"><td colspan="7">暂无管理操作记录</td></tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>
</template>
