# 技术架构

## 总体结构

```text
Vue 管理端 / 内部业务系统
              ↓
        FastAPI HTTP API
              ↓
        业务场景层 scenarios
              ↓
        AI 能力层 capabilities
              ↓
     基础调用层 infrastructure
        ├── llm → /v1/chat/completions
        └── speech → /v1/audio/speech

每次调用同时写入：
ai_request_audit + ai_upstream_attempt
```

## 架构选择

第一阶段采用模块化单体，而不是微服务。招聘、文字转语音、审计、工作台和配置共享一个 FastAPI 进程和数据库，但通过目录和接口边界解耦。文本模型和语音模型共用服务端 API Key 与 Base URL，分别由 `infrastructure/llm` 和 `infrastructure/speech` 调用不同的上游端点。

## 请求生命周期

1. Request ID 中间件生成或接收 `X-Request-ID`。
2. 内部鉴权检查 `X-Internal-Token`，本地未配置时允许开发调用。
3. 场景服务构造业务提示词。
   文件简历会先进行大小、类型和结构校验，再临时提取文本；原文件不持久化。
4. 能力执行器调用 LLM 客户端。
5. LLM 客户端执行错误映射和有限重试。
6. 结构化结果解析失败时最多发起一次格式修复调用。
7. 审计服务写入业务请求和全部上游尝试。
8. API 返回业务结果或统一错误。

每次业务请求通过数据库读取当前运行时 Base URL、文本模型和语音模型；未保存运行时配置时使用服务端环境默认值。管理员保存的新配置无需重启 API 即可供后续请求使用。

## 数据库

本地默认 SQLite，便于启动和测试；部署使用 MySQL 8。Schema 通过 Alembic 维护，不依赖容器首次初始化脚本。

MySQL 只保存调用审计和平台配置类数据。招聘简历原文件、提取正文和结构化业务结果均不持久化，因此第一阶段不需要 MinIO；如果未来出现复用、归档或人工下载原件的明确需求，再单独设计对象存储、授权和生命周期。

运行时配置只保存 Base URL、单一当前文本模型和单一当前语音模型，不构成多模型路由或聚合。模型候选项由后端使用服务端 Key 调用受控上游 `/v1/models` 动态发现，并按能力类型过滤。

## TTS 流式边界

- `infrastructure/speech` 负责打开上游原始音频流、首字节前重试、音频类型与大小校验。
- `capabilities/speech_synthesis` 负责一次业务请求和多次真实分段调用的统一审计。
- `scenarios/tts/text_segmenter.py` 只负责中英文长文本句界切分，不调用网络或数据库。
- `scenarios/tts` 负责非流式二进制与流式 MP3 两种 HTTP 边界。
- 前端通过显式“流式播放”开关选择模式；支持 MediaSource 时渐进追加 MP3，
  否则回退为完整 Blob，不改变后端安全边界。

单次上游语音输入仍限制为 4096 字符。长文本流式请求由场景层拆分，第一段尚未向客户端
输出时可进行有限重试；一旦任何音频字节已发出，后续分段失败只终止流并记录
`AI_STREAM_INTERRUPTED`，不透明重试。
