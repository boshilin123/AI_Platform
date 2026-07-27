<script setup lang="ts">
import { computed, ref } from "vue";
import { ApiClientError, apiRequest } from "../api/client";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { InterviewKitResult, ResumeParseResult, ScreeningResult } from "../types/api";

type Step = "parse" | "screen" | "interview";
type ParseInputMode = "file" | "text";
const MAX_FILE_BYTES = 10 * 1024 * 1024;

const step = ref<Step>("parse");
const parseInputMode = ref<ParseInputMode>("file");
const resumeText = ref("");
const resumeFile = ref<File | null>(null);
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
const currentStep = computed(() => steps.find((item) => item.key === step.value));

function selectStep(next: Step): void {
  step.value = next;
  result.value = null;
  requestId.value = "";
  error.value = "";
}

function selectParseInputMode(next: ParseInputMode): void {
  parseInputMode.value = next;
  error.value = "";
}

function clearForm(): void {
  resumeText.value = "";
  resumeFile.value = null;
  jobDescription.value = "";
  screeningRisks.value = "";
  result.value = null;
  requestId.value = "";
  error.value = "";
}

function fillExample(): void {
  parseInputMode.value = "text";
  resumeText.value = "姓名：张三\n学校：武汉理工大学\n专业：软件工程\n项目：SmartCampus 智能问答系统，使用 Spring Boot、Milvus、BM25 和大模型实现校园知识库问答，简历中写到问答准确率提升 28%，但未说明评估方法。\n技能：Java、Python、Spring Boot、RAG、Milvus、Docker、Kubernetes。";
  if (needsJob.value) {
    jobDescription.value = "负责企业级 AI 应用和知识库问答系统研发；熟悉 Java 或 Python，掌握 RAG、向量数据库和容器化部署；具备项目指标设计与效果评估经验。";
  }
}

function clearResult(): void {
  result.value = null;
  requestId.value = "";
}

function selectResumeFile(event: Event): void {
  const input = event.target as HTMLInputElement;
  const selected = input.files?.[0] ?? null;
  if (selected && selected.size > MAX_FILE_BYTES) {
    resumeFile.value = null;
    input.value = "";
    error.value = "简历文件不能超过 10MB";
    return;
  }
  resumeFile.value = selected;
  error.value = "";
}

async function submit(): Promise<void> {
  error.value = "";
  result.value = null;
  requestId.value = "";
  const usesFile = step.value === "parse" && parseInputMode.value === "file";
  if (usesFile && !resumeFile.value) {
    error.value = "请选择 PDF 或 DOCX 简历文件";
    return;
  }
  if (!usesFile && resumeText.value.trim().length < 20) {
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
      const response = usesFile
        ? await parseResumeFile(resumeFile.value as File)
        : await apiRequest<ResumeParseResult>("/api/v1/recruitment/resumes/parse", {
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

async function parseResumeFile(file: File) {
  const body = new FormData();
  body.append("file", file);
  return apiRequest<ResumeParseResult>("/api/v1/recruitment/resumes/parse-file", {
    method: "POST",
    body,
  });
}

async function copyResult(): Promise<void> {
  if (result.value) await navigator.clipboard.writeText(JSON.stringify(result.value, null, 2));
}
</script>

<template>
  <div class="stack-lg">
    <section class="flow-tabs" aria-label="招聘助手步骤">
      <button v-for="item in steps" :key="item.key" class="flow-tab" :class="{ active: step === item.key }" type="button" @click="selectStep(item.key)">
        <span class="tab-index">{{ item.index }}</span><span class="tab-name">{{ item.label }}</span>
      </button>
    </section>

    <section class="workspace-grid">
      <form class="panel workspace-card form-panel" @submit.prevent="submit">
        <div class="panel-heading"><div><h2>{{ currentStep?.label }}</h2></div></div>
        <div v-if="step === 'parse'" class="input-mode" aria-label="简历输入方式">
          <button type="button" :class="{ active: parseInputMode === 'file' }" @click="selectParseInputMode('file')">上传文件</button>
          <button type="button" :class="{ active: parseInputMode === 'text' }" @click="selectParseInputMode('text')">粘贴文本</button>
        </div>
        <label v-if="step === 'parse' && parseInputMode === 'file'" class="field">
          <span>简历文件 <em>必填</em></span>
          <input type="file" accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document" @change="selectResumeFile" />
          <small v-if="resumeFile">{{ resumeFile.name }} · {{ (resumeFile.size / 1024).toFixed(1) }} KB</small>
          <small v-else>支持 PDF、DOCX，最大 10MB；扫描版 PDF 暂不支持</small>
        </label>
        <label v-else class="field">
          <span>简历内容 <em>必填</em></span>
          <textarea v-model="resumeText" rows="11" placeholder="粘贴候选人的简历文本。系统不会在审计日志中保存完整内容。"></textarea>
          <small>{{ resumeText.length.toLocaleString() }} / 100,000</small>
        </label>
        <p v-if="step === 'parse' && parseInputMode === 'file'" class="privacy-note">
          文件只用于本次文本提取与人才评估，处理后立即释放，不保存到对象存储或数据库。
        </p>
        <label v-if="needsJob" class="field">
          <span>岗位要求 <em>必填</em></span>
          <textarea v-model="jobDescription" rows="7" placeholder="输入岗位职责、必备技能和经验要求。"></textarea>
        </label>
        <label v-if="step === 'interview'" class="field">
          <span>初筛风险点 <i>可选，每行一项</i></span>
          <textarea v-model="screeningRisks" rows="4" placeholder="例如：项目指标需要进一步验证"></textarea>
        </label>
        <ErrorNotice v-if="error" :message="error" :request-id="requestId" />
        <div class="form-actions">
          <button class="button" type="button" @click="clearForm">清空</button>
          <button class="button" type="button" @click="fillExample">填充示例</button>
          <button class="button primary" type="submit" :disabled="loading">{{ loading ? "AI 正在处理…" : actionLabel }}</button>
        </div>
      </form>

      <article class="panel workspace-card result-panel">
        <div class="panel-heading"><div><h2>返回结果</h2></div></div>
        <div class="result-box">
          <div v-if="result" class="result-tools">
            <button type="button" @click="copyResult">复制</button>
            <button type="button" @click="clearResult">清空</button>
          </div>
          <div v-if="loading" class="processing"><span class="spinner"></span><strong>正在调用 AI 能力</strong><p>完成后将展示经过校验的结构化结果。</p></div>
          <div v-else-if="result">
            <div class="result-meta"><span class="badge success">处理成功</span><span class="mono">{{ requestId }}</span></div>
            <pre class="result-json">{{ JSON.stringify(result, null, 2) }}</pre>
          </div>
          <div v-else class="empty-state"><div class="empty-icon">⌁</div><strong>等待任务提交</strong><p>结果会显示在这里，同时自动写入不含原文的审计记录。</p></div>
        </div>
      </article>
    </section>
  </div>
</template>
