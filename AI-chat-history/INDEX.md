# BLUEDOT AI Agent 中台历史索引

> 更新时间：2026-07-27

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
| 前端视觉与原型 | `Prototype/AI 能力中台.html`、`frontend/src/App.vue`、`frontend/src/styles/main.css` |
| 部署 | `deploy/`、`docs/deployment.md` |

## 日期记录

新增重要架构决策、复杂故障或完整工作阶段后，在此登记：

```text
YYYY-MM-DD-topic-summary.md
```

- `2026-07-24-repository-foundation-summary.md`：正式仓库基础版本、关键决策与验证结果。
- `2026-07-24-recruitment-file-upload-summary.md`：PDF/DOCX 临时解析、审计修正、18554 统一入口与部署验证。
- `2026-07-24-container-registry-mirror-summary.md`：Docker Hub 超时、DaoCloud 镜像代理切换和构建验证。
- `2026-07-24-production-compose-deployment-summary.md`：MySQL 8.4 认证依赖修复、Alembic 迁移和三容器部署成功。
- `2026-07-24-frontend-prototype-alignment-summary.md`：四个前端页面按原型 V2 对齐、公司 Logo 替换与构建验证。
- `2026-07-27-recruitment-ui-interaction-fixes-summary.md`：品牌更名、复制兼容、招聘步骤结果保留和岗位模板。
- `2026-07-27-navigation-pagination-dashboard-summary.md`：招聘任务跨路由保活、审计分页与筛选语义、工作台耗时图坐标轴。
- `2026-07-27-beijing-time-settings-status-summary.md`：MySQL UTC 时区标记、北京时间展示和只读运行配置页面调整。
- `2026-07-27-usage-trend-model-configuration-review-summary.md`：近 7 天 API 调用次数趋势、GPTSAPI 模型发现和安全配置写入边界。
- `2026-07-27-admin-runtime-llm-settings-summary.md`：管理员短期会话、受控 Base URL、动态模型、运行时持久化和管理操作审计。
