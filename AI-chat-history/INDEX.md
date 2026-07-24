# BLUEDOT AI 能力中台历史索引

> 更新时间：2026-07-24

## 默认读取规则

1. 先读 `CURRENT_PROJECT_STATE.md`。
2. 查看 Git 分支、短提交号和工作区状态。
3. 根据任务只读取相关代码、文档和日期记录。
4. 日期记录代表当时事实；当前代码始终优先。
5. 不在历史文档中保存密钥、密码、简历原文或完整连接串。

## 任务路由

| 任务 | 主要入口 |
| --- | --- |
| 项目定位与架构 | `AGENTS.md`、`docs/architecture.md` |
| GPT 调用、错误和重试 | `backend/app/infrastructure/llm/` |
| Token 与调用审计 | `backend/app/modules/audits/`、`backend/app/db/models.py` |
| 招聘助手 | `backend/app/scenarios/recruitment/`、`frontend/src/views/RecruitmentView.vue` |
| 工作台 | `backend/app/modules/dashboard/`、`frontend/src/views/DashboardView.vue` |
| 基础配置 | `backend/app/modules/settings/`、`frontend/src/views/SettingsView.vue` |
| 部署 | `deploy/`、`docs/deployment.md` |

## 日期记录

新增重要架构决策、复杂故障或完整工作阶段后，在此登记：

```text
YYYY-MM-DD-topic-summary.md
```

- `2026-07-24-repository-foundation-summary.md`：正式仓库基础版本、关键决策与验证结果。
