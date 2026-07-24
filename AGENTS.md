# BLUEDOT AI 能力中台 AGENTS.md

本文件是项目级 AI 协作规范。适用于分析、开发、审查、测试、文档和发布工作。

## 1. 项目定位

本项目不是多模型聚合网关。它使用一个服务端 OpenAI 兼容 API Key，为公司业务系统提供可复用 AI 能力。第一阶段只实现招聘助手，但基础调用层和能力层必须允许后续扩展其他业务场景。

## 2. 开始工作前

按顺序读取：

1. 本文件。
2. `AI-chat-history/CURRENT_PROJECT_STATE.md`。
3. `AI-chat-history/INDEX.md`。
4. 当前 Git 状态。
5. 任务目录下更近的 `AGENTS.md`。
6. 任务相关代码、测试和文档。

当前代码是最终事实来源；历史记录只提供上下文。

## 3. 架构边界

- `backend/app/infrastructure/llm/`：上游模型调用、错误映射、重试和流式处理。
- `backend/app/capabilities/`：通用 AI 能力与结构化执行。
- `backend/app/scenarios/`：业务场景编排，目前只有招聘。
- `backend/app/modules/`：工作台、审计、配置和系统接口。
- `frontend/`：管理端，不得持有真实上游 Key。

路由只做 HTTP 边界处理，业务编排放在 service，数据库访问放在 repository，Pydantic 模型放在 schemas。

## 4. 安全

- 不提交或输出真实 API Key、内部 Token、密码和连接串。
- 不记录完整简历、提示词或模型完整响应。
- 不向前端返回 API Key，即使是掩码形式也不返回。
- `caller_system` 必须来自认证后的调用身份或受控请求头，不能作为独立鉴权依据。
- 仓库为公开仓库，所有示例配置必须使用空值或占位符。

## 5. LLM 调用要求

- 只重试网络错误、超时、HTTP 429 和上游 5xx。
- HTTP 400、401、403、模型不存在和内容拒绝不得重试。
- 默认最多重试 2 次，优先遵守 `Retry-After`。
- 结构化格式修复是独立上游调用，不计为传输重试。
- 流式响应开始向客户端输出后，不进行透明重试。
- 每次业务请求和每次真实上游调用都必须可审计。

## 6. 验证

后端修改至少运行：

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall app
```

前端修改至少运行：

```powershell
cd frontend
npm run build
```

配置或部署修改还需执行 Docker Compose 配置检查。最终回复必须说明已验证和未验证内容。

## 7. 禁止事项

- 未经要求不执行 Git 提交、推送、发布或生产操作。
- 不复制 BEAT 参考压缩包中的凭据、环境文件、`.git` 或大体量依赖。
- 不为第一阶段引入 Redis、Celery、MongoDB、Milvus、LangChain 或微服务拆分。
- 不为了局部任务进行全仓格式化、大规模重命名或无关重构。
