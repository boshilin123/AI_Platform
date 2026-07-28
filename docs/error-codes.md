# 错误码

| 错误码 | 是否重试 | 说明 |
| --- | ---: | --- |
| `AI_INVALID_REQUEST` | 否 | 业务参数错误 |
| `AI_UNSUPPORTED_FILE_TYPE` | 否 | 简历扩展名或 MIME 类型不支持 |
| `AI_FILE_TOO_LARGE` | 否 | 文件、PDF 页数或 DOCX 解压内容超过限制 |
| `AI_FILE_CORRUPTED` | 否 | PDF/DOCX 为空、损坏或结构无效 |
| `AI_PDF_ENCRYPTED` | 否 | PDF 需要密码 |
| `AI_RESUME_TEXT_NOT_FOUND` | 否 | 未提取到足够可读文本 |
| `AI_UPSTREAM_AUTH_ERROR` | 否 | 上游认证或权限错误 |
| `AI_MODEL_NOT_FOUND` | 否 | 模型配置错误 |
| `AI_CONTENT_REJECTED` | 否 | 内容被上游拒绝 |
| `AI_UPSTREAM_RATE_LIMIT` | 是 | 上游限流 |
| `AI_UPSTREAM_TIMEOUT` | 是 | 连接或读取超时 |
| `AI_UPSTREAM_UNAVAILABLE` | 是 | 网络错误或上游 5xx |
| `AI_RESPONSE_FORMAT_ERROR` | 否 | 结构化结果修复后仍不合法 |
| `AI_STREAM_INTERRUPTED` | 否 | 流式响应已经开始后中断 |
| `AI_UNAUTHORIZED` | 否 | 内部调用鉴权失败，或管理员会话缺失/失效 |
| `AI_ADMIN_AUTH_NOT_CONFIGURED` | 否 | 服务端尚未配置管理员账号和密码 |
| `AI_INTERNAL_ERROR` | 否 | 未分类内部错误 |

429 优先使用 `Retry-After`。400、401、403 和模型错误不得自动重试。
