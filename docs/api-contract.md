# API 契约

基础路径：`/api/v1`

## 系统

```http
GET /system/health
GET /settings
GET /dashboard/overview
```

`GET /settings` 只返回 `apiKeyConfigured`，不会返回 API Key 或掩码。

## 招聘

```http
POST /recruitment/resumes/parse
POST /recruitment/screenings/evaluate
POST /recruitment/interview-kits/generate
```

成功返回：

```json
{
  "success": true,
  "requestId": "ai-20260724-000001",
  "data": {}
}
```

失败返回：

```json
{
  "success": false,
  "requestId": "ai-20260724-000001",
  "error": {
    "code": "AI_UPSTREAM_TIMEOUT",
    "message": "AI 服务响应超时，请稍后重试",
    "retryable": true
  }
}
```

## 审计

```http
GET /audits?page=1&pageSize=20
GET /audits/export
```

支持 `status`、`capabilityCode` 和 `requestId` 筛选。导出格式为 CSV。

## 调用方请求头

```text
X-Request-ID       可选；未提供时由中台生成
X-Caller-System    调用方系统标识
X-Internal-Token   共享环境启用内部鉴权时必填
```
