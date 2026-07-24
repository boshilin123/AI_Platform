<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiClientError, apiRequest } from "../api/client";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { InterviewKitResult, ResumeParseResult, ScreeningResult } from "../types/api";

type Step = "parse" | "screen" | "interview";
const step = ref<Step>("parse");
const resumeText = ref("");
const jobDescription = ref("");
const screeningRisks = ref("");
const loading = ref(false);
const result = ref<unknown>(null);
const requestId = ref("");
const error = ref("");

const steps: Array<{ key: Step; index: string; label: string; description: string }> = [
  { key: "parse", index: "01", label: "简历解析", description: "提取候选人核心信息" },
  { key: "screen", index: "02", label: "岗位初筛", description: "分析岗位匹配程度" },
  { key: "interview", index: "03", label: "面试题生成", description: "生成针对性问题" },
];

const needsJob = computed(() => step.value !== "parse");
const actionLabel = computed(() => ({
  parse: "开始解析",
  screen: "开始评估",
  interview: "生成面试题",
})[step.value]);

function selectStep(next: Step): void {
  step.value = next;
  result.value = null;
  requestId.value = "";
  error.value = "";
}

async function submit(): Promise<void> {
  error.value = "";
  result.value = null;
  requestId.value = "";
  if (resumeText.value.trim().length < 20) {
    error.value = "请至少输入 20 个字符的简历内容";
    return;
  }
  if (needsJob.value && jobDescription.value.trim().length < 20) {
    error.value = "请至少输入 20 个字符的岗位要求";
    return;
  }

  loading.value = true;
  try {
    if (step.value === "parse") {
      const response = await apiRequest<ResumeParseResult>("/api/v1/recruitment/resumes/parse", {
        method: "POST",
        body: JSON.stringify({ resumeText: resumeText.value }),
      });
      result.value = response.data;
      requestId.value = response.requestId;
    } else if (step.value === "screen") {
      const response = await apiRequest<ScreeningResult>("/api/v1/recruitment/screenings/evaluate", {
        method: "POST",
        body: JSON.stringify({ resumeText: resumeText.value, jobDescription: jobDescription.value }),
      });
      result.value = response.data;
      requestId.value = response.requestId;
    } else {
      const response = await apiRequest<InterviewKitResult>("/api/v1/recruitment/interview-kits/generate", {
        method: "POST",
        body: JSON.stringify({
          resumeText: resumeText.value,
          jobDescription: jobDescription.value,
          screeningRisks: screeningRisks.value.split("\n").map((item) => item.trim()).filter(Boolean),
        }),
      });
      result.value = response.data;
      requestId.value = response.requestId;
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "AI 服务请求失败";
    if (reason instanceof ApiClientError) requestId.value = reason.requestId;
  } finally {
    loading.value = false;
  }
}

async function copyResult(): Promise<void> {
  if (result.value) await navigator.clipboard.writeText(JSON.stringify(result.value, null, 2));
}
</script>

<template>
  <div class="stack-lg">
    <section class="step-grid" aria-label="招聘助手步骤">
      <button v-for="item in steps" :key="item.key" class="step-card" :class="{ active: step === item.key }" type="button" @click="selectStep(item.key)">
        <span class="step-index">{{ item.index }}</span><strong>{{ item.label }}</strong><small>{{ item.description }}</small>
      </button>
    </section>

    <section class="workspace-grid">
      <form class="panel form-panel" @submit.prevent="submit">
        <div class="panel-heading">
          <div><span class="eyebrow">当前任务</span><h2>{{ steps.find((item) => item.key === step)?.label }}</h2></div>
        </div>
        <label class="field">
          <span>简历内容 <em>必填</em></span>
          <textarea v-model="resumeText" rows="11" placeholder="粘贴候选人的简历文本。系统不会在审计日志中保存完整内容。"></textarea>
          <small>{{ resumeText.length.toLocaleString() }} / 100,000</small>
        </label>
        <label v-if="needsJob" class="field">
          <span>岗位要求 <em>必填</em></span>
          <textarea v-model="jobDescription" rows="7" placeholder="输入岗位职责、必备技能和经验要求。"></textarea>
        </label>
        <label v-if="step === 'interview'" class="field">
          <span>初筛风险点 <i>可选，每行一项</i></span>
          <textarea v-model="screeningRisks" rows="4" placeholder="例如：项目指标需要进一步验证"></textarea>
        </label>
        <ErrorNotice v-if="error" :message="error" :request-id="requestId" />
        <button class="button primary wide" type="submit" :disabled="loading">
          {{ loading ? "AI 正在处理…" : actionLabel }}
        </button>
      </form>

      <article class="panel result-panel">
        <div class="panel-heading">
          <div><span class="eyebrow">处理结果</span><h2>结构化输出</h2></div>
          <button v-if="result" class="button ghost" type="button" @click="copyResult">复制结果</button>
        </div>
        <div v-if="loading" class="processing"><span class="spinner"></span><strong>正在调用 AI 能力</strong><p>完成后将展示经过校验的结构化结果。</p></div>
        <div v-else-if="result" class="result-content">
          <div class="result-meta"><span class="badge success">处理成功</span><span class="mono">{{ requestId }}</span></div>
          <pre>{{ JSON.stringify(result, null, 2) }}</pre>
        </div>
        <div v-else class="empty-state result-empty"><div class="empty-icon">⌁</div><strong>等待任务提交</strong><p>结果会显示在这里，同时自动写入不含原文的审计记录。</p></div>
      </article>
    </section>
  </div>
</template>
