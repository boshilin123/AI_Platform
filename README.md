# BLUEDOT AI Agent 中台

基于现有 OpenAI 兼容 API 建设的公司内部统一 AI 服务。平台负责保护上游 API Key，统一处理模型调用、错误与有限重试、Token 用量和审计日志，并以招聘助手作为首个业务场景。

## 当前范围

- 工作台：业务请求、Token、成功率、响应耗时和最近调用。
- 招聘助手：文本或 PDF/DOCX 简历解析、岗位匹配与初筛、面试题生成。
- 调用审计：业务请求和每次真实上游调用的统计。
- 基础配置：管理员可维护受控 Base URL、动态选择当前模型并查看变更审计；不向前端返回真实 API Key。
- 基础调用层：OpenAI 兼容 Chat Completions、有限重试、统一错误和 Token 统计。

暂不包含多模型聚合、知识库、员工通用聊天、额度计费和复杂工作流编排。

## 技术栈

- 后端：FastAPI、Pydantic、HTTPX、SQLAlchemy 2、Alembic。
- 数据库：本地默认 SQLite，部署环境使用 MySQL 8。
- 前端：Vue 3、TypeScript、Vite、Vue Router。
- 部署：Docker Compose、Nginx。

## 目录

```text
backend/          FastAPI 后端
frontend/         Vue 3 管理端
docs/             架构、接口、数据和安全文档
deploy/           Docker Compose 与 Nginx 配置
Prototype/        已确认的 HTML 视觉原型
.codex/skills/    项目级 Codex 工作流
AI-chat-history/  当前状态、索引和重要历史
```

## 本地启动

### 后端

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
Copy-Item ..\.env.example .env
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8080
```

默认开启 `AI_MOCK_MODE=true`，无需真实上游 Key 即可联调招聘流程。接入真实上游时，将 `AI_MOCK_MODE=false` 并通过服务端环境变量设置 `GPTSAPI_API_KEY`。

### 前端

```powershell
cd frontend
npm install
npm run dev
```

前端开发地址默认为 `http://localhost:5173`，Vite 将 `/api` 代理到 `http://localhost:8080`。

### 验证

```powershell
.\scripts\check.ps1
```

## 安全约束

- 真实上游 API Key 只能存在于服务端环境变量或外部 Secret。
- 前端配置接口只返回 `apiKeyConfigured`，不返回任何密钥内容；管理员密码由服务端环境变量注入。
- 简历文件、提取正文和业务结果不持久化；审计仅保存哈希、长度和调用统计。
- 仓库不得提交 `.env`、数据库文件、构建产物和任何真实凭据。

更多信息见 [docs/architecture.md](docs/architecture.md) 和 [docs/security.md](docs/security.md)。
