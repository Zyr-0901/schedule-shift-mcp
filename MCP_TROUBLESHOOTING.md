# MCP 服务器连接故障排查指南

## 问题：无法通过 MCP 形式导入到需要的系统

### 1. 检查服务器是否正常运行

```bash
# 检查健康检查端点
curl http://localhost:8000/health

# 应该返回: {"status": "OK"}
```

### 2. 检查 MCP 端点是否可访问

```bash
# 测试 MCP 端点（可能需要 POST 请求）
curl -X POST http://localhost:8000/mcp/ \
  -H "Content-Type: application/json" \
  -d '{"jsonrpc":"2.0","id":1,"method":"tools/list","params":{}}'
```

### 3. 运行诊断脚本

```bash
python diagnose_mcp.py
```

这会检查：
- FastMCP 实例是否正确创建
- 工具是否正确注册
- HTTP 应用是否正确创建

### 4. 检查工具注册

确保 `mcp_server.py` 中的工具使用 `@mcp.tool()` 装饰器：

```python
@mcp.tool()
def query_available_slots(...):
    ...

@mcp.tool()
def submit_schedule_change(...):
    ...
```

### 5. 尝试独立运行 MCP 服务器

如果挂载到 FastAPI 有问题，尝试独立运行：

```bash
python run_mcp_server.py
```

然后使用 MCP 客户端连接到 `http://localhost:8000/mcp`

### 6. 检查客户端配置

确保客户端配置正确：

**JSON 配置示例**：
```json
{
  "name": "schedule-shift",
  "type": "streamable-http",
  "url": "http://localhost:8000/mcp",
  "headers": {}
}
```

**常见配置问题**：
- URL 末尾的斜杠：尝试 `http://localhost:8000/mcp` 和 `http://localhost:8000/mcp/`
- 端口号：确保与服务器启动端口一致
- 协议：确保使用 `http://` 或 `https://`

### 7. 检查防火墙和网络

```bash
# 检查端口是否被占用
lsof -i :8000

# 检查服务器是否监听正确地址
netstat -an | grep 8000
```

### 8. 查看服务器日志

启动服务器时查看输出日志，检查是否有错误信息：

```bash
uvicorn app:app --host 0.0.0.0 --port 8000 --log-level debug
```

### 9. 测试 MCP 协议请求

使用测试脚本：

```bash
python test_mcp.py
```

### 10. 常见错误和解决方案

#### 错误：404 Not Found
- **原因**：MCP 端点路径不正确
- **解决**：检查 URL 是否为 `http://localhost:8000/mcp` 或 `http://localhost:8000/mcp/`

#### 错误：Connection Refused
- **原因**：服务器未启动或端口错误
- **解决**：确保服务器正在运行，检查端口号

#### 错误：工具列表为空
- **原因**：工具未正确注册
- **解决**：检查 `@mcp.tool()` 装饰器，确保工具函数被正确导入

#### 错误：协议不匹配
- **原因**：客户端和服务器使用的协议版本不匹配
- **解决**：检查 MCP 协议版本，确保兼容

### 11. 验证工具是否可用

如果服务器正常运行，但客户端无法发现工具，检查：

1. **工具函数签名**：确保工具函数有正确的类型注解
2. **工具描述**：确保工具函数有文档字符串
3. **导入顺序**：确保 `mcp_server.py` 中的工具在 `app.py` 导入前已注册

### 12. 联系支持

如果以上步骤都无法解决问题，请提供：
- 服务器启动日志
- 客户端错误信息
- 诊断脚本输出
- 客户端配置信息

## 快速测试清单

- [ ] 服务器可以启动（`uvicorn app:app` 无错误）
- [ ] `/health` 端点返回 `{"status": "OK"}`
- [ ] `diagnose_mcp.py` 显示工具已注册
- [ ] MCP 端点可以访问（`/mcp/` 不返回 404）
- [ ] 客户端配置 URL 正确
- [ ] 端口未被其他程序占用
- [ ] 防火墙允许连接

