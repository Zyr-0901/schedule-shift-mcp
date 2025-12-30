"""诊断 MCP 服务器配置"""
from mcp_server import mcp

print("=" * 60)
print("MCP 服务器诊断")
print("=" * 60)
print()

# 检查 FastMCP 实例
print(f"FastMCP 实例: {mcp}")
print(f"FastMCP 名称: {mcp.name if hasattr(mcp, 'name') else 'N/A'}")
print()

# 检查工具
print("已注册的工具:")
if hasattr(mcp, 'tools'):
    tools = mcp.tools if hasattr(mcp, 'tools') else []
    for tool in tools:
        print(f"  - {tool}")
else:
    # 尝试获取工具列表
    try:
        # FastMCP 可能使用不同的属性名
        if hasattr(mcp, '_tools'):
            tools = mcp._tools
            for name, tool in tools.items():
                print(f"  - {name}: {tool}")
        else:
            print("  无法获取工具列表（可能需要运行时检查）")
    except Exception as e:
        print(f"  获取工具列表时出错: {e}")
print()

# 检查 HTTP 应用
print("检查 HTTP 应用:")
try:
    http_app = mcp.http_app()
    print(f"  HTTP 应用类型: {type(http_app)}")
    print(f"  HTTP 应用: {http_app}")
    
    # 检查是否有路由
    if hasattr(http_app, 'routes'):
        print(f"  路由数量: {len(http_app.routes)}")
        for route in http_app.routes:
            print(f"    - {route}")
    else:
        print("  无法获取路由信息（可能需要运行时检查）")
except Exception as e:
    print(f"  创建 HTTP 应用时出错: {e}")
print()

print("=" * 60)
print("诊断完成")
print("=" * 60)
print()
print("提示:")
print("1. 确保工具使用 @mcp.tool() 装饰器")
print("2. 确保 FastMCP 实例在导入时已创建")
print("3. 检查 http_app() 方法是否正确返回 ASGI 应用")
print("4. 如果问题仍然存在，尝试使用 run_mcp_server.py 独立运行 MCP 服务器")

