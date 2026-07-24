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
        基础调用层 infrastructure/llm
              ↓
   OpenAI 兼容 /v1/chat/completions

每次调用同时写入：
ai_request_audit + ai_upstream_attempt
```

## 架构选择

第一阶段采用模块化单体，而不是微服务。招聘、审计、工作台和配置共享一个 FastAPI 进程和数据库，但通过目录和接口边界解耦。新增业务场景时增加新的 `scenarios/<name>/`，不修改 LLM 基础层。

## 请求生命周期

1. Request ID 中间件生成或接收 `X-Request-ID`。
2. 内部鉴权检查 `X-Internal-Token`，本地未配置时允许开发调用。
3. 场景服务构造业务提示词。
4. 能力执行器调用 LLM 客户端。
5. LLM 客户端执行错误映射和有限重试。
6. 结构化结果解析失败时最多发起一次格式修复调用。
7. 审计服务写入业务请求和全部上游尝试。
8. API 返回业务结果或统一错误。

## 数据库

本地默认 SQLite，便于启动和测试；部署使用 MySQL 8。Schema 通过 Alembic 维护，不依赖容器首次初始化脚本。
