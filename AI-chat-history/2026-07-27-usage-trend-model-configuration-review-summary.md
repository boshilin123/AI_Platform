# 用量趋势与模型配置评审

## 讨论主题

- 将工作台“近期响应耗时”改为近 7 天 API 调用次数趋势。
- 核实 GPTSAPI 是否只支持当前 `gpt-5.6-luna`，以及 Base URL、模型是否适合在基础配置页编辑。

## 关键结论

- 用量趋势按北京时间自然日统计最近 7 天业务请求次数，并补齐没有调用的日期。
- GPTSAPI 文档提供 OpenAI 兼容的 `/v1/chat/completions`，同时提供带服务端密钥鉴权的 `/v1/models`；模型不应硬编码为唯一选项，后续宜由后端动态读取可用模型。
- API Key 继续只通过服务端环境变量注入，不返回前端，也不在页面中编辑。
- Base URL 不能直接接受任意地址，否则后端的模型发现和调用可能形成 SSRF。后续写入功能至少需要 HTTPS、受控域名或管理员配置的允许列表。
- 当前 Web 入口由 Nginx 为所有浏览器请求注入同一个内部令牌，没有真实管理员身份。因此本阶段不新增配置写接口，避免任何可访问页面的人都能改变全局上游配置。

## 已完成修改

- 审计仓储增加跨数据库兼容的时间区间请求计数。
- 工作台接口增加 `usageTrend`，返回近 7 个北京时间日期及其业务请求次数。
- 前端工作台改为用量面积折线图，展示日期轴、调用次数轴、每日节点和 7 日累计。
- 更新前端类型、接口契约和 API 测试断言。

## 变更文件

- `backend/app/modules/audits/repository.py`
- `backend/app/modules/dashboard/schemas.py`
- `backend/app/modules/dashboard/service.py`
- `backend/tests/test_api.py`
- `frontend/src/views/DashboardView.vue`
- `frontend/src/types/api.ts`
- `frontend/src/styles/main.css`
- `docs/api-contract.md`

## 验证

- `python3 -m compileall -q app tests`：通过。
- `npm run type-check`：通过。
- `npm run build`：通过。
- `docker compose --env-file deploy/.env -f deploy/docker-compose.yml config --quiet`：通过。
- `git diff --check`：通过。
- `python3 -m pytest`：未执行，当前系统 Python 未安装 pytest。

## 当前状态与后续

- 用量趋势代码已完成，尚未执行生产部署或浏览器视觉验收。
- 下一步配置编辑应先明确管理身份边界，再实现安全配置持久化、受控 Base URL 校验、服务端 `/v1/models` 发现、模型下拉选择和配置变更审计。

