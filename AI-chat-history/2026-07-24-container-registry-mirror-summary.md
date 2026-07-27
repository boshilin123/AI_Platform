# 容器镜像代理调整记录

> 日期：2026-07-24  
> 范围：Docker 官方基础镜像拉取故障与 DaoCloud 代理切换。

## 讨论主题

部署机访问 Docker Hub 超时，导致 API 和 Web 镜像无法解析 Python、Node 和 Nginx 基础镜像；MySQL 拉取日志也未形成可用镜像或容器。

## 关键结论

- 所有 Docker 官方基础镜像统一改为通过 `docker.m.daocloud.io` 拉取。
- MySQL 服务的镜像地址同步修改，但不删除或重建已有数据卷。
- 构建日志曾展开敏感上游凭据；该凭据不得写入代码或历史记录，并应在供应商侧轮换。

## 完成修改

- `backend/Dockerfile`：Python 基础镜像切换到 DaoCloud。
- `frontend/Dockerfile`：Node 和 Nginx 基础镜像切换到 DaoCloud。
- `deploy/docker-compose.yml`：MySQL 镜像切换到 DaoCloud。
- `docs/deployment.md`：记录镜像清单和本地 MySQL 镜像复用方式。

## 验证与错误

- `docker compose config --quiet`：通过。
- Python、Node 和 Nginx 基础镜像：通过 DaoCloud 成功解析和拉取。
- Web 镜像：构建成功并导入本地 Docker。
- API 镜像：基础镜像拉取成功；后续 PyPI 依赖下载长时间无进展，验证被人工中止，尚未生成完整 API 镜像。
- 当前 Docker daemon 未发现本项目 MySQL 容器、镜像标签或数据卷，不能将先前的下载进度视为已成功启动。

## 后续

1. 轮换已经出现在终端/聊天日志中的上游 API Key，并只写入不入库的 `deploy/.env`。
2. 重新执行 Compose 构建；若仍停在 Python 包下载，再单独配置受控 PyPI 镜像。
3. 构建成功后执行 `up -d`，等待 MySQL、API 和 Web 均为 healthy。
