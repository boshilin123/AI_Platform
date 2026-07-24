# 错误码

| 错误码 | 是否重试 | 说明 |
| --- | ---: | --- |
| `AI_INVALID_REQUEST` | 否 | 业务参数错误 |
| `AI_UPSTREAM_AUTH_ERROR` | 否 | 上游认证或权限错误 |
| `AI_MODEL_NOT_FOUND` | 否 | 模型配置错误 |
| `AI_CONTENT_REJECTED` | 否 | 内容被上游拒绝 |
| `AI_UPSTREAM_RATE_LIMIT` | 是 | 上游限流 |
| `AI_UPSTREAM_TIMEOUT` | 是 | 连接或读取超时 |
| `AI_UPSTREAM_UNAVAILABLE` | 是 | 网络错误或上游 5xx |
| `AI_RESPONSE_FORMAT_ERROR` | 否 | 结构化结果修复后仍不合法 |
| `AI_STREAM_INTERRUPTED` | 否 | 流式响应已经开始后中断 |
| `AI_UNAUTHORIZED` | 否 | 内部调用鉴权失败 |
| `AI_INTERNAL_ERROR` | 否 | 未分类内部错误 |

429 优先使用 `Retry-After`。400、401、403 和模型错误不得自动重试。
