<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, reactive, ref, watch } from "vue";
import {
  ApiClientError,
  apiRequest,
  startSpeechStream,
  supportsProgressiveMp3,
  synthesizeSpeech,
} from "../api/client";
import ErrorNotice from "../components/ErrorNotice.vue";
import type { SettingsData } from "../types/api";

const SINGLE_REQUEST_MAX_LENGTH = 4096;
const STREAM_MAX_TEXT_LENGTH = 50_000;
const settings = ref<SettingsData | null>(null);
const form = reactive({
  text: "",
  voice: "alloy",
  responseFormat: "mp3" as "mp3" | "wav",
  speed: 1,
  streaming: false,
});
const loading = ref(false);
const streamingPlayback = ref(false);
const browserSupportsStreaming = supportsProgressiveMp3();
const error = ref("");
const audioUrl = ref("");
const audioBlob = ref<Blob | null>(null);
const audioElement = ref<HTMLAudioElement | null>(null);
let streamCancel: (() => void) | null = null;
let generationSequence = 0;
const result = reactive({
  requestId: "",
  model: "",
  voice: "",
  format: "",
  speed: 1,
  segmentCount: 1,
  progressive: false,
});

const voices = [
  { value: "alloy", label: "Alloy（均衡）" },
  { value: "nova", label: "Nova（清晰）" },
  { value: "shimmer", label: "Shimmer（柔和）" },
  { value: "echo", label: "Echo（沉稳）" },
  { value: "onyx", label: "Onyx（厚重）" },
  { value: "fable", label: "Fable（叙述）" },
] as const;

const textLength = computed(() => [...form.text].length);
const activeTextLimit = computed(() => {
  if (form.streaming) {
    return settings.value?.speechMaxStreamChars ?? STREAM_MAX_TEXT_LENGTH;
  }
  return settings.value?.speechMaxInputChars ?? SINGLE_REQUEST_MAX_LENGTH;
});
const canSynthesize = computed(
  () => Boolean(form.text.trim()) && textLength.value <= activeTextLimit.value && !loading.value,
);
const requiresSegmentation = computed(
  () => form.streaming && textLength.value > SINGLE_REQUEST_MAX_LENGTH,
);
const speedDiffersFromResult = computed(
  () => Boolean(audioUrl.value) && Math.abs(Number(form.speed) - result.speed) > 0.001,
);
const playbackRatio = computed(() => {
  if (!result.speed) return 1;
  return Math.min(4, Math.max(0.25, Number(form.speed) / result.speed));
});
const currentAuditionSpeed = computed(() => result.speed * playbackRatio.value);

function syncAudioPlaybackRate(): void {
  if (!audioElement.value) return;
  audioElement.value.playbackRate = playbackRatio.value;
  audioElement.value.defaultPlaybackRate = playbackRatio.value;
}

function releaseAudio(): void {
  streamCancel?.();
  streamCancel = null;
  if (audioUrl.value) URL.revokeObjectURL(audioUrl.value);
  audioUrl.value = "";
  audioBlob.value = null;
  streamingPlayback.value = false;
  result.requestId = "";
  result.model = "";
  result.voice = "";
  result.format = "";
  result.speed = 1;
  result.segmentCount = 1;
  result.progressive = false;
}

function fillSample(): void {
  form.text = `“PTL”是英特尔下一代移动处理器平台“Panther Lake”的缩写。它将是酷睿 Ultra 300 系列，作为你电脑上 Ultra 7 258V，也就是 Lunar Lake 架构的继任者。

简单来说，PTL 平台主要有以下几个特点：

更先进的制造工艺：采用英特尔新一代的 Intel 18A 工艺，能效比有望进一步提升。

全新的核心架构：将采用 Cougar Cove 性能核与 Skymont 能效核的混合架构，核心数最高可达 16 核以上。

更强的集成显卡：集成全新的 Xe3，也就是 Celestial 核显，最高配置将拥有多达 12 个 Xe 核心，图形性能预计会有大幅提升。

更高的 AI 算力：NPU，也就是神经网络处理单元的算力预计将达到 50 TOPS，能为 AI 应用提供更强的本地计算能力。

英特尔通常会用这些缩写来区分不同的处理器平台。就像你电脑上用的 Lunar Lake 被简称为 LNL 一样，PTL 就是 Panther Lake 的官方缩写。搭载该平台的新款笔记本预计将在 2026 年广泛上市。

你看到的 PTL，指的就是即将采用这些新技术的下一代笔记本处理器平台。`;
  error.value = "";
}

function clearAll(): void {
  generationSequence += 1;
  form.text = "";
  error.value = "";
  loading.value = false;
  releaseAudio();
}

function toggleStreaming(): void {
  if (loading.value) return;
  form.streaming = !form.streaming;
  if (form.streaming) form.responseFormat = "mp3";
  error.value = "";
}

async function generate(): Promise<void> {
  if (!canSynthesize.value) return;
  const sequence = ++generationSequence;
  releaseAudio();
  loading.value = true;
  error.value = "";
  try {
    if (form.streaming) {
      const controller = new AbortController();
      streamCancel = () => controller.abort();
      const session = await startSpeechStream({
        text: form.text.trim(),
        voice: form.voice,
        responseFormat: "mp3",
        speed: Number(form.speed),
      }, controller);
      if (sequence !== generationSequence) {
        session.cancel();
        URL.revokeObjectURL(session.audioUrl);
        return;
      }
      streamCancel = session.cancel;
      audioUrl.value = session.audioUrl;
      result.requestId = session.requestId;
      result.model = session.model || settings.value?.speechModel || "";
      result.voice = session.voice;
      result.format = session.format;
      result.speed = session.speed;
      result.segmentCount = session.segmentCount;
      result.progressive = session.progressive;
      streamingPlayback.value = session.progressive;
      await nextTick();
      syncAudioPlaybackRate();
      if (session.progressive) {
        void audioElement.value?.play().catch(() => {
          // Browsers may require the user to press play even after clicking generate.
        });
      }
      const blob = await session.completion;
      if (sequence !== generationSequence) return;
      audioBlob.value = blob;
      streamingPlayback.value = false;
      return;
    }

    const response = await synthesizeSpeech({
      text: form.text.trim(),
      voice: form.voice,
      responseFormat: form.responseFormat,
      speed: Number(form.speed),
    });
    if (sequence !== generationSequence) return;
    audioBlob.value = response.blob;
    audioUrl.value = URL.createObjectURL(response.blob);
    result.requestId = response.requestId;
    result.model = response.model || settings.value?.speechModel || "";
    result.voice = response.voice;
    result.format = response.format;
    result.speed = response.speed;
    result.segmentCount = 1;
    result.progressive = false;
    await nextTick();
    syncAudioPlaybackRate();
  } catch (reason) {
    if (sequence !== generationSequence) return;
    if (reason instanceof DOMException && reason.name === "AbortError") return;
    if (reason instanceof ApiClientError) {
      error.value = reason.requestId
        ? `${reason.message}（Request ID：${reason.requestId}）`
        : reason.message;
    } else {
      error.value = reason instanceof Error ? reason.message : "语音生成失败";
    }
  } finally {
    if (sequence === generationSequence) loading.value = false;
  }
}

function download(): void {
  if (!audioBlob.value) return;
  const downloadUrl = URL.createObjectURL(audioBlob.value);
  const anchor = document.createElement("a");
  anchor.href = downloadUrl;
  anchor.download = `speech-${result.requestId || Date.now()}.${result.format || form.responseFormat}`;
  anchor.click();
  window.setTimeout(() => URL.revokeObjectURL(downloadUrl), 1000);
}

onMounted(async () => {
  try {
    settings.value = (await apiRequest<SettingsData>("/api/v1/settings")).data;
  } catch (reason) {
    error.value = reason instanceof Error ? reason.message : "语音运行配置加载失败";
  }
});

watch(() => Number(form.speed), syncAudioPlaybackRate);
onBeforeUnmount(releaseAudio);
</script>

<template>
  <div class="stack-lg">
    <div class="notice">
      <strong>语音合成</strong>
      <span>
        当前使用服务端语音模型 {{ settings?.speechModel ?? "读取中" }}；输入文本与生成音频仅用于本次请求，不持久化保存。
      </span>
    </div>
    <ErrorNotice v-if="error" :message="error" />

    <section class="workspace-grid tts-workspace">
      <article class="panel workspace-card">
        <div class="panel-heading">
          <div><span class="eyebrow">文字输入</span><h2>生成语音</h2></div>
          <span class="badge success">{{ settings?.speechModel ?? "TTS" }}</span>
        </div>

        <form class="form-panel" @submit.prevent="generate">
          <label class="field">
            <span>合成文本 <em>必填</em></span>
            <textarea
              v-model="form.text"
              :maxlength="activeTextLimit"
              placeholder="请输入需要转换为语音的文字内容"
            ></textarea>
            <small :class="{ 'error-text': textLength > activeTextLimit }">
              {{ textLength.toLocaleString() }} / {{ activeTextLimit.toLocaleString() }} 字符
            </small>
          </label>

          <div class="tts-option-grid">
            <label class="field">
              <span>声音</span>
              <select v-model="form.voice">
                <option v-for="voice in voices" :key="voice.value" :value="voice.value">
                  {{ voice.label }}
                </option>
              </select>
            </label>
            <label class="field">
              <span>输出格式</span>
              <select v-model="form.responseFormat" :disabled="form.streaming">
                <option value="mp3">MP3</option>
                <option value="wav">WAV</option>
              </select>
            </label>
          </div>

          <button
            class="tts-stream-choice"
            :class="{ active: form.streaming }"
            type="button"
            :disabled="loading"
            :aria-pressed="form.streaming"
            @click="toggleStreaming"
          >
            <span class="tts-stream-switch"><i></i></span>
            <span>
              <strong>流式播放</strong>
              <small>
                {{ form.streaming
                  ? "已开启：收到首批 MP3 音频后即可播放"
                  : "未开启：等待完整音频生成后再播放" }}
              </small>
            </span>
          </button>

          <p v-if="requiresSegmentation" class="tts-segment-note">
            当前文本超过单次 4,096 字符限制，系统会按中文或英文句子边界自动分段并连续播放。
          </p>
          <p v-else-if="form.streaming && !browserSupportsStreaming" class="tts-segment-note warning">
            当前浏览器不支持 MP3 渐进播放，将自动回退为完整接收后播放。
          </p>

          <label class="field">
            <span>目标语速：{{ Number(form.speed).toFixed(2) }}×</span>
            <input v-model.number="form.speed" class="speed-slider" type="range" min="0.25" max="4" step="0.05" />
            <small>拖动后立即调整当前试听；重新生成后写入下载音频</small>
          </label>
          <p v-if="speedDiffersFromResult" class="tts-segment-note">
            当前试听已调整为 {{ currentAuditionSpeed.toFixed(2) }}×；现有下载音频仍为
            {{ result.speed.toFixed(2) }}×，点击“重新生成语音”后才会更新。
          </p>

          <p class="privacy-note">
            API Key 仅由后端读取。中文与英文均由语音模型自动识别；流式模式固定使用 MP3。
          </p>

          <div class="form-actions">
            <button class="button" type="button" :disabled="loading" @click="clearAll">清空</button>
            <button class="button" type="button" :disabled="loading" @click="fillSample">填充示例</button>
            <button class="button primary" type="submit" :disabled="!canSynthesize">
              {{ loading ? "正在生成" : speedDiffersFromResult ? "重新生成语音" : "生成语音" }}
            </button>
          </div>
        </form>
      </article>

      <article class="panel workspace-card result-panel">
        <div class="panel-heading">
          <div><span class="eyebrow">音频结果</span><h2>试听与下载</h2></div>
          <button v-if="audioBlob" class="button" type="button" @click="download">下载音频</button>
        </div>
        <div class="tts-result-box">
          <div v-if="audioUrl" class="tts-audio-result">
            <span class="tts-result-icon">
              <svg viewBox="0 0 24 24"><path d="M4 14h3l4 4V6L7 10H4z" /><path d="M15 9c1.7 1.6 1.7 4.4 0 6M18 6c3.4 3.2 3.4 8.8 0 12" /></svg>
            </span>
            <strong>
              {{ streamingPlayback ? "正在流式生成，可边生成边播放" : "语音生成成功" }}
            </strong>
            <p v-if="streamingPlayback" class="tts-stream-status">
              后续音频正在持续写入播放器，请保持当前页面打开。
            </p>
            <audio
              ref="audioElement"
              :src="audioUrl"
              controls
              preload="auto"
              @loadedmetadata="syncAudioPlaybackRate"
            ></audio>
            <dl class="tts-result-meta">
              <div><dt>模型</dt><dd>{{ result.model }}</dd></div>
              <div><dt>声音</dt><dd>{{ result.voice }}</dd></div>
              <div><dt>格式</dt><dd>{{ result.format.toUpperCase() }}</dd></div>
              <div><dt>合成语速</dt><dd>{{ result.speed.toFixed(2) }}×</dd></div>
              <div><dt>播放方式</dt><dd>{{ result.progressive ? "流式" : "完整音频" }}</dd></div>
              <div><dt>分段</dt><dd>{{ result.segmentCount }} 段</dd></div>
              <div><dt>Request ID</dt><dd class="mono">{{ result.requestId }}</dd></div>
            </dl>
          </div>
          <div v-else-if="loading" class="processing">
            <span class="spinner"></span>
            <strong>正在调用语音合成能力</strong>
            <p>{{ form.streaming ? "建立音频流后即可开始播放。" : "完成后可直接试听或下载音频。" }}</p>
          </div>
          <div v-else class="empty-state">
            <span class="empty-icon">♪</span>
            <strong>等待生成语音</strong>
            <p>输入文字并选择声音后，点击“生成语音”。</p>
          </div>
        </div>
      </article>
    </section>
  </div>
</template>
