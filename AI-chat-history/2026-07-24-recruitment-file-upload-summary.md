# 招聘简历文件上传与部署入口阶段记录

> 日期：2026-07-24  
> 范围：招聘文件解析、LLM 审计、前端上传、Compose 统一入口和文档。

## 本次决策

- 第一阶段继续只使用 MySQL；简历原文件、提取正文和招聘业务结果均不持久化，因此不引入 MinIO。
- 新增 `POST /api/v1/recruitment/resumes/parse-file`，支持文本型 PDF 和 DOCX，响应复用文本解析结果。
- 文件只在单次请求内读取并解析。审计保存原文件 SHA-256、字节数及调用统计，不保存文件名、文件内容、提示词或模型完整响应。
- 默认限制为：上传 10MB、PDF 20 页、提取文本 100000 字符、DOCX 解压内容 50MB；扫描版 PDF、图片和 OCR 暂不支持。
- mock 模式不再伪造真实 Token 和上游调用；结构化格式修复是独立上游调用，不计入传输重试。

## 实现结果

- 后端加入 PDF/DOCX 校验和文本提取器、文件错误码、配置项、招聘 service 编排和 multipart 路由。
- LLM 客户端会将 HTTP 200 但响应结构损坏记录为失败上游尝试；失败尝试中的 Token 会汇总到业务审计。
- 前端简历解析支持“上传文件/粘贴文本”切换，multipart 请求不手工设置 JSON Content-Type，浏览器不持有内部 Token。
- Compose 项目名、服务/网络/卷标签、API/Web 健康检查和 `18554` 单一入口已配置；Nginx 同源代理前端、API、Swagger、ReDoc 和 OpenAPI，并在服务端注入内部 Token。
- MySQL 和 FastAPI 不对宿主机暴露端口；Nginx 上传上限默认 11MB，略高于业务文件上限。
- 接口、错误码、架构、安全和部署文档已同步。

## 验证

- 后端：14 项 pytest 全部通过。
- 后端：`compileall app` 通过。
- 前端：TypeScript 检查和 Vite 生产构建通过。
- 部署：`docker compose config` 通过。
- Docker 镜像构建已发起，但 Docker Hub 基础镜像拉取发生网络超时；需在网络正常的部署机重新执行构建。
- 未使用真实 API Key 和真实简历进行测试。

## 后续

1. 在部署机创建不入库的 `deploy/.env`，填写密码、内部 Token 和上游 Key。
2. 网络正常时执行 Compose 构建和启动，确认三个容器均为 healthy。
3. 先用 mock 或虚构简历验证文件接口，再切换真实上游模式测试 Key、Token 与审计统计。
4. 将 `18554` 限制在公司内网/VPN，不直接暴露互联网。
