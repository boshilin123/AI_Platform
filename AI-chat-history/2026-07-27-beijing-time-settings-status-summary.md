# 北京时间修复与运行配置状态页调整

## 讨论主题

修复 MySQL 审计时间在浏览器中少 8 小时的问题，并重新明确基础配置页面的只读安全边界和实际用途。

## 关键结论

- 审计记录以 UTC 写入数据库；MySQL `DATETIME` 读取后不保留时区标记，API 曾输出无 `Z/+00:00` 的字符串，浏览器因此将 UTC 数值误当作本地时间。
- API 应始终输出带 UTC 标记的 ISO 8601 时间；前端应显式使用 `Asia/Shanghai` 展示，不能依赖浏览器或宿主机默认时区。
- 工作台“今日”统计应按北京时间自然日计算，而不是 UTC 自然日。
- 基础配置来自服务端环境变量，浏览器不能修改 API Key、内部令牌或运行策略。页面价值是发布核验、故障排查和安全审计，不是配置编辑。
- 原输入框和开关样式产生了可编辑错觉，应改为明确的状态卡片和启用状态标签。

## 完成修改

- `backend/app/modules/audits/service.py` 为 MySQL 返回的无时区时间恢复 UTC 标记，列表和 CSV 导出使用统一时间。
- `backend/app/modules/dashboard/service.py` 将“今日”统计边界调整为北京时间 00:00。
- `frontend/src/utils/datetime.ts` 统一解析历史无时区 UTC 字符串和新带时区字符串，并按北京时间格式化。
- `frontend/src/views/AuditsView.vue` 和 `frontend/src/views/DashboardView.vue` 使用北京时间工具。
- `frontend/src/views/SettingsView.vue` 去除伪输入框和伪开关，改为运行配置状态、策略状态和配置说明。
- `frontend/src/styles/main.css` 增加运行配置卡片、状态标签和说明区域样式。
- `backend/tests/test_api.py` 增加审计列表和工作台时间必须带 UTC 标记的断言。
- `docs/api-contract.md` 明确时间响应的 UTC 标记和北京时间“今日”统计口径。

## 验证

```bash
cd frontend
npm run type-check
npm run build

cd ../backend
python3 -m compileall -q app tests
python3 -m pytest

cd ..
docker compose --env-file deploy/.env.example -f deploy/docker-compose.yml config --quiet
git diff --check
```

- Vue TypeScript 检查通过。
- Vite 生产构建通过。
- Python 编译检查通过。
- Docker Compose 配置解析通过。
- Git 差异空白检查通过。
- pytest 未执行成功：当前宿主机未安装 pytest。

## 当前状态

- 审计列表和工作台图表按北京时间显示。
- API 时间仍以 UTC 作为传输和数据库基准，并明确携带时区信息。
- 基础配置页面不提供浏览器写入，改为说明当前实际生效配置、页面用途、服务器修改入口和部署生效方式。

## 后续

- 在带后端测试依赖的环境中运行 pytest，确认新增时间断言。
- 重新构建 API 和 Web 镜像并更新容器。
- 浏览器检查审计时间、工作台时间轴和基础配置状态页。
- 使用北京时间午夜边界附近的测试记录验证“今日”统计口径。
