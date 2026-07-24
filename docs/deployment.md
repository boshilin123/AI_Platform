# 部署说明

## 本地

本地默认使用 SQLite 和 mock LLM，执行根目录 `scripts/dev.ps1` 可以分别启动后端和前端。

## Docker Compose

部署形态：

```text
ai-platform-web   Nginx + Vue 静态文件
ai-platform-api   FastAPI
ai-platform-db    MySQL 8
```

只对外暴露 Web 端口，Nginx 将 `/api/` 反向代理到后端。数据库和后端默认只走 Docker 内网。

生产环境必须覆盖：

- `GPTSAPI_API_KEY`
- `INTERNAL_API_TOKEN`
- `MYSQL_ROOT_PASSWORD`
- `MYSQL_PASSWORD`
- `APP_CORS_ORIGINS`

部署前运行测试、前端构建和 `docker compose config`。
