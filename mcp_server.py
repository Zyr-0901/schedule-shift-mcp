import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from storage import (
    find_course_by_key,
    find_slot_by_id,
    get_slots,
    append_request,
)

mcp = FastMCP("ScheduleShiftMCP")


def _parse_time(time_str: str) -> datetime:
    """解析时间字符串为 datetime 对象"""
    return datetime.strptime(time_str, "%Y-%m-%d %H:%M")


def _format_time(dt: datetime) -> str:
    """格式化 datetime 为时间字符串"""
    return dt.strftime("%Y-%m-%d %H:%M")


def _find_slot_by_time(time_str: str) -> Optional[Dict[str, Any]]:
    """根据时间查找 slot"""
    for slot in get_slots():
        if slot.get("time") == time_str:
            return slot
    return None


def _calculate_match_score(
    slot: Dict[str, Any],
    original_teacher: str,
    original_content: str,
    require_same_teacher: bool,
    prefer_same_content: bool,
) -> tuple[int, datetime]:
    """计算匹配分数，返回 (score, time) 用于排序"""
    same_teacher = slot.get("teacher") == original_teacher
    same_content = slot.get("content") == original_content
    
    # 如果要求同老师但不匹配，返回低分
    if require_same_teacher and not same_teacher:
        return (-1000, _parse_time(slot["time"]))
    
    # 计算分数：同老师同内容 > 同内容 > 同老师 > 其他
    score = 0
    if same_teacher and same_content:
        score = 100
    elif same_content and prefer_same_content:
        score = 50
    elif same_teacher:
        score = 25
    
    # 时间越近越好（作为次要排序）
    time = _parse_time(slot["time"])
    return (score, time)


@mcp.tool()
def query_available_slots(
    course_key: str,
    original_time: str,
    target_time_or_range: Dict[str, Any],
    require_same_teacher: bool = True,
    prefer_same_content: bool = True,
) -> Dict[str, Any]:
    """
    查询可约档期。如果目标时间不可约，返回替代方案。
    
    Args:
        course_key: 课程标识
        original_time: 原时间 "YYYY-MM-DD HH:mm"
        target_time_or_range: 目标时间或时间范围
            - type: "exact" 或 "range"
            - start: "YYYY-MM-DD HH:mm"
            - end: "YYYY-MM-DD HH:mm"
        require_same_teacher: 是否要求同老师
        prefer_same_content: 是否优先同内容
    
    Returns:
        包含 requested 和 alternatives 的 JSON
    """
    # 查找课程信息
    course = find_course_by_key(course_key)
    if not course:
        return {
            "status": "ok",
            "requested": {
                "is_available": False,
                "reason": "NOT_FOUND",
                "requested_time": target_time_or_range.get("start", ""),
            },
            "alternatives": [],
        }
    
    original_teacher = course.get("teacher", "")
    original_content = course.get("content", "")
    
    # 确定要查询的目标时间
    target_type = target_time_or_range.get("type", "exact")
    if target_type == "exact":
        target_time = target_time_or_range.get("start", "")
    else:
        # range 类型暂时只检查 start
        target_time = target_time_or_range.get("start", "")
    
    # 查找目标时间的 slot
    target_slot = _find_slot_by_time(target_time)
    
    requested_result = {
        "is_available": False,
        "reason": "NOT_FOUND",
        "requested_time": target_time,
    }
    
    if target_slot:
        capacity_left = target_slot.get("capacity", 0) - target_slot.get("booked", 0)
        if capacity_left > 0:
            # 检查是否满足要求
            if require_same_teacher and target_slot.get("teacher") != original_teacher:
                requested_result["reason"] = "INVALID_TIME"
            else:
                requested_result["is_available"] = True
                requested_result["reason"] = "AVAILABLE"
        else:
            requested_result["reason"] = "FULL"
    else:
        requested_result["reason"] = "NOT_FOUND"
    
    # 如果目标时间可用，不需要替代方案
    if requested_result["is_available"]:
        return {
            "status": "ok",
            "requested": requested_result,
            "alternatives": [],
        }
    
    # 查找替代方案
    all_slots = get_slots()
    alternatives = []
    
    for slot in all_slots:
        slot_id = slot.get("slot_id")
        slot_time = slot.get("time")
        capacity_left = slot.get("capacity", 0) - slot.get("booked", 0)
        
        # 跳过已满的
        if capacity_left <= 0:
            continue
        
        # 跳过目标时间本身
        if slot_time == target_time:
            continue
        
        # 如果要求同老师，检查是否匹配
        if require_same_teacher and slot.get("teacher") != original_teacher:
            continue
        
        # 计算匹配分数
        score, time_dt = _calculate_match_score(
            slot, original_teacher, original_content, require_same_teacher, prefer_same_content
        )
        
        alternatives.append({
            "slot": slot,
            "score": score,
            "time": time_dt,
        })
    
    # 排序：分数高优先，时间近优先
    alternatives.sort(key=lambda x: (-x["score"], x["time"]))
    
    # 格式化返回结果（最多 3 个）
    result_alternatives = []
    for alt in alternatives[:3]:
        slot = alt["slot"]
        same_teacher = slot.get("teacher") == original_teacher
        same_content = slot.get("content") == original_content
        
        result_alternatives.append({
            "slot_id": slot.get("slot_id"),
            "time": slot.get("time"),
            "teacher": slot.get("teacher"),
            "content": slot.get("content"),
            "capacity_left": slot.get("capacity", 0) - slot.get("booked", 0),
            "location": slot.get("location", ""),
            "match": {
                "same_teacher": same_teacher,
                "same_content": same_content,
            },
        })
    
    # 返回原始业务数据（符合 MCP 协议）
    return {
        "status": "ok",
        "requested": requested_result,
        "alternatives": result_alternatives,
    }


@mcp.tool()
def submit_schedule_change(
    course_key: str,
    slot_id: str,
    verification: Dict[str, Any],
) -> Dict[str, Any]:
    """
    核验后提交调班申请。
    
    Args:
        course_key: 课程标识
        slot_id: 目标档期 ID
        verification: 核验信息
            - type: "last4"
            - value: 手机号后四位
    
    Returns:
        提交结果，包含状态、消息、审核信息等
    """
    # 查找课程
    course = find_course_by_key(course_key)
    if not course:
        return {
            "status": "ok",
            "result": "FAILED",
            "message": "COURSE_NOT_FOUND",
            "audit": None,
            "updated_schedule": None,
        }
    
    # 核验手机号后四位
    verification_type = verification.get("type", "")
    verification_value = verification.get("value", "")
    course_phone_last4 = course.get("phone_last4", "")
    
    if verification_type == "last4" and verification_value != course_phone_last4:
        return {
            "status": "ok",
            "result": "FAILED",
            "message": "VERIFICATION_MISMATCH",
            "audit": None,
            "updated_schedule": None,
        }
    
    # 查找目标 slot
    target_slot = find_slot_by_id(slot_id)
    if not target_slot:
        return {
            "status": "ok",
            "result": "FAILED",
            "message": "SLOT_NOT_FOUND",
            "audit": None,
            "updated_schedule": None,
        }
    
    # 检查是否还有空位
    capacity_left = target_slot.get("capacity", 0) - target_slot.get("booked", 0)
    if capacity_left <= 0:
        return {
            "status": "ok",
            "result": "FAILED",
            "message": "SLOT_FULL",
            "audit": None,
            "updated_schedule": None,
        }
    
    # 提交申请（默认待审核，可通过环境变量配置为直接成功）
    import os
    direct_success = os.getenv("SCHEDULE_DIRECT_SUCCESS", "false").lower() == "true"
    
    if direct_success:
        result_status = "SUCCESS"
        audit_info = None
    else:
        result_status = "PENDING_AUDIT"
        audit_info = {"eta_seconds": 180}
    
    # 记录到 requests
    request_record = {
        "course_key": course_key,
        "slot_id": slot_id,
        "status": result_status,
        "timestamp": datetime.now().isoformat(),
        "verification_type": verification_type,
    }
    append_request(request_record)
    
    # 返回原始业务数据（符合 MCP 协议）
    message_text = "申请已提交" if result_status == "PENDING_AUDIT" else "调班成功" if result_status == "SUCCESS" else "提交失败"
    
    return {
        "status": "ok",
        "result": result_status,
        "message": message_text,
        "audit": audit_info,
        "updated_schedule": {
            "time": target_slot.get("time"),
            "teacher": target_slot.get("teacher"),
            "location": target_slot.get("location", ""),
        },
    }

