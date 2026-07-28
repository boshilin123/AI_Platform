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

## runtime_llm_configuration

单例记录，保存管理员最近一次确认的非敏感运行配置：

- `base_url`
- `model`
- `speech_model`
- `updated_by`
- `updated_at`

真实 API Key 不进入该表。数据库配置仅在仍满足当前服务端域名允许列表时生效，否则回退到环境默认值。

## admin_operation_audit

记录模型发现与配置保存操作：

- `request_id`
- `actor`
- `action`
- `status`
- `http_status`
- `error_code`
- `duration_ms`
- `old_base_url` / `new_base_url`
- `old_model` / `new_model`
- `old_speech_model` / `new_speech_model`
- `created_at`

该表不保存管理员密码、会话令牌、API Key 或上游模型列表正文。
