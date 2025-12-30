"""直接运行 FastMCP HTTP 服务器（独立模式）"""
from mcp_server import mcp

if __name__ == "__main__":
    # FastMCP 可以直接运行 HTTP 服务器
    # 使用 run() 方法启动服务器
    import uvicorn
    
    # 获取 FastMCP 的 ASGI 应用
    app = mcp.http_app()
    
    # 直接运行 FastMCP 服务器
    print("启动 FastMCP HTTP 服务器...")
    print("MCP 端点: http://localhost:8000/mcp/")
    print("按 Ctrl+C 停止服务器")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info"
    )

