# 管理员运行时 LLM 配置

## 讨论主题

在不向浏览器暴露 API Key 的前提下，为基础配置页增加管理员登录、受控 Base URL 修改、动态模型选择、数据库持久化和配置变更审计。

## 关键结论

- 管理员账号和密码只由 API 容器环境变量注入，不写入源码、数据库、前端构建产物或历史记录。
- 登录成功后使用随机短期会话令牌；服务端仅在进程内存保存会话，浏览器仅在 `sessionStorage` 保存令牌。
- API Key 继续只从服务端环境变量读取，页面不提供输入、展示或修改能力。
- Base URL 必须使用 HTTPS、443 端口、`/v1` 路径，并精确匹配 `GPTSAPI_ALLOWED_HOSTS`。
- 模型列表由后端使用服务端 Key 请求受控上游 `/models`，配置保存前再次验证模型当前可用。
- MySQL 只保存 Base URL、单一当前模型和修改信息；后续招聘请求按请求读取运行时配置，保存后无需重启 API。
- 模型发现和配置保存使用独立管理操作审计，不计入招聘业务请求数量。

## 完成内容

- 新增管理员登录、会话检查和退出接口。
- 新增运行时 LLM 配置读取、保存、模型发现和管理审计接口。
- 新增 `runtime_llm_configuration` 与 `admin_operation_audit` 模型及 Alembic 迁移。
- 招聘场景和 LLM 客户端改为使用数据库中的当前 Base URL 与模型。
- 基础配置页增加管理员登录、Base URL 输入、模型下拉、立即生效保存、退出登录和最近审计列表。
- 更新环境变量示例、Compose、接口契约、安全、数据库、架构、部署和 README。
- 将 Pydantic 上限固定在兼容 FastAPI 0.115 的 `<2.12`，避免请求模型运行时告警。

## 主要变更路径

- `backend/app/modules/admin/`
- `backend/app/modules/settings/`
- `backend/app/infrastructure/llm/catalog.py`
- `backend/app/infrastructure/llm/client.py`
- `backend/app/scenarios/recruitment/router.py`
- `backend/app/db/models.py`
- `backend/alembic/versions/20260727_002_runtime_llm_configuration.py`
- `frontend/src/views/SettingsView.vue`
- `frontend/src/api/client.ts`
- `deploy/docker-compose.yml`
- `docs/`

## 验证

- 前端 `npm run type-check` 和 `npm run build`：通过。
- Python `compileall`：通过。
- Docker Compose 配置检查：通过（使用非敏感验证凭据补齐必填变量）。
- API 与 Web 镜像构建：通过。
- 最终 API 镜像隔离冒烟测试：管理员登录、未授权拒绝、模型发现、配置保存、受信域名拒绝、审计和退出登录全部通过。
- Alembic 临时 SQLite 升级：`20260727_002 (head)`。
- 一次性 API 容器完整 pytest：15 项全部通过。
- `git diff --check`：通过。

## 当前状态与后续

- 代码、迁移、镜像和测试均完成，但未启动或替换生产容器。
- 生产部署前必须在受 Git 忽略的 `deploy/.env` 增加管理员账号和密码；本次没有把会话中提供的真实密码写入任何仓库文件或工具输出。
- 部署后应登录基础配置页，读取真实上游模型列表，选择模型并保存，再用虚构简历验证新模型调用与两类审计记录。

