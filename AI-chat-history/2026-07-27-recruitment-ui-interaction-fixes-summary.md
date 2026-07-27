# 品牌更名与招聘助手交互修复

## 讨论主题

将产品名称统一为“AI Agent 中台”，并修复工作台状态提示、招聘结果复制、步骤切换结果丢失和岗位要求模板缺失的问题。

## 关键结论

- 当前生产入口通过 HTTP + IP 访问，不能只依赖需要安全上下文的 Clipboard API。
- 简历解析、岗位初筛和面试题生成的返回结果必须按步骤独立保留，切换步骤不应清空已经完成的结果。
- PDF/DOCX 解析后的结构化结果可作为后续初筛和面试题生成的简历输入回退，避免重复解析或重新粘贴。
- 岗位要求模板属于前端便捷填充内容，不修改后端接口结构。

## 完成修改

- 将前端标题、浏览器标题、后端默认服务名称、接口文档和当前项目说明统一改为“AI Agent 中台”。
- 修复平均响应耗时卡片的绿色状态点和文字重叠。
- 结果复制支持 Clipboard API，并在 HTTP 或权限受限时回退到兼容复制方式；成功后按钮短暂显示对号。
- 三个招聘步骤分别保存结果和请求编号，来回切换时保持不变。
- 文件简历的解析结果可以自动用于后续岗位初筛和面试题生成。
- 增加“AI Agent 工程师”岗位要求模板快捷填充。

## 主要文件

- `frontend/src/views/RecruitmentView.vue`
- `frontend/src/styles/main.css`
- `frontend/src/App.vue`
- `frontend/src/router.ts`
- `frontend/index.html`
- `backend/app/core/config.py`
- `backend/app/main.py`
- `docs/api-contract.md`

## 验证

```bash
cd frontend
npm run type-check
npm run build

cd ../backend
python3 -m compileall app
```

- Vue TypeScript 检查通过。
- Vite 生产构建通过。
- Python 编译检查通过。
- `git diff --check` 通过。
- 宿主机没有安装 pytest，因此后端完整测试未在本次运行；本次后端只修改服务名称和错误文案。
- 尚未重建运行中的容器，也尚未在部署地址完成浏览器点击验收。

## 后续

- 重建 `api` 和 `web` 镜像并更新两个容器。
- 在 18554 入口验证绿色状态提示、复制对号、三步骤往返、文件简历结果沿用和岗位模板填充。
