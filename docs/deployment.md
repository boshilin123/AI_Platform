# 部署说明

## 本地

本地默认使用 SQLite 和 mock LLM，执行根目录 `scripts/dev.ps1` 可以分别启动后端和前端。

## Docker Compose

为避免部署服务器访问 Docker Hub 超时，当前官方基础镜像统一通过
`docker.m.daocloud.io` 拉取：

- `docker.m.daocloud.io/python:3.12-slim`
- `docker.m.daocloud.io/node:24-alpine`
- `docker.m.daocloud.io/nginx:1.27-alpine`
- `docker.m.daocloud.io/mysql:8.4`

部署形态：

```text
浏览器
  │
  │ http://<server>:18554
  ▼
bluedot-ai-platform-web   Nginx + Vue 静态文件
  ├── /                     前端
  ├── /docs                 FastAPI Swagger
  ├── /redoc                FastAPI ReDoc
  ├── /openapi.json         OpenAPI Schema
  └── /api/* ─────────────► bluedot-ai-platform-api:8080
                              │
                              ▼
                            bluedot-ai-platform-mysql:3306
```

只对外暴露宿主机 `18554` 端口。Nginx 将 API 和文档请求反向代理到 Docker 内网的 `api:8080`，数据库和 FastAPI 不直接暴露宿主机端口。

部署后访问：

```text
前端：http://<server-ip>:18554/
Swagger：http://<server-ip>:18554/docs
ReDoc：http://<server-ip>:18554/redoc
OpenAPI：http://<server-ip>:18554/openapi.json
健康检查：http://<server-ip>:18554/api/v1/system/health
```

Swagger 页面中的 `Try it out` 请求使用同源 `/api/v1/*` 地址，由 Nginx 转发到内网 API。`INTERNAL_API_TOKEN` 只注入 Nginx 和 FastAPI 容器，不进入 Vue 构建产物或浏览器状态。

`18554` 必须通过服务器防火墙、安全组或 VPN 限制为公司受控网络访问。能访问该端口的用户可以打开 Swagger 并调用内部接口，不应将该端口直接公开到互联网。

Compose 项目名默认为 `bluedot-ai-platform`。容器、网络和数据卷同时带有 `com.bluedot.*` 标签，可通过以下命令筛选：

```bash
docker ps --filter label=com.bluedot.system=ai-platform
docker ps --filter label=com.docker.compose.project=bluedot-ai-platform
```

生产环境必须覆盖：

- `GPTSAPI_API_KEY`
- `GPTSAPI_ALLOWED_HOSTS`，默认只允许 `api.gptsapi.net`
- `INTERNAL_API_TOKEN`
- `ADMIN_USERNAME`
- `ADMIN_PASSWORD`
- `ADMIN_SESSION_TTL_MINUTES`，默认 480 分钟
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `APP_CORS_ORIGINS`
- `WEB_PORT`，当前约定为 `18554`
- `NGINX_CLIENT_MAX_BODY_SIZE`，默认 `11m`，应略大于后端简历上传上限
- `SPEECH_MAX_STREAM_CHARS`，默认 `50000`，限制单次长文本流式任务的总字符数
- `SPEECH_STREAM_FIRST_SEGMENT_CHARS`，默认 `120`，控制流式首段长度以缩短首音频等待
- `SPEECH_STREAM_SEGMENT_CHARS`，默认 `400`，控制首段之后的流式分段长度

首次部署：

```bash
cd /opt/software/AI_Platform
cp deploy/.env.example deploy/.env
chmod 600 deploy/.env
# 使用受控编辑器填写 deploy/.env 中的数据库密码、管理员凭据、
# 内部 Token 和 GPTSAPI_API_KEY

docker compose --env-file deploy/.env -f deploy/docker-compose.yml config
docker compose --env-file deploy/.env -f deploy/docker-compose.yml build --pull
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d
docker compose --env-file deploy/.env -f deploy/docker-compose.yml ps
```

`config` 输出会展开环境变量，其中可能包含敏感值；只在受控终端执行，不要将输出粘贴到工单或聊天记录。`build --pull` 负责构建后端与前端镜像，`up -d` 启动 MySQL、执行 Alembic 迁移，然后启动 API 和 Web。首次启动会创建带项目名前缀的 MySQL 数据卷。

管理员账号和密码只进入 API 容器环境，不写入镜像或数据库。管理页面保存的 Base URL 和模型写入 MySQL；后续更新容器不会清除该配置。若要允许其他 GPTSAPI API 主机，必须先在 `GPTSAPI_ALLOWED_HOSTS` 中以逗号分隔添加精确域名，再重建 API 容器。

后端镜像包含 MySQL 8.4 `caching_sha2_password` 认证所需的 `cryptography` 运行依赖。构建使用 BuildKit pip 缓存；第一次下载仍可能较慢，后续重建可以复用已下载的 wheel。

Nginx 的 `/api/` 代理已关闭 `proxy_buffering`，并保留较长读取超时，使 TTS 音频块可以直接转发到浏览器。不要在外层网关重新开启响应缓冲，否则前端虽然选择“流式播放”，仍会等待完整音频后才收到数据。

镜像源调整不会删除或重建 `bluedot-ai-platform_mysql-data` 数据卷。若服务器已经存在
`mysql:8.4`，可先执行下面的命令为同一个本地镜像增加代理仓库标签，避免重复下载：

```bash
docker image inspect mysql:8.4 >/dev/null 2>&1 \
  && docker tag mysql:8.4 docker.m.daocloud.io/mysql:8.4
```

部署后调试顺序：

1. 执行 `curl -fsS http://127.0.0.1:18554/api/v1/system/health`，确认 API 和数据库正常。
2. 访问 `/docs`，使用 Swagger 调用非敏感测试数据。
3. 查看 `docker compose --env-file deploy/.env -f deploy/docker-compose.yml logs --tail=200 api`，按响应中的 `X-Request-ID` 定位请求。
4. 在调用审计页面核对业务请求、上游次数、Token、重试和耗时。
5. 不在终端、截图、工单或日志中输出真实 API Key、内部 Token 或真实简历内容。

部署完成后，Swagger 适合内部联调和故障定位，不替代自动化测试，也不用于提交真实候选人数据进行随意测试。

日常更新：

```bash
cd /opt/software/AI_Platform
git pull --ff-only
docker compose --env-file deploy/.env -f deploy/docker-compose.yml config
docker compose --env-file deploy/.env -f deploy/docker-compose.yml up -d --build
docker compose --env-file deploy/.env -f deploy/docker-compose.yml ps
```

停止服务但保留 MySQL 数据：

```bash
docker compose --env-file deploy/.env -f deploy/docker-compose.yml down
```

不要对正式环境执行 `down -v`，该命令会删除 MySQL 数据卷。
