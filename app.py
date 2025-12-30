from contextlib import asynccontextmanager
from typing import Any, Dict
from fastapi import FastAPI, Request, Body
from fastapi.responses import JSONResponse
from mcp_server import mcp, query_available_slots, submit_schedule_change
from api_formatter import format_query_result_to_card, format_submit_result_to_card


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时初始化（如果需要）
    yield
    # 关闭时清理（如果需要）


app = FastAPI(
    title="Schedule Shift MCP Server",
    description="教育-临时调班 MCP Server",
    lifespan=lifespan,
)

# 挂载 MCP 服务器到 /mcp/ 路径
# FastMCP 的 http_app() 返回 ASGI 应用
# 注意：FastMCP 的 http_app() 不包含 FastAPI 的文档端点（/docs, /openapi.json）
# 文档端点应访问主应用的 /docs 和 /openapi.json，而不是 /mcp/docs

# 获取 FastMCP 的 HTTP 应用
# http_app() 返回一个 ASGI 应用，可以直接挂载到 FastAPI
mcp_app = mcp.http_app()
app = FastAPI(lifespan=mcp_app.lifespan)

# 挂载到 /mcp 路径（FastAPI 会自动处理 /mcp 和 /mcp/）
# 使用 name=None 避免路径冲突
app.mount("/", mcp_app)
# app.mount("/mcp", mcp_app)
# app.mount("/mcp/", mcp_app)

# @app.on_event("startup")
# async def _print_routes():
#     print("=== FastAPI routes ===")
#     for r in app.router.routes:
#         path = getattr(r, "path", None)
#         name = getattr(r, "name", None)
#         methods = getattr(r, "methods", None)
#         print(path, name, methods)


@app.get("/health")
async def health_check():
    """健康检查端点"""
    return JSONResponse({"status": "OK"})


# 注意：FastAPI 自动生成的文档端点：
# - /docs - Swagger UI 文档
# - /openapi.json - OpenAPI JSON Schema
# - /redoc - ReDoc 文档
# 这些端点在主应用根路径下，不在 /mcp/ 路径下


# ========== 标准 REST API 端点（符合图片规范）==========

@app.post("/api/query-available-slots")
async def api_query_available_slots(request: Request):
    """
    查询可约档期 API（POST 方法，返回卡片格式）
    符合图片规范：POST 方法，Content-Type: application/json，响应为卡片格式 JSON
    """
    try:
        body: Dict[str, Any] = await request.json()
        
        # 调用 MCP 工具函数
        result = query_available_slots(
            course_key=body.get("course_key", ""),
            original_time=body.get("original_time", ""),
            target_time_or_range=body.get("target_time_or_range", {}),
            require_same_teacher=body.get("require_same_teacher", True),
            prefer_same_content=body.get("prefer_same_content", True),
        )
        
        # 转换为卡片格式
        card_response = format_query_result_to_card(result)
        return JSONResponse(card_response)
    except Exception as e:
        return JSONResponse({
            "type": "markdown",
            "data": [f"错误: {str(e)}"],
            "raw": [{"error": str(e)}],
            "markdown": f"**错误**: {str(e)}",
            "field_headers": [],
            "chart_type": "",
            "dimension": "",
            "desc": f"查询档期时发生错误: {str(e)}",
        }, status_code=400)


@app.post("/api/submit-schedule-change")
async def api_submit_schedule_change(request: Request):
    """
    提交调班申请 API（POST 方法，返回卡片格式）
    符合图片规范：POST 方法，Content-Type: application/json，响应为卡片格式 JSON
    """
    try:
        body: Dict[str, Any] = await request.json()
        
        # 调用 MCP 工具函数
        result = submit_schedule_change(
            course_key=body.get("course_key", ""),
            slot_id=body.get("slot_id", ""),
            verification=body.get("verification", {}),
        )
        
        # 转换为卡片格式
        card_response = format_submit_result_to_card(result)
        return JSONResponse(card_response)
    except Exception as e:
        return JSONResponse({
            "type": "markdown",
            "data": [f"错误: {str(e)}"],
            "raw": [{"error": str(e)}],
            "markdown": f"**错误**: {str(e)}",
            "field_headers": [],
            "chart_type": "",
            "dimension": "",
            "desc": f"提交调班申请时发生错误: {str(e)}",
        }, status_code=400)


@app.get("/api/query-available-slots")
async def api_query_available_slots_get(
    course_key: str,
    original_time: str,
    target_time: str,
    require_same_teacher: bool = True,
    prefer_same_content: bool = True,
):
    """
    查询可约档期 API（GET 方法，返回卡片格式）
    符合图片规范：GET 方法，响应为卡片格式 JSON
    """
    try:
        target_time_or_range = {
            "type": "exact",
            "start": target_time,
            "end": target_time,
        }
        
        result = query_available_slots(
            course_key=course_key,
            original_time=original_time,
            target_time_or_range=target_time_or_range,
            require_same_teacher=require_same_teacher,
            prefer_same_content=prefer_same_content,
        )
        
        card_response = format_query_result_to_card(result)
        return JSONResponse(card_response)
    except Exception as e:
        return JSONResponse({
            "type": "markdown",
            "data": [f"错误: {str(e)}"],
            "raw": [{"error": str(e)}],
            "markdown": f"**错误**: {str(e)}",
            "field_headers": [],
            "chart_type": "",
            "dimension": "",
            "desc": f"查询档期时发生错误: {str(e)}",
        }, status_code=400)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

