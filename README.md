## 需求说明：教育-临时调班 MCP Server（Python / HTTP）

### 1) 目标

在本地实现一个 MCP Server：`schedule-shift-mcp`，通过 **Streamable HTTP** 对外提供 MCP 工具能力（HTTP 传输是 MCP 标准传输之一）。 ([Model Context Protocol][1])

服务要暴露 2 个 tools：

* `query_available_slots`：查可约档期（如果目标满员，要自动给替代方案）
* `submit_schedule_change`：核验后提交调班（返回成功/待审核/失败原因）

### 2) 技术选型（必须）

* **Python**
* 使用 **FastMCP** 来实现 MCP Server（简化协议细节）
* 传输方式：`transport="http"`，MCP 端点默认在 `/mcp/`（同域名根路径可挂 `/health`） ([gofastmcp.com][2])

> FastMCP 支持把 MCP 服务作为 HTTP Web 服务运行，并且 MCP endpoint 在 `/mcp/`。 ([gofastmcp.com][2])

### 3) 运行方式

* 启动命令（示例）：`uvicorn app:app --host 0.0.0.0 --port 8000`
* MCP endpoint：`http://localhost:8000/mcp/`
* 健康检查：`GET http://localhost:8000/health`

### 4) 数据存储（最简可跑通）

用本地文件 `data/db.json`（或 sqlite 也行，但 json 更快）模拟教务系统，包含：

* `courses[]`：用户报名/订单信息（含手机号后四位）
* `slots[]`：可约档期（老师、内容、容量、已约）
* `requests[]`：调班申请记录（状态、时间戳、原因）

> 只要能支持“目标满员→推荐替代→核验→提交→待审核/成功”闭环即可。

---

## 5) Tool 设计（严格按下面 schema）

### Tool 1：query_available_slots

**name**：`query_available_slots`
**用途**：查询目标时间是否可约；不可约时给替代档期（同老师同内容优先）

**Input (JSON)**

```json
{
  "course_key": "string",
  "original_time": "YYYY-MM-DD HH:mm",
  "target_time_or_range": {
    "type": "exact|range",
    "start": "YYYY-MM-DD HH:mm",
    "end": "YYYY-MM-DD HH:mm"
  },
  "require_same_teacher": true,
  "prefer_same_content": true
}
```

**Output (JSON)**

```json
{
  "status": "ok",
  "requested": {
    "is_available": false,
    "reason": "FULL|NOT_FOUND|INVALID_TIME",
    "requested_time": "YYYY-MM-DD HH:mm"
  },
  "alternatives": [
    {
      "slot_id": "string",
      "time": "YYYY-MM-DD HH:mm",
      "teacher": "string",
      "content": "string",
      "capacity_left": 3,
      "location": "string",
      "match": { "same_teacher": true, "same_content": true }
    }
  ]
}
```

**核心逻辑**

* `exact`：只检查 `start` 这一个时刻
* 满员：`requested.is_available=false` 且 `reason=FULL`
* `alternatives` 排序：同老师同内容 > 同内容 > 最近时间
* `alternatives` 最多返回 3 个（够用、避免太长）

---

### Tool 2：submit_schedule_change

**name**：`submit_schedule_change`
**用途**：核验通过后提交调班申请（默认返回待审核，模拟 180 秒）

**Input (JSON)**

```json
{
  "course_key": "string",
  "slot_id": "string",
  "verification": {
    "type": "last4",
    "value": "9706"
  }
}
```

**Output (JSON)**

```json
{
  "status": "ok",
  "result": "PENDING_AUDIT|SUCCESS|FAILED",
  "message": "string",
  "audit": { "eta_seconds": 180 },
  "updated_schedule": {
    "time": "YYYY-MM-DD HH:mm",
    "teacher": "string",
    "location": "string"
  }
}
```

**核心逻辑**

* 核验失败：`FAILED` + `message=VERIFICATION_MISMATCH`
* slot 被抢/满员：`FAILED` + `message=SLOT_FULL`
* 正常：写入 `requests[]`，默认 `PENDING_AUDIT`（eta=180），可用配置切换为直接 `SUCCESS`

---

## 6) 服务结构（建议）

```
schedule-shift-mcp/
  app.py                  # FastAPI + MCP 挂载
  mcp_server.py           # FastMCP tools 定义
  storage.py              # 读写 data/db.json
  data/db.json
  pyproject.toml
  README.md
```

### 需要实现的 HTTP 挂载方式

* 让 MCP 作为 ASGI app 挂在 FastAPI 下（路径 `/mcp` 或 `/mcp/`）
* 注意 lifespan 合并（FastMCP 文档建议传递 lifespan） ([gofastmcp.com][3])

---

## 7) 验收标准（跑通即可）

1. 本地启动后，访问 `/health` 返回 `OK` ([gofastmcp.com][2])
2. MCP 客户端能发现 2 个 tools
3. 调用 `query_available_slots`：

   * 目标满员时能返回至少 1 个替代档期
4. 调用 `submit_schedule_change`：

   * 后四位不匹配 → FAILED
   * 匹配 → PENDING_AUDIT（eta=180）或 SUCCESS
5. `data/db.json` 的 `requests[]` 有新增记录

---

## 8) 录入到你的系统（HTTP MCP 插件）

你系统里只要支持 **Streamable HTTP**，通常配置就是“URL + 可选 headers”。MCP 的 HTTP（streamable-http）客户端一般用形如 `http://localhost:8000/mcp` 的 URL。 ([LangChain Docs][4])

**示例（通用）**

```json
{
  "name": "schedule-shift",
  "type": "streamable-http",
  "url": "http://localhost:8000/mcp",
  "headers": {}
}
```

> 如果你的系统界面是“Add MCP Server → HTTP(Streamable HTTP) → URL”，就填上面这个 URL，然后刷新工具列表即可。

---

## 9) 具体任务

> 用 Python 实现一个基于 FastMCP 的 MCP Server，使用 Streamable HTTP（/mcp/）对外提供两个 tools：query_available_slots 和 submit_schedule_change。用 data/db.json 模拟 courses/slots/requests 三类数据，按需求文档的输入输出 schema 实现逻辑（满员给替代、核验后四位、提交返回待审核 180 秒）。提供 /health 路由、README、启动命令、以及如何在客户端用 [http://localhost:8000/mcp/](http://localhost:8000/mcp/) 连接测试。

---