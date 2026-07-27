# Compose 部署成功与 MySQL 认证修复记录

> 日期：2026-07-24  
> 范围：MySQL 8.4、FastAPI、Web 三容器首次完整启动。

## 讨论主题

API 镜像构建完成后，MySQL 容器健康，但 API 在 Alembic 迁移阶段反复退出，导致 Web 无法进入运行状态。

## 根因与决策

- MySQL 8.4 使用 `caching_sha2_password` 认证。
- `asyncmy` 执行该认证时需要 `cryptography`，原后端运行依赖未声明该包。
- 继续使用 MySQL 8.4 默认安全认证方式，不降级为旧认证插件。

## 完成修改

- `backend/pyproject.toml` 增加 `cryptography` 正式运行依赖。
- `backend/Dockerfile` 启用 BuildKit pip 缓存，减少后续慢速 wheel 重复下载。
- `docs/deployment.md` 补充 MySQL 认证依赖和构建缓存说明。

## 验证

- 修复后的 API 镜像构建成功，镜像内安装了 `cryptography`。
- Alembic 首次迁移成功创建审计表。
- MySQL、API、Web 三个容器均进入 healthy。
- 宿主机统一入口健康检查返回成功，数据库状态为 `ok`，LLM 模式为 `upstream`。
- API 和 Web 容器日志中的健康检查持续返回 HTTP 200。

## 风险与后续

- 构建使用的外部 PyPI 下载速度较慢，但 wheel 已进入 BuildKit 缓存。
- 终端日志曾展开上游 API Key，必须在供应商侧轮换。
- 当前 MySQL 密码和内部 Token 若仍为示例占位值，正式使用前必须更换；MySQL 数据卷已初始化后，仅修改 `.env` 不会自动修改库内账号密码。
- 下一步使用虚构简历验证 Swagger 和招聘文件接口，再检查业务审计与 Token 统计。
