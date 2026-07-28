# 文字转语音助手实现总结

## 讨论主题

在现有单一 GPTSAPI 服务端 API Key 和 Base URL 基础上，接入 `tts-1`、`tts-1-hd` 文字转语音能力，同时保持基础设施、通用能力、业务场景和前端页面高内聚、低耦合。

## 关键结论

- 文本模型和语音模型共用服务端凭据与 Base URL，但分别调用 `/chat/completions` 和 `/audio/speech`。
- 运行时配置拆分为单一文本模型与单一语音模型，避免把 TTS 模型误发到聊天接口。
- `/models` 返回值按能力类型过滤；语音模型当前只允许 `tts-1` 和 `tts-1-hd`。
- TTS 成功响应直接返回音频二进制；失败继续使用统一 JSON 错误结构。
- 输入文本和生成音频不持久化，审计只保存哈希、字符数、模型、状态、耗时和上游尝试。

## 完成修改

- 新增 `backend/app/infrastructure/speech/`，实现 OpenAI 兼容 `/audio/speech` 客户端、有限重试、错误映射、音频格式和大小校验及 Mock 客户端。
- 新增 `backend/app/capabilities/speech_synthesis/`，封装可复用合成能力和统一审计。
- 新增 `backend/app/scenarios/tts/` 与 `POST /api/v1/tts/synthesize`。
- 新增迁移 `20260728_003`，持久化 `speech_model` 及配置变更审计前后值。
- 基础配置页面拆分文本模型和语音模型下拉，并从 `/models` 动态读取过滤后的候选项。
- 新增文字转语音前端页面，支持文本输入、六种声音、0.25-4 倍语速、MP3/WAV、试听、下载和 Request ID 展示。
- 工作台和侧边栏增加文字转语音入口；调用审计增加 TTS 能力筛选、音频模式和请求字符数展示。
- 更新接口、架构、数据库、需求和部署配置文档。

## 错误与修正

- 首轮后端测试发现 `request_content_length` 被误加到上游尝试响应结构，导致 TTS 审计列表缺少字符数；已移动到业务审计结构并复测通过。
- 宿主机没有安装 pytest；完整后端测试改在一次性 API 容器中安装开发测试依赖后执行。
- 初次镜像构建因沙箱无法写 Docker buildx 活动目录失败；授权后在沙箱外完成构建。

## 验证

- 后端 Python `compileall`：通过。
- 后端 pytest：20 项全部通过。
- 前端 `npm run type-check`：通过。
- 前端 `npm run build`：通过。
- API 和 Web 镜像构建：通过。
- Docker Compose 配置解析：通过。
- Alembic 在临时 SQLite 数据库从初始版本升级到 `20260728_003 (head)`：通过。
- `git diff --check`：通过。

## 当前状态

代码和部署镜像已具备 TTS 模块，但未替换当前运行中的生产容器，也未使用真实上游 Key 发起付费语音合成。部署时 API 启动会自动执行 Alembic 升级。

## 后续

1. 使用 Compose 重建并替换 API/Web 容器。
2. 管理员进入基础配置读取模型列表，确认文本模型与语音模型分别正确。
3. 使用虚构短文本对 `tts-1` 和 `tts-1-hd` 各做一次真实冒烟测试，核对试听、下载、模型响应头和调用审计。
4. 根据真实使用量再评估长文本分段、音频拼接和字符用量统计面板。
