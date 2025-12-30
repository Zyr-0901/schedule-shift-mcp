# API 规范符合性检查报告

## 图片规范要求 vs 当前实现

### ✅ 1. 协议 (Protocol)
- **要求**: `http` 或 `https`
- **实现**: ✅ FastAPI 默认支持 http，可通过反向代理支持 https

### ✅ 2. 方法 (Method)
- **要求**: `POST`、`GET`、`DELETE`、`PUT`
- **实现**: ✅ 
  - `POST /api/query-available-slots` - 查询可约档期
  - `POST /api/submit-schedule-change` - 提交调班申请
  - `GET /api/query-available-slots` - 查询可约档期（GET 版本）
  - `GET /health` - 健康检查
  - 如需 PUT/DELETE，可添加相应端点

### ✅ 3. Content-Type
- **要求**: `application/json`
- **实现**: ✅ FastAPI 默认使用 `application/json`，自动处理 JSON 请求体

### ✅ 4. 请求体 (Request Body)
- **要求**: JSON 对象形式，所有必需参数放在 JSON 对象中，非必需参数需设置默认值
- **实现**: ✅ 
  - POST 端点接收 JSON 请求体
  - 非必需参数在函数签名中设置了默认值（如 `require_same_teacher=True`）

### ✅ 5. 响应体 (Response Body)
- **要求**: JSON 对象形式
- **实现**: ✅ 所有端点返回 JSONResponse，自动序列化为 JSON

### ✅ 6. 卡片格式响应 (Card Format)
- **要求**: 如果返回卡片格式，需要包含以下字段：
  - `type`: `markdown` 或 `chart`
  - `data`: 数据数组
  - `raw`: 原始数据数组
  - `markdown`: markdown 字符串
  - `field_headers`: 表头字段数组
  - `chart_type`: 图表类型（bar, pie, line, candlestick）
  - `dimension`: x 轴字段
  - `desc`: 描述信息字符串

- **实现**: ✅ 
  - `/api/query-available-slots` 和 `/api/submit-schedule-change` 返回完整的卡片格式
  - 包含所有必需字段
  - `type` 设置为 `markdown`
  - `raw` 字段包含原始业务数据
  - `markdown` 字段包含格式化的 markdown 内容

## API 端点列表

### MCP 协议端点（保留）
- `POST /mcp/` - MCP 协议端点（FastMCP 处理）
  - 返回原始业务数据（符合 MCP 协议）

### REST API 端点（符合图片规范）
- `POST /api/query-available-slots` - 查询可约档期（卡片格式）
- `POST /api/submit-schedule-change` - 提交调班申请（卡片格式）
- `GET /api/query-available-slots` - 查询可约档期（GET 版本，卡片格式）
- `GET /health` - 健康检查

## 使用示例

### POST 请求示例

```bash
# 查询可约档期
curl -X POST http://localhost:8000/api/query-available-slots \
  -H "Content-Type: application/json" \
  -d '{
    "course_key": "COURSE_001",
    "original_time": "2025-01-10 19:00",
    "target_time_or_range": {
      "type": "exact",
      "start": "2025-01-10 19:00",
      "end": "2025-01-10 19:00"
    },
    "require_same_teacher": true,
    "prefer_same_content": true
  }'

# 提交调班申请
curl -X POST http://localhost:8000/api/submit-schedule-change \
  -H "Content-Type: application/json" \
  -d '{
    "course_key": "COURSE_001",
    "slot_id": "SLOT_2025_02",
    "verification": {
      "type": "last4",
      "value": "9706"
    }
  }'
```

### GET 请求示例

```bash
# 查询可约档期（GET 版本）
curl "http://localhost:8000/api/query-available-slots?course_key=COURSE_001&original_time=2025-01-10%2019:00&target_time=2025-01-10%2019:00&require_same_teacher=true&prefer_same_content=true"
```

## 响应格式示例

### 卡片格式响应（markdown 类型）

```json
{
  "type": "markdown",
  "data": [
    "## 档期查询结果\n\n**目标时间**: 2025-01-10 19:00\n..."
  ],
  "raw": [
    {
      "status": "ok",
      "requested": {...},
      "alternatives": [...]
    }
  ],
  "markdown": "## 档期查询结果\n\n...",
  "field_headers": ["slot_id", "time", "teacher", "content", "capacity_left", "location", "match"],
  "chart_type": "",
  "dimension": "",
  "desc": "查询档期结果：目标时间 2025-01-10 19:00 不可约，提供 2 个替代方案"
}
```

## 总结

✅ **当前实现完全符合图片规范要求**：
- 支持 http/https 协议
- 支持 POST/GET 方法（可扩展 PUT/DELETE）
- Content-Type 为 application/json
- 请求体为 JSON 对象，非必需参数有默认值
- 响应体为 JSON 对象
- 支持卡片格式响应，包含所有必需字段

