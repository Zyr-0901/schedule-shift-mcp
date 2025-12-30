import json
from datetime import datetime
from typing import Any, Dict, List, Optional
from fastmcp import FastMCP
from storage import (
    find_course_by_key,
    find_course_by_student_name,
    find_slot_by_id,
    get_slots,
    get_courses,
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


# 普通函数版本，可以被 app.py 直接调用
def query_available_slots_impl(
    course_name: str,
    original_date: str,
    target_date: str,
) -> Dict[str, Any]:
    """
    查询可约档期（按日期）。若目标日期不可约，返回替代方案。
    输入简化为：课程名称 + 原日期 + 目标日期。
    """
    course = None
    for c in get_courses():
        if c.get("content") == course_name:
            course = c
            break
    if not course:
        return {
            "status": "ok",
            "requested": {
                "is_available": False,
                "reason": "COURSE_NOT_FOUND",
                "requested_date": target_date,
            },
            "alternatives": [],
        }

    target_slots = [
        s for s in get_slots()
        if s.get("content") == course_name and s.get("time", "").startswith(target_date)
    ]
    target_slot = target_slots[0] if target_slots else None

    requested_result = {
        "is_available": False,
        "reason": "NOT_FOUND",
        "requested_date": target_date,
    }

    if target_slot:
        capacity_left = target_slot.get("capacity", 0) - target_slot.get("booked", 0)
        if capacity_left > 0:
            requested_result["is_available"] = True
            requested_result["reason"] = "AVAILABLE"
        else:
            requested_result["reason"] = "FULL"
    else:
        requested_result["reason"] = "NOT_FOUND"

    if requested_result["is_available"]:
        return {
            "status": "ok",
            "requested": requested_result,
            "alternatives": [],
        }

    alternatives_source = [
        s for s in get_slots()
        if s.get("content") == course_name
           and (s.get("capacity", 0) - s.get("booked", 0)) > 0
           and not s.get("time", "").startswith(target_date)
    ]
    alternatives_sorted = sorted(
        alternatives_source,
        key=lambda s: abs(
            (_parse_time(s["time"]).date() - _parse_time(f"{target_date} 00:00").date()).days
        )
    )

    result_alternatives = []
    for slot in alternatives_sorted[:3]:
        result_alternatives.append({
            "slot_id": slot.get("slot_id"),
            "time": slot.get("time"),
            "teacher": slot.get("teacher"),
            "content": slot.get("content"),
            "capacity_left": slot.get("capacity", 0) - slot.get("booked", 0),
            "location": slot.get("location", ""),
            "match": {
                "same_teacher": slot.get("teacher") == course.get("teacher"),
                "same_content": True,
            },
        })

    return {
        "status": "ok",
        "requested": requested_result,
        "alternatives": result_alternatives,
    }


# MCP 工具版本，调用普通函数
@mcp.tool()
def query_available_slots(
    course_name: str,
    original_date: str,
    target_date: str,
) -> Dict[str, Any]:
    """
    查询可约档期（按日期）。若目标日期不可约，返回替代方案。
    输入简化为：课程名称 + 原日期 + 目标日期。
    """
    return query_available_slots_impl(course_name, original_date, target_date)


# 普通函数版本，可以被 app.py 直接调用
def submit_schedule_change_impl(
    student_name: str,
    target_date: str,
) -> Dict[str, Any]:
    """
    提交调班申请（按学生姓名、目标日期）。取消手机号核验，改用学生姓名。
    """
    course = find_course_by_student_name(student_name)
    if not course:
        return {
            "status": "ok",
            "result": "FAILED",
            "message": "STUDENT_NOT_FOUND",
            "audit": None,
            "updated_schedule": None,
        }

    candidate_slots = [
        s for s in get_slots()
        if s.get("content") == course.get("content")
           and s.get("time", "").startswith(target_date)
           and (s.get("capacity", 0) - s.get("booked", 0)) > 0
    ]
    target_slot = candidate_slots[0] if candidate_slots else None

    if not target_slot:
        return {
            "status": "ok",
            "result": "FAILED",
            "message": "SLOT_NOT_FOUND_OR_FULL",
            "audit": None,
            "updated_schedule": None,
        }

    import os
    direct_success = os.getenv("SCHEDULE_DIRECT_SUCCESS", "false").lower() == "true"

    if direct_success:
        result_status = "SUCCESS"
        audit_info = None
    else:
        result_status = "PENDING_AUDIT"
        audit_info = {"eta_seconds": 180}

    request_record = {
        "student_name": student_name,
        "slot_id": target_slot.get("slot_id"),
        "status": result_status,
        "timestamp": datetime.now().isoformat(),
    }
    append_request(request_record)

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


# MCP 工具版本，调用普通函数
@mcp.tool()
def submit_schedule_change(
    student_name: str,
    target_date: str,
) -> Dict[str, Any]:
    """
    提交调班申请（按学生姓名、目标日期）。取消手机号核验，改用学生姓名。
    """
    return submit_schedule_change_impl(student_name, target_date)

