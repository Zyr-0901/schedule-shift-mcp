"""测试 MCP 端点是否正常工作"""
import requests
import json

BASE_URL = "http://localhost:8000"

def test_health():
    """测试健康检查"""
    print("测试 /health...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"状态码: {response.status_code}")
    print(f"响应: {response.json()}")
    print()

def test_mcp_endpoint():
    """测试 MCP 端点"""
    print("测试 /mcp/ 端点...")
    
    # MCP 协议通常使用 POST 请求
    # 尝试发送一个 MCP 协议请求（initialize）
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {
                "name": "test-client",
                "version": "1.0.0"
            }
        }
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp/",
            json=mcp_request,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应头: {dict(response.headers)}")
        print(f"响应内容: {response.text[:500]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

def test_mcp_list_tools():
    """测试列出工具"""
    print("测试列出工具...")
    
    mcp_request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/list",
        "params": {}
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/mcp/",
            json=mcp_request,
            headers={"Content-Type": "application/json"}
        )
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text[:1000]}")
    except Exception as e:
        print(f"错误: {e}")
    print()

if __name__ == "__main__":
    print("=" * 50)
    print("MCP 端点测试")
    print("=" * 50)
    print()
    
    test_health()
    test_mcp_endpoint()
    test_mcp_list_tools()

