# 测试指南

## 连通性测试

### 1. 健康检查

```bash
curl http://localhost:8000/health
```

预期返回：
```json
{"status": "OK"}
```

### 2. API 文档端点

**重要**：FastAPI 的文档端点在主应用根路径下，**不在** `/mcp/` 路径下。

```bash
# Swagger UI 文档（浏览器访问）
http://localhost:8000/docs

# OpenAPI JSON Schema
curl http://localhost:8000/openapi.json

# ReDoc 文档（浏览器访问）
http://localhost:8000/redoc
```

**错误示例**（这些会返回 404）：
```bash
# ❌ 这些路径不存在
curl http://localhost:8000/mcp/docs
curl http://localhost:8000/mcp/openapi.json
```

**原因**：FastMCP 的 `http_app()` 返回的 ASGI 应用只处理 MCP 协议请求，不包含 FastAPI 的文档功能。

### 3. MCP 协议端点

MCP 协议端点用于 MCP 客户端连接：

```bash
# MCP 端点（用于 MCP 客户端连接）
# 注意：这是 MCP 协议端点，不是 REST API
http://localhost:8000/mcp/
```

### 4. REST API 端点（卡片格式）

#### 查询可约档期

```bash
# POST 方法
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

# GET 方法
curl "http://localhost:8000/api/query-available-slots?course_key=COURSE_001&original_time=2025-01-10%2019:00&target_time=2025-01-10%2019:00&require_same_teacher=true&prefer_same_content=true"
```

#### 提交调班申请

```bash
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

## 常见问题

### Q: 为什么 `/mcp/docs` 返回 404？

**A**: FastMCP 的 `http_app()` 返回的 ASGI 应用只处理 MCP 协议请求，不包含 FastAPI 的文档功能。文档端点应该访问主应用的 `/docs` 和 `/openapi.json`。

### Q: 如何测试 MCP 协议端点？

**A**: MCP 协议端点（`/mcp/`）需要使用支持 MCP 协议的客户端连接，不能直接用 curl 测试。可以使用：
- Claude Desktop（配置 MCP 服务器）
- LangChain MCPHttpServer
- 其他支持 MCP 协议的客户端

### Q: REST API 和 MCP 协议有什么区别？

**A**: 
- **REST API** (`/api/*`): 标准的 HTTP REST API，返回卡片格式 JSON，符合图片规范
- **MCP 协议** (`/mcp/`): Model Context Protocol 端点，用于 MCP 客户端连接，返回原始业务数据

## 测试清单

- [ ] `/health` 返回 `{"status": "OK"}`
- [ ] `/docs` 可以访问 Swagger UI
- [ ] `/openapi.json` 返回 OpenAPI Schema
- [ ] `/api/query-available-slots` (POST) 返回卡片格式响应
- [ ] `/api/submit-schedule-change` (POST) 返回卡片格式响应
- [ ] MCP 客户端可以连接到 `/mcp/` 并发现 2 个工具

