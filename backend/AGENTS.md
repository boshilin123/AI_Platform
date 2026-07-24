# backend AGENTS.md

本目录实现 FastAPI 模块化单体。除根目录规范外，遵守以下约定。

## 分层

- `router.py`：HTTP 参数、依赖和响应。
- `service.py`：业务编排。
- `repository.py`：数据库查询。
- `schemas.py`：Pydantic 请求和响应。
- `infrastructure/`：外部系统和技术基础设施。
- `scenarios/`：业务场景。

禁止在路由中写 SQL、拼接提示词或直接请求上游模型。禁止在 async 路由中调用同步网络和数据库客户端。

## 依赖与配置

- 配置统一来自 `app/core/config.py`。
- 数据库会话统一通过 `get_db_session`。
- 上游调用统一通过 `LlmClient`。
- 不在 import 阶段读取或输出敏感值。

## 验证

```powershell
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall app
```

接口变更需同步 `docs/api-contract.md` 和测试。
