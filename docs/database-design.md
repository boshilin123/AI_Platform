# 数据库设计

## ai_request_audit

一条记录代表一次业务请求。

主要字段：

- `request_id`
- `business_code`
- `capability_code`
- `caller_system`
- `interface_path`
- `request_mode`
- `model`
- `status`
- `http_status`
- `error_code`
- `retry_count`
- `upstream_call_count`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `duration_ms`
- `request_content_hash`
- `request_content_length`
- `prompt_version`
- `created_at`

## ai_upstream_attempt

一条记录代表一次真实上游 HTTP 调用。传输重试和格式修复均单独记录。

主要字段：

- `request_id`
- `attempt_no`
- `attempt_type`
- `status`
- `http_status`
- `error_code`
- `retryable`
- `prompt_tokens`
- `completion_tokens`
- `total_tokens`
- `duration_ms`
- `created_at`

## 隐私

两张表均不保存简历原文、岗位原文、完整提示词或完整模型响应。业务结果持久化不属于第一阶段范围。
