<script setup lang="ts">
import { computed, onBeforeUnmount, reactive, ref } from "vue";
import { ApiClientError, apiRequest } from "../api/client";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { InterviewKitResult, ResumeParseResult, ScreeningResult } from "../types/api";

defineOptions({ name: "RecruitmentView" });

type Step = "parse" | "screen" | "interview";
type ParseInputMode = "file" | "text";
const MAX_FILE_BYTES = 10 * 1024 * 1024;
const AI_AGENT_JOB_TEMPLATE = `岗位名称：AI Agent 工程师

岗位职责：
1. 负责企业级 AI Agent 的设计、开发、测试与上线，完成任务规划、工具调用、上下文管理和结构化输出。
2. 对接 OpenAI 兼容模型 API，建设稳定的模型调用、超时重试、错误处理和调用审计能力。
3. 根据业务场景设计 Prompt、Agent 工作流和效果评估方案，持续优化准确率、响应速度与 Token 成本。
4. 与产品、前端及业务团队协作，将 Agent 能力接入实际业务流程。

任职要求：
1. 计算机相关专业，本科及以上学历，具备良好的软件工程基础。
2. 熟练使用 Python，熟悉 FastAPI、关系型数据库、RESTful API 和异步编程。
3. 理解大语言模型、Prompt 设计、Function Calling、Tool Use、RAG 和结构化输出。
4. 熟悉 Docker、Linux 和 Git，具备服务部署、问题排查与自动化测试经验。
5. 具备良好的需求分析、技术沟通和文档编写能力。

加分项：
有 AI Agent、智能助手、知识库问答或模型效果评估项目经验。`;

const step = ref<Step>("parse");
const parseInputMode = ref<ParseInputMode>("file");
const resumeText = ref("");
const resumeFile = ref<File | null>(null);
const jobDescription = ref("");
const screeningRisks = ref("");
const loading = ref(false);
const error = ref("");
const copied = ref(false);
const stepResults = reactive<Record<Step, unknown | null>>({
  parse: null,
  screen: null,
  interview: null,
});
const stepRequestIds = reactive<Record<Step, string>>({
  parse: "",
  screen: "",
  interview: "",
});
let copiedResetTimer: ReturnType<typeof setTimeout> | undefined;

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
const result = computed(() => stepResults[step.value]);
const requestId = computed(() => stepRequestIds[step.value]);
const parsedResumeFallback = computed(() => {
  if (resumeText.value.trim().length >= 20 || !stepResults.parse) return "";
  return JSON.stringify(stepResults.parse, null, 2);
});
const effectiveResumeText = computed(() => resumeText.value.trim() || parsedResumeFallback.value);

function selectStep(next: Step): void {
  step.value = next;
  copied.value = false;
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
  stepResults.parse = null;
  stepResults.screen = null;
  stepResults.interview = null;
  stepRequestIds.parse = "";
  stepRequestIds.screen = "";
  stepRequestIds.interview = "";
  copied.value = false;
  error.value = "";
}

function fillExample(): void {
  parseInputMode.value = "text";
  resumeText.value = "姓名：张三\n学校：武汉理工大学\n专业：软件工程\n项目：SmartCampus 智能问答系统，使用 Spring Boot、Milvus、BM25 和大模型实现校园知识库问答，简历中写到问答准确率提升 28%，但未说明评估方法。\n技能：Java、Python、Spring Boot、RAG、Milvus、Docker、Kubernetes。";
  if (needsJob.value) {
    fillJobTemplate();
  }
}

function fillJobTemplate(): void {
  jobDescription.value = AI_AGENT_JOB_TEMPLATE;
}

function clearResult(): void {
  stepResults[step.value] = null;
  stepRequestIds[step.value] = "";
  copied.value = false;
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
  const activeStep = step.value;
  error.value = "";
  copied.value = false;
  stepResults[activeStep] = null;
  stepRequestIds[activeStep] = "";
  const usesFile = activeStep === "parse" && parseInputMode.value === "file";
  if (usesFile && !resumeFile.value) {
    error.value = "请选择 PDF 或 DOCX 简历文件";
    return;
  }
  if (!usesFile && effectiveResumeText.value.length < 20) {
    error.value = "请至少输入 20 个字符的简历内容";
    return;
  }
  if (needsJob.value && jobDescription.value.trim().length < 20) {
    error.value = "请至少输入 20 个字符的岗位要求";
    return;
  }

  loading.value = true;
  try {
    if (activeStep === "parse") {
      const response = usesFile
        ? await parseResumeFile(resumeFile.value as File)
        : await apiRequest<ResumeParseResult>("/api/v1/recruitment/resumes/parse", {
            method: "POST",
            body: JSON.stringify({ resumeText: resumeText.value }),
          });
      stepResults.parse = response.data;
      stepRequestIds.parse = response.requestId;
    } else if (activeStep === "screen") {
      const response = await apiRequest<ScreeningResult>("/api/v1/recruitment/screenings/evaluate", {
        method: "POST",
        body: JSON.stringify({ resumeText: effectiveResumeText.value, jobDescription: jobDescription.value }),
      });
      stepResults.screen = response.data;
      stepRequestIds.screen = response.requestId;
    } else {
      const response = await apiRequest<InterviewKitResult>("/api/v1/recruitment/interview-kits/generate", {
        method: "POST",
        body: JSON.stringify({
          resumeText: effectiveResumeText.value,
          jobDescription: jobDescription.value,
          screeningRisks: screeningRisks.value.split("\n").map((item) => item.trim()).filter(Boolean),
        }),
      });
      stepResults.interview = response.data;
      stepRequestIds.interview = response.requestId;
    }
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "AI 服务请求失败";
    if (reason instanceof ApiClientError) stepRequestIds[activeStep] = reason.requestId;
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
  if (!result.value) return;
  const content = JSON.stringify(result.value, null, 2);
  try {
    let usedClipboardApi = false;
    if (window.isSecureContext && navigator.clipboard) {
      try {
        await navigator.clipboard.writeText(content);
        usedClipboardApi = true;
      } catch {
        usedClipboardApi = false;
      }
    }
    if (!usedClipboardApi) {
      copyWithTextArea(content);
    }
    copied.value = true;
    if (copiedResetTimer) clearTimeout(copiedResetTimer);
    copiedResetTimer = setTimeout(() => {
      copied.value = false;
    }, 1800);
  } catch {
    error.value = "复制失败，请选中结果文本后手动复制";
  }
}

function copyWithTextArea(content: string): void {
  const textArea = document.createElement("textarea");
  textArea.value = content;
  textArea.setAttribute("readonly", "");
  textArea.style.position = "fixed";
  textArea.style.opacity = "0";
  document.body.appendChild(textArea);
  textArea.select();
  const copiedSuccessfully = document.execCommand("copy");
  document.body.removeChild(textArea);
  if (!copiedSuccessfully) throw new Error("copy command failed");
}

onBeforeUnmount(() => {
  if (copiedResetTimer) clearTimeout(copiedResetTimer);
});
</script>

<template>
  <div class="stack-lg">
    <section class="flow-tabs" aria-label="招聘助手步骤">
      <button v-for="item in steps" :key="item.key" class="flow-tab" :class="{ active: step === item.key }" type="button" :disabled="loading" @click="selectStep(item.key)">
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
          <textarea v-model="resumeText" rows="11" :placeholder="parsedResumeFallback ? '已自动使用步骤一的解析结果；也可以在这里粘贴简历原文进行替换。' : '粘贴候选人的简历文本。系统不会在审计日志中保存完整内容。'"></textarea>
          <small v-if="parsedResumeFallback" class="field-success">✓ 已自动沿用步骤一的简历解析结果</small>
          <small v-else>{{ resumeText.length.toLocaleString() }} / 100,000</small>
        </label>
        <p v-if="step === 'parse' && parseInputMode === 'file'" class="privacy-note">
          文件只用于本次文本提取与人才评估，处理后立即释放，不保存到对象存储或数据库。
        </p>
        <div v-if="needsJob" class="field">
          <div class="field-label-row">
            <span>岗位要求 <em>必填</em></span>
            <button class="template-button" type="button" @click="fillJobTemplate">填入 AI Agent 工程师模板</button>
          </div>
          <textarea v-model="jobDescription" rows="7" placeholder="输入岗位职责、必备技能和经验要求。"></textarea>
        </div>
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
            <button class="copy-button" type="button" :class="{ copied }" :aria-label="copied ? '已复制' : '复制结果'" :title="copied ? '已复制' : '复制'" @click="copyResult">
              <svg v-if="copied" viewBox="0 0 24 24" aria-hidden="true"><path d="m5 12 4 4L19 6" /></svg>
              <span v-else>复制</span>
            </button>
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
