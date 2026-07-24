# BLUEDOT AI 能力中台当前项目状态

> 更新时间：2026-07-24  
> 用途：新会话先读取本文件，再按 `INDEX.md` 定向补充历史。若内容与代码冲突，以当前代码为准。

## 项目定位

项目基于一个服务端 OpenAI 兼容 API Key，向公司内部业务提供统一 AI 服务。它不做多模型聚合。第一阶段业务场景为招聘助手。

## 技术基线

- 后端：FastAPI 模块化单体。
- 数据访问：SQLAlchemy 2 异步模式；本地 SQLite，部署 MySQL 8。
- 上游调用：HTTPX 调用 OpenAI 兼容 `/v1/chat/completions`。
- 前端：Vue 3 + TypeScript + Vite。
- 项目协作：根目录和模块级 `AGENTS.md`、`.codex/skills/`、`AI-chat-history/`。

## 第一阶段范围

- 简历解析。
- 岗位匹配与初筛。
- 面试题生成。
- 业务请求审计与上游调用明细。
- Token 用量、成功率和耗时统计。
- 安全的运行配置展示。
- 基础层支持非流式和流式调用；招聘接口使用非流式结构化输出。

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

首个可运行基础版本已经完成。后端接口、前端管理端、审计链路、数据库迁移、容器部署和项目协作文件均已落入仓库。详细记录见 `2026-07-24-repository-foundation-summary.md`。

当前本地验证状态：

- FastAPI 测试：5 项全部通过。
- Vue TypeScript 检查与生产构建：通过。
- 浏览器联调：工作台、简历解析、调用审计通过。
- Docker Compose 配置解析：通过；尚未在本机实际构建镜像。

下一项业务工作应是真实上游环境联调，真实 Key 只能在仓库外通过环境变量注入。
