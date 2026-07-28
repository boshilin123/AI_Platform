# BLUEDOT AI Agent 中台当前项目状态

> 更新时间：2026-07-28
> 用途：新会话先读取本文件，再按 `INDEX.md` 定向补充历史。若内容与代码冲突，以当前代码为准。

## 项目定位

项目基于一个服务端 OpenAI 兼容 API Key，向公司内部业务提供统一 AI 服务。它不做多模型聚合。当前已实现招聘助手和文字转语音助手。

## 技术基线

- 后端：FastAPI 模块化单体。
- 数据访问：SQLAlchemy 2 异步模式；本地 SQLite，部署 MySQL 8。
- 上游调用：HTTPX 调用 OpenAI 兼容 `/v1/chat/completions` 和 `/v1/audio/speech`。
- 前端：Vue 3 + TypeScript + Vite。
- 项目协作：根目录和模块级 `AGENTS.md`、`.codex/skills/`、`AI-chat-history/`。

## 当前范围

- 简历文本解析，以及文本型 PDF/DOCX 的单次请求临时解析。
- 岗位匹配与初筛。
- 面试题生成。
- 业务请求审计与上游调用明细。
- Token 用量、成功率和耗时统计。
- 管理员受控的运行时 Base URL、单一文本模型和单一语音模型配置。
- 基础层支持非流式和流式调用；招聘接口使用非流式结构化输出。
- 文字转语音助手，支持 `tts-1`、`tts-1-hd`、多声音、语速、MP3/WAV、试听和下载。

## 明确不做

- 多模型聚合和切换。
- RAG、向量数据库和知识库。
- 员工通用聊天。
- 用户自助创建 Key、配额和计费。
- Redis、Celery 和复杂工作流编排。

## 安全基线

- 真实上游 Key 只由后端环境变量读取。
- 前端不显示或修改 API Key。
- 审计日志不保存完整简历、提示词和模型响应。
- 简历文件、提取正文和招聘业务结果不持久化，当前不需要 MinIO。
- 示例配置不包含真实凭据。

## 读取入口

- 架构：`docs/architecture.md`
- 接口：`docs/api-contract.md`
- 数据库：`docs/database-design.md`
- 错误码：`docs/error-codes.md`
- 安全：`docs/security.md`
- 招聘后端：`backend/app/scenarios/recruitment/`
- LLM 调用：`backend/app/infrastructure/llm/`
- 审计：`backend/app/modules/audits/`
- 前端：`frontend/src/`

## 当前完成度

首个可运行基础版本、招聘简历文件上传和前端原型对齐已经完成。后端接口、前端管理端、审计链路、数据库迁移、容器部署和项目协作文件均已落入仓库。详细记录见 `2026-07-24-repository-foundation-summary.md`、`2026-07-24-recruitment-file-upload-summary.md` 和 `2026-07-24-frontend-prototype-alignment-summary.md`。

当前本地验证状态：

- FastAPI 测试：29 项全部通过。
- Vue TypeScript 检查与生产构建：通过。
- 浏览器联调：工作台、简历解析、调用审计通过。
- Docker Compose 配置解析：通过。
- Docker 官方基础镜像已统一切换到 `docker.m.daocloud.io`。
- Web 和 API 镜像构建成功；MySQL、API、Web 三容器均已 healthy。
- MySQL 8.4 认证所需的 `cryptography` 已加入后端运行依赖，Alembic 首次迁移成功。
- 统一入口健康检查通过，数据库状态为 `ok`，当前为真实上游模式。
- 工作台、招聘助手、调用审计和基础配置已按 `Prototype/AI 能力中台.html` 重新实现视觉结构，并替换为公司球形 Logo；前端构建通过，尚待重建 Web 容器后进行最终浏览器视觉验收。
- 产品展示名称已统一为“AI Agent 中台”。
- 招聘助手按步骤保留结果和请求编号，文件简历解析结果可供后续步骤沿用；结果复制兼容 HTTP 页面，并提供 AI Agent 工程师岗位要求模板。
- 招聘助手页面已支持跨侧边栏路由保活；调用审计默认每页 10 条并展示总页数；工作台已展示按北京时间自然日汇总的近 7 天 API 调用次数趋势和累计用量。
- 审计时间响应已补齐 UTC 标记并由前端统一按北京时间显示，工作台“今日”统计按北京时间自然日计算。
- 基础配置已支持管理员短期会话、受信任 Base URL 修改、服务端 `/v1/models` 动态模型选择、MySQL 持久化和管理操作审计；API Key 仍只允许服务端环境变量注入。
- 文本模型与语音模型已拆分配置并共用服务端凭据；语音调用使用独立 `/v1/audio/speech` 客户端，不再进入聊天接口。
- 新增文字转语音助手、`POST /api/v1/tts/synthesize`、二进制音频响应、试听下载和字符数审计。
- 新增 `speech_model` 及配置审计字段，迁移版本更新为 `20260728_003`。
- `runtime_llm_configuration` 和 `admin_operation_audit` 已扩展语音模型字段；运行时配置保存后立即供后续文本和语音请求使用。
- API 和 Web 最终镜像构建、隔离配置冒烟测试、Alembic 升级及 20 项 pytest 已通过，尚未替换生产容器。
- 真实上游 TTS 性能测试已完成：`tts-1`/`tts-1-hd` RTF 为 0.179-0.313，首字节为 1.332-3.118 秒，上游使用 chunked 音频传输。
- 新增用户可选的 TTS 流式 MP3 播放；支持 MediaSource 时边收边播，不支持时回退完整音频。
- 新增最多 50000 字符的流式长文本入口，按中英文自然句界拆成不超过 4096 字符的真实上游调用，一次业务审计关联全部分段调用。
- 流式首字节发出后不再透明重试；后续分段错误和浏览器断连记录为流中断。
- TTS 语速已区分即时试听与文件合成语速：拖动滑块立即调整当前播放器，重新生成后所选语速写入下载音频；真实上游 0.5× 与 2.3× 时长对比验证通过。

下一项工作应是部署 API/Web 新镜像，并使用虚构中英文短文本及超过 4096 字符的长文本做真实浏览器流式冒烟测试，同时继续轮换已暴露的上游 Key。真实 Key 只能在仓库外通过环境变量注入。
