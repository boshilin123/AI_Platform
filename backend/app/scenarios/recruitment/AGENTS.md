# recruitment AGENTS.md

本模块是第一阶段招聘业务场景。

## 接口

- `POST /api/v1/recruitment/resumes/parse`
- `POST /api/v1/recruitment/screenings/evaluate`
- `POST /api/v1/recruitment/interview-kits/generate`

## 约束

- 招聘接口使用非流式结构化输出。
- 提示词集中在 `prompts.py` 并带版本号。
- 输入和输出使用 Pydantic 严格校验。
- 路由不得直接调用上游。
- 不持久化简历和业务结果；审计只保存哈希和长度。
- 不能将 AI 评分描述为最终录用决定，返回内容必须保留人工复核语义。

修改后验证三个接口、格式修复和审计记录。
