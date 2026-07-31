# BLUEDOT AI Agent 中台接口文档

> 文档版本：0.1.0
>
> 最后更新：2026-07-27
>
> 维护原则：接口路由、请求字段、响应字段、状态码或鉴权方式发生变化时，必须在同一次修改中更新本文档。当前代码是最终事实来源。

## 1. 接口概览

### 1.1 基础信息

| 项目 | 说明 |
| --- | --- |
| 服务名称 | BLUEDOT AI Agent 中台 |
| API 基础路径 | `/api/v1` |
| 默认本地地址 | `http://127.0.0.1:8080` |
| 部署统一入口 | `http://<server-ip>:18554` |
| 部署前端 | `http://<server-ip>:18554/` |
| 部署 Swagger UI | `http://<server-ip>:18554/docs` |
| 部署 OpenAPI JSON | `http://<server-ip>:18554/openapi.json` |
| 请求与响应命名 | JSON 字段使用 `camelCase` |
| 招聘接口模式 | 非流式、结构化 JSON 输出 |
| 字符编码 | UTF-8 |

### 1.2 当前接口目录

| 类别 | 方法 | 路径 | 内部鉴权 | 状态 |
| --- | --- | --- | --- | --- |
| 系统 | GET | `/api/v1/system/health` | 否 | 已实现 |
| 工作台 | GET | `/api/v1/dashboard/overview` | 是 | 已实现 |
| 招聘助手 | POST | `/api/v1/recruitment/resumes/parse` | 是 | 已实现 |
| 招聘助手 | POST | `/api/v1/recruitment/resumes/parse-file` | 是 | 已实现 |
| 招聘助手 | POST | `/api/v1/recruitment/screenings/evaluate` | 是 | 已实现 |
| 招聘助手 | POST | `/api/v1/recruitment/interview-kits/generate` | 是 | 已实现 |
| 文字转语音 | POST | `/api/v1/tts/synthesize` | 是 | 已实现 |
| 流式文字转语音 | POST | `/api/v1/tts/synthesize-stream` | 是 | 已实现 |
| 调用审计 | GET | `/api/v1/audits` | 是 | 已实现 |
| 调用审计 | GET | `/api/v1/audits/export` | 是 | 已实现 |
| 管理员认证 | POST | `/api/v1/admin/login` | 是 | 已实现 |
| 管理员认证 | GET/DELETE | `/api/v1/admin/session` | 是 + 管理员 | 已实现 |
| 基础配置 | GET | `/api/v1/settings` | 是 | 已实现 |
| 基础配置 | GET | `/api/v1/settings/models` | 是 + 管理员 | 已实现 |
| 基础配置 | PUT | `/api/v1/settings/llm` | 是 + 管理员 | 已实现 |
| 基础配置 | GET | `/api/v1/settings/audits` | 是 + 管理员 | 已实现 |

## 2. 通用约定

### 2.1 请求头

| 请求头 | 必填 | 适用范围 | 说明 |
| --- | --- | --- | --- |
| `Content-Type` | POST 请求必填 | 业务接口 | 文本和语音请求使用 `application/json`；文件接口使用 `multipart/form-data` |
| `X-Request-ID` | 否 | 全部接口 | 调用方请求编号，最长使用前 96 个字符；未提供时由服务生成 |
| `X-Internal-Token` | 视环境而定 | 除健康检查外 | 服务端配置后必填；部署管理端由 Nginx 注入，其他内部调用方自行传递 |
| `X-Caller-System` | 否 | 招聘助手 | 调用方系统标识，最长使用前 64 个字符；默认 `ai-platform-web` |
| `Authorization: Bearer <admin-session>` | 管理写操作必填 | 管理员会话、模型发现、配置保存和配置审计 | 通过管理员登录获取的短期会话令牌 |

所有响应都包含 `X-Request-ID` 响应头。

`X-Caller-System` 只用于审计归属，不应被当作独立鉴权凭证。共享和生产环境必须通过受控身份或内部鉴权确定调用方。

### 2.2 成功响应

除 CSV 导出和 TTS 音频二进制响应外，成功响应统一使用：

```json
{
  "success": true,
  "requestId": "ai-0123456789abcdef",
  "data": {}
}
```

### 2.3 失败响应

```json
{
  "success": false,
  "requestId": "ai-0123456789abcdef",
  "error": {
    "code": "AI_UPSTREAM_TIMEOUT",
    "message": "AI 服务响应超时，请稍后重试",
    "retryable": true
  }
}
```

### 2.4 常见 HTTP 状态码

| HTTP 状态 | 说明 |
| ---: | --- |
| 200 | 请求成功 |
| 400 | 请求被上游拒绝或业务请求不合法 |
| 401 | 内部调用鉴权失败，或管理员会话缺失/失效 |
| 422 | FastAPI/Pydantic 请求参数校验失败，使用统一错误响应 |
| 413 | 简历文件、PDF 页数或 DOCX 解压内容超过限制 |
| 415 | 简历文件类型或 MIME 类型不受支持 |
| 500 | 未分类内部错误 |
| 502 | 上游认证、模型、响应格式或其他上游错误 |
| 503 | 上游限流、网络错误或服务不可用 |
| 504 | 上游调用超时 |

完整错误码及重试语义见 [error-codes.md](error-codes.md)。

### 2.5 隐私与审计

- 真实上游 API Key 不进入请求、响应、前端状态和普通日志。
- 招聘业务结果只返回给调用方，当前不持久化。
- 审计只保存请求内容的 SHA-256、长度、能力编号、Token、耗时和状态。
- 审计不保存完整简历、岗位说明、提示词或模型完整响应。
- 一次业务请求产生一条业务审计；重试和格式修复分别计入上游调用次数。

## 3. 系统接口

### 3.1 健康检查

```http
GET /api/v1/system/health
```

用于检查 API 进程和数据库连接。该接口不要求 `X-Internal-Token`。

注意：`llmMode=upstream` 只表示当前配置为真实上游模式，不代表健康检查执行了真实模型请求。

成功响应：

```json
{
  "success": true,
  "requestId": "ai-0123456789abcdef",
  "data": {
    "status": "ok",
    "service": "BLUEDOT AI Agent 中台",
    "environment": "development",
    "database": "ok",
    "llmMode": "mock"
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `status` | string | 服务状态，当前成功时为 `ok` |
| `service` | string | 服务名称 |
| `environment` | string | 当前运行环境 |
| `database` | string | 数据库检查状态 |
| `llmMode` | string | `mock` 或 `upstream` |

## 4. 工作台接口

### 4.1 获取工作台概览

```http
GET /api/v1/dashboard/overview
```

今日指标的统计范围为北京时间当日 00:00 至当前时间；用量趋势返回按北京时间自然日汇总的近 7 天业务请求次数；最近调用返回最新 5 条业务审计。

成功响应：

```json
{
  "success": true,
  "requestId": "ai-0123456789abcdef",
  "data": {
    "stats": {
      "businessRequests": 3,
      "upstreamCalls": 4,
      "totalTokens": 1520,
      "successRate": 100.0,
      "retryCount": 0,
      "averageDurationMs": 3200
    },
    "usageTrend": [
      {
        "date": "2026-07-18",
        "requestCount": 0
      },
      {
        "date": "2026-07-24",
        "requestCount": 3
      }
    ],
    "recentRequests": [],
    "generatedAt": "2026-07-24T08:00:00Z"
  }
}
```

统计字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `businessRequests` | integer | 业务请求数量 |
| `upstreamCalls` | integer | 上游调用总数，包含传输重试和格式修复 |
| `totalTokens` | integer | 输入与输出 Token 总数 |
| `successRate` | number | 业务请求成功率，范围 0-100 |
| `retryCount` | integer | 传输重试总数，不包含格式修复 |
| `averageDurationMs` | integer | 业务请求平均耗时，单位毫秒 |
| `usageTrend` | UsageTrendPoint[] | 按北京时间自然日汇总的近 7 天业务请求次数，包含无调用日期 |
| `usageTrend[].date` | date | 北京时间日期，格式 `YYYY-MM-DD` |
| `usageTrend[].requestCount` | integer | 当天业务请求次数 |
| `recentRequests` | AuditItem[] | 最新 5 条业务审计，字段见 6.1 |
| `generatedAt` | datetime | 统计生成时间，ISO 8601 |

## 5. 招聘助手接口

招聘接口均使用非流式结构化输出。AI 评分与建议只用于辅助人工判断，不代表自动录用决定。

### 5.1 简历文本解析

```http
POST /api/v1/recruitment/resumes/parse
Content-Type: application/json
```

能力编号：`recruitment.resume.parse`

请求字段：

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `resumeText` | string | 是 | 20-100000 字符 | 简历文本 |

请求示例：

```json
{
  "resumeText": "候选人示例，软件工程专业，熟悉 Python、FastAPI 和 SQL，参与过内部数据分析服务开发。"
}
```

成功响应：

```json
{
  "success": true,
  "requestId": "ai-0123456789abcdef",
  "data": {
    "name": "候选人示例",
    "school": null,
    "major": "软件工程",
    "graduationTime": null,
    "skills": [
      "Python",
      "FastAPI",
      "SQL"
    ],
    "projects": [
      {
        "name": "内部数据分析服务",
        "summary": "参与接口开发与测试",
        "technologies": [
          "Python",
          "FastAPI"
        ],
        "risks": [
          "项目规模和个人职责需要人工核实"
        ]
      }
    ]
  }
}
```

响应字段：

| 字段 | 类型 | 可为空 | 说明 |
| --- | --- | --- | --- |
| `name` | string | 是 | 候选人姓名 |
| `school` | string | 是 | 学校 |
| `major` | string | 是 | 专业 |
| `graduationTime` | string | 是 | 毕业时间 |
| `skills` | string[] | 否 | 技能列表 |
| `projects` | ProjectExperience[] | 否 | 项目经历 |
| `projects[].name` | string | 否 | 项目名称 |
| `projects[].summary` | string | 否 | 项目摘要 |
| `projects[].technologies` | string[] | 否 | 项目技术 |
| `projects[].risks` | string[] | 否 | 需人工核实的风险 |

### 5.2 岗位匹配与初筛

```http
POST /api/v1/recruitment/screenings/evaluate
Content-Type: application/json
```

能力编号：`recruitment.screening.evaluate`

请求字段：

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `resumeText` | string | 是 | 20-100000 字符 | 简历文本 |
| `jobDescription` | string | 是 | 20-50000 字符 | 岗位职责与要求 |

请求示例：

```json
{
  "resumeText": "候选人示例，熟悉 Python、FastAPI 和 SQL，参与过内部数据分析服务开发。",
  "jobDescription": "招聘 AI 应用开发工程师，要求熟悉 Python、接口开发、关系数据库和自动化测试。"
}
```

成功响应：

```json
{
  "success": true,
  "requestId": "ai-0123456789abcdef",
  "data": {
    "matchScore": 82,
    "recommendation": "建议进入人工面试",
    "confidence": 0.86,
    "strengths": [
      "技术方向与岗位要求匹配"
    ],
    "risks": [
      "实际项目职责需要核实"
    ],
    "interviewFocus": [
      "项目职责边界",
      "接口稳定性设计"
    ],
    "finalComment": "建议由面试官结合项目细节进行人工复核。"
  }
}
```

响应字段：

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `matchScore` | integer | 0-100 | 岗位匹配分 |
| `recommendation` | string | - | 辅助建议 |
| `confidence` | number | 0-1 | 模型对结果的置信度 |
| `strengths` | string[] | - | 匹配优势 |
| `risks` | string[] | - | 风险和待核实点 |
| `interviewFocus` | string[] | - | 建议面试关注点 |
| `finalComment` | string | - | 人工复核导向的总结 |

### 5.3 面试题生成

```http
POST /api/v1/recruitment/interview-kits/generate
Content-Type: application/json
```

能力编号：`recruitment.interview-kit.generate`

请求字段：

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `resumeText` | string | 是 | 20-100000 字符 | 简历文本 |
| `jobDescription` | string | 是 | 20-50000 字符 | 岗位职责与要求 |
| `screeningRisks` | string[] | 否 | 最多 30 项 | 初筛阶段发现的风险点 |

请求示例：

```json
{
  "resumeText": "候选人示例，熟悉 Python、FastAPI 和 SQL，参与过内部数据分析服务开发。",
  "jobDescription": "招聘 AI 应用开发工程师，要求熟悉 Python、接口开发、关系数据库和自动化测试。",
  "screeningRisks": [
    "项目规模和个人职责需要核实"
  ]
}
```

成功响应：

```json
{
  "success": true,
  "requestId": "ai-0123456789abcdef",
  "data": {
    "questions": [
      {
        "type": "项目验真",
        "question": "请说明你在项目中独立负责的模块以及主要技术决策。",
        "purpose": "核实项目职责边界"
      }
    ]
  }
}
```

响应字段：

| 字段 | 类型 | 约束 | 说明 |
| --- | --- | --- | --- |
| `questions` | InterviewQuestion[] | 1-30 项 | 面试题列表 |
| `questions[].type` | string | - | 题目类别 |
| `questions[].question` | string | - | 面试问题 |
| `questions[].purpose` | string | - | 出题目的 |

### 5.4 简历文件解析

```http
POST /api/v1/recruitment/resumes/parse-file
Content-Type: multipart/form-data
```

能力编号：`recruitment.resume.parse`

请求字段：

| 字段 | 类型 | 必填 | 约束 | 说明 |
| --- | --- | --- | --- | --- |
| `file` | binary | 是 | 最大 10MB | 文本型 PDF 或 DOCX 简历 |

默认安全限制：

- PDF 最多 20 页；加密 PDF、扫描版 PDF、图片简历和 OCR 暂不支持。
- DOCX 必须是合法的 Office Open XML 文档，不接受含宏文件；解压后总大小最多 50MB。
- 提取文本最多向模型提交 100000 字符，超出部分截断。
- 文件仅在本次请求中读取并提取文本，请求完成后释放，不写入 MySQL 或对象存储。
- 审计保存原文件 SHA-256 和字节数，不保存文件名、原文件或提取正文。
- 成功响应与 5.1 的 `ResumeParseResult` 完全相同。

示例：

```bash
curl -X POST "http://<server-ip>:18554/api/v1/recruitment/resumes/parse-file" \
  -H "X-Caller-System: recruitment-test" \
  -F "file=@./candidate.docx"
```

文件接口特有错误：

| HTTP | 错误码 | 说明 |
| ---: | --- | --- |
| 413 | `AI_FILE_TOO_LARGE` | 文件字节数、PDF 页数或 DOCX 解压大小超过限制 |
| 415 | `AI_UNSUPPORTED_FILE_TYPE` | 扩展名或 MIME 类型不支持/不匹配 |
| 422 | `AI_FILE_CORRUPTED` | 文件为空、签名或内部结构损坏 |
| 422 | `AI_PDF_ENCRYPTED` | PDF 需要密码 |
| 422 | `AI_RESUME_TEXT_NOT_FOUND` | 未提取到足够文本，常见于扫描版 PDF |

## 6. 文字转语音接口

### 6.1 合成语音

```http
POST /api/v1/tts/synthesize
Content-Type: application/json
```

能力编号：`tts.speech.synthesize`

请求：

```json
{
  "text": "欢迎使用 BLUEDOT AI Agent 中台。",
  "voice": "alloy",
  "responseFormat": "mp3",
  "speed": 1.0
}
```

约束：

- `text`：1-4096 字符。
- `voice`：`alloy`、`echo`、`fable`、`onyx`、`nova`、`shimmer`。
- `responseFormat`：`mp3` 或 `wav`。
- `speed`：0.25-4.0。

成功时直接返回音频二进制，并通过响应头返回 `X-Request-ID`、`X-Audio-Model`、
`X-Audio-Voice`、`X-Audio-Format` 和 `X-Audio-Speed`。`X-Audio-Speed` 表示生成该
音频时实际提交的合成语速。失败时仍返回统一 JSON 错误结构。输入文本和音频不持久化；
审计只保存文本哈希、字符数、模型、状态、耗时和上游尝试。

### 6.2 流式合成与长文本

```http
POST /api/v1/tts/synthesize-stream
Content-Type: application/json
```

请求字段与非流式接口相同，但 `responseFormat` 必须为 `mp3`。接口使用原始 MP3
字节流而不是 SSE；响应不提供 `Content-Length`，收到首批音频后即可开始播放。

约束和行为：

- `text`：1-50000 字符。
- 单次上游 Speech 请求仍不超过 4096 字符。
- 为降低首批音频等待时间，默认将第一段控制在 120 字符以内，后续段控制在
  400 字符以内；两项均可通过部署配置调整，但不会超过单次上游请求上限。
- 服务端优先按中文 `。！？；`、英文 `.?!;` 和换行拆分，
  其次按逗号、冒号或英文单词空格拆分，最后才按安全字符长度截段。
- 中文和英文使用同一声音与语速连续播放，不改变或翻译原文。
- 第一段在尚未输出音频前允许按统一策略重试；任何音频字节发出后不再透明重试。
- 每次流式请求只产生一条业务审计，每个实际分段请求和重试均产生独立上游调用明细。
- 浏览器不支持 MP3 MediaSource 时，前端自动回退为完整接收后播放。

除通用音频响应头外，流式接口还返回：

| 响应头 | 说明 |
| --- | --- |
| `X-Audio-Streaming` | 固定为 `true` |
| `X-Audio-Segments` | 本次文本拆分后的上游语音段数 |
| `X-Audio-Speed` | 生成音频时提交的合成语速 |
| `Cache-Control` | 固定为 `no-store` |

## 7. 调用审计接口

### 7.1 分页查询业务审计

```http
GET /api/v1/audits
```

查询参数：

| 参数 | 类型 | 必填 | 默认值 | 约束 | 说明 |
| --- | --- | --- | --- | --- | --- |
| `page` | integer | 否 | 1 | >= 1 | 页码 |
| `pageSize` | integer | 否 | 20 | 1-100 | 每页数量 |
| `status` | string | 否 | - | 建议 `success`/`failed` | 精确匹配业务状态 |
| `capabilityCode` | string | 否 | - | - | 精确匹配能力编号 |
| `requestId` | string | 否 | - | - | 当前实现为包含匹配 |

请求示例：

```http
GET /api/v1/audits?page=1&pageSize=20&status=success&capabilityCode=recruitment.resume.parse
```

成功响应：

```json
{
  "success": true,
  "requestId": "ai-query-request-id",
  "data": {
    "items": [
      {
        "requestId": "ai-business-request-id",
        "businessCode": "recruitment",
        "capabilityCode": "recruitment.resume.parse",
        "callerSystem": "ai-platform-web",
        "interfacePath": "/api/v1/recruitment/resumes/parse",
        "requestMode": "non_stream",
        "model": "gpt-5.6-luna",
        "status": "success",
        "httpStatus": 200,
        "errorCode": null,
        "retryCount": 0,
        "upstreamCallCount": 1,
        "promptTokens": 320,
        "completionTokens": 180,
        "totalTokens": 500,
        "requestContentLength": 1200,
        "durationMs": 3200,
        "promptVersion": "v1.0",
        "createdAt": "2026-07-24T08:00:00Z"
      }
    ],
    "page": 1,
    "pageSize": 20,
    "total": 1
  }
}
```

`AuditItem` 字段：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `requestId` | string | 业务请求编号 |
| `businessCode` | string | 业务编号，如 `recruitment` 或 `tts` |
| `capabilityCode` | string | 能力编号 |
| `callerSystem` | string | 调用方系统 |
| `interfacePath` | string | 业务接口路径 |
| `requestMode` | string | `non_stream`、`stream` 或非流式 TTS 使用的 `binary` |
| `model` | string | 实际或配置模型 |
| `status` | string | `success` 或 `failed` |
| `httpStatus` | integer | 业务响应 HTTP 状态 |
| `errorCode` | string/null | 失败错误码 |
| `retryCount` | integer | 传输重试次数 |
| `upstreamCallCount` | integer | 上游调用次数，包含重试和格式修复 |
| `promptTokens` | integer | 输入 Token |
| `completionTokens` | integer | 输出 Token |
| `totalTokens` | integer | Token 总数 |
| `requestContentLength` | integer | 请求内容字符数；TTS 用量以该字段展示 |
| `durationMs` | integer | 业务请求耗时，单位毫秒 |
| `promptVersion` | string | Prompt 版本 |
| `createdAt` | datetime | 创建时间，ISO 8601 UTC，响应始终包含 `Z` 或 `+00:00` 时区标记 |

当前列表接口不返回完整请求、内容哈希、提示词、模型响应或上游尝试明细。

### 7.2 导出业务审计

```http
GET /api/v1/audits/export
```

查询参数：

| 参数 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| `status` | string | 否 | 精确匹配业务状态 |
| `capabilityCode` | string | 否 | 精确匹配能力编号 |

响应：

```text
Content-Type: text/csv; charset=utf-8
Content-Disposition: attachment; filename="ai-audits.csv"
```

导出最多返回最新 5000 条记录，CSV 包含 UTF-8 BOM。CSV 列：

```text
Request ID
业务
能力
调用方
状态
错误码
上游调用
重试
Token
请求字符数
耗时(ms)
时间
```

CSV 不包含 API Key、内部 Token、请求原文、完整提示词或模型响应。

## 8. 基础配置接口

### 8.1 查询安全运行配置

```http
GET /api/v1/settings
```

该接口可由管理页面只读调用。API Key 仅返回是否已配置；Base URL 和模型返回当前实际生效值。数据库运行配置优先于环境默认值。

成功响应：

```json
{
  "success": true,
  "requestId": "ai-0123456789abcdef",
  "data": {
    "environment": "development",
    "mockMode": true,
    "apiKeyConfigured": false,
    "baseUrl": "https://api.gptsapi.net/v1",
    "model": "gpt-5.6-luna",
    "speechModel": "tts-1",
    "connectTimeoutSeconds": 10,
    "readTimeoutSeconds": 120,
    "streamIdleTimeoutSeconds": 30,
    "maxRetries": 2,
    "retryDelaysSeconds": [
      1,
      2
    ],
    "speechMaxInputChars": 4096,
    "speechMaxStreamChars": 50000,
    "auditRetentionDays": 90,
    "internalAuthEnabled": true,
    "adminAuthConfigured": true,
    "configurationSource": "database",
    "updatedBy": "platform-admin",
    "updatedAt": "2026-07-27T08:00:00Z"
  }
}
```

字段说明：

| 字段 | 类型 | 说明 |
| --- | --- | --- |
| `environment` | string | 运行环境 |
| `mockMode` | boolean | 是否使用模拟模型 |
| `apiKeyConfigured` | boolean | 服务端是否配置上游 Key |
| `baseUrl` | string | 上游基础地址，不包含 Key |
| `model` | string | 当前文本模型 |
| `speechModel` | string | 当前语音模型 |
| `connectTimeoutSeconds` | number | 连接超时 |
| `readTimeoutSeconds` | number | 非流式读取超时 |
| `streamIdleTimeoutSeconds` | number | 流空闲超时 |
| `maxRetries` | integer | 最大传输重试次数 |
| `retryDelaysSeconds` | number[] | 默认重试等待时间 |
| `auditRetentionDays` | integer | 配置的审计保留天数 |
| `internalAuthEnabled` | boolean | 是否启用内部令牌校验 |
| `adminAuthConfigured` | boolean | 服务端是否已配置管理员账号和密码 |
| `configurationSource` | string | `environment` 或 `database` |
| `updatedBy` | string/null | 最近通过管理页面修改配置的管理员 |
| `updatedAt` | datetime/null | 最近配置修改时间，UTC |

接口永远不会返回真实 API Key、掩码 Key 或内部 Token。

### 8.2 管理员登录

```http
POST /api/v1/admin/login
Content-Type: application/json
```

请求：

```json
{
  "username": "platform-admin",
  "password": "由部署环境配置的密码"
}
```

成功后返回 `username`、`accessToken` 和 `expiresAt`。密码不持久化到浏览器；管理端只在 `sessionStorage` 保存短期会话令牌。API 进程重启、主动退出或会话过期后需要重新登录。

```http
GET /api/v1/admin/session
Authorization: Bearer <admin-session>

DELETE /api/v1/admin/session
Authorization: Bearer <admin-session>
```

### 8.3 获取上游可用模型

```http
GET /api/v1/settings/models?baseUrl=https%3A%2F%2Fapi.gptsapi.net%2Fv1
Authorization: Bearer <admin-session>
```

后端使用服务端 API Key 请求受控 Base URL 的 `/models`，返回原始模型 ID，并分别提供过滤后的 `chatModels` 与 `speechModels`。Base URL 必须满足：

- 使用 HTTPS。
- 端口为 443 或省略。
- 主机名精确匹配 `GPTSAPI_ALLOWED_HOSTS`。
- 路径以 `/v1` 结尾。
- 不包含用户名、密码、查询参数、片段或路径回退。

模型发现的成功或失败都会写入 `admin_operation_audit`，但不计入招聘业务请求数量。

### 8.4 保存运行时 AI 配置

```http
PUT /api/v1/settings/llm
Authorization: Bearer <admin-session>
Content-Type: application/json
```

请求：

```json
{
  "baseUrl": "https://api.gptsapi.net/v1",
  "model": "gpt-5.6-luna",
  "speechModel": "tts-1"
}
```

保存前后端会重新获取模型列表，确认文本模型属于对话能力且语音模型为 `tts-1` 或 `tts-1-hd`。成功后 Base URL、文本模型和语音模型写入 MySQL 并立即用于后续请求，无需重启 API。API Key、超时、重试和鉴权配置仍只允许通过服务端环境变量维护。

### 8.5 查询管理操作审计

```http
GET /api/v1/settings/audits?page=1&pageSize=10
Authorization: Bearer <admin-session>
```

返回模型发现和配置保存操作，包含操作者、Request ID、状态、错误码、耗时、配置前后值和时间。审计记录不包含 API Key、管理员密码、管理员会话令牌或模型列表响应全文。

## 9. 能力编号

| 业务 | 能力编号 | 对应接口 |
| --- | --- | --- |
| 招聘 | `recruitment.resume.parse` | `/recruitment/resumes/parse`、`/recruitment/resumes/parse-file` |
| 招聘 | `recruitment.screening.evaluate` | `/recruitment/screenings/evaluate` |
| 招聘 | `recruitment.interview-kit.generate` | `/recruitment/interview-kits/generate` |
| 文字转语音 | `tts.speech.synthesize` | `/tts/synthesize`、`/tts/synthesize-stream` |

## 10. 文档维护清单

发生以下变化时必须同步更新本文档：

- 新增、删除或重命名路由。
- 修改 HTTP 方法、路径、请求头或鉴权方式。
- 修改请求/响应 Schema、字段约束或字段含义。
- 修改状态码、错误码或重试语义。
- 修改审计字段、导出列或统计口径。
- 将“规划中”接口正式实现。

接口实现完成但本文档未同步更新时，不应将该接口视为可交付状态。
