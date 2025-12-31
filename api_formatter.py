"""API 响应格式化工具，将业务数据转换为卡片格式（符合图片规范）"""

from typing import Any, Dict, List


def format_query_result_to_card(data: Dict[str, Any]) -> Dict[str, Any]:
    """将 query_available_slots 的结果转换为卡片格式（按日期查询）"""
    requested = data.get("requested", {})
    alternatives = data.get("alternatives", [])

    alternatives_table = ""
    if alternatives:
        alternatives_table = "| 档期ID | 时间 | 老师 | 内容 | 剩余容量 | 地点 | 匹配度 |\n"
        alternatives_table += "|--------|------|------|------|----------|------|--------|\n"
        for alt in alternatives:
            match_desc = ""
            match = alt.get("match", {})
            if match.get("same_teacher") and match.get("same_content"):
                match_desc = "同老师同内容"
            elif match.get("same_content"):
                match_desc = "同内容"
            elif match.get("same_teacher"):
                match_desc = "同老师"
            else:
                match_desc = "其他"

            alternatives_table += f"| {alt.get('slot_id', '')} | {alt.get('time', '')} | {alt.get('teacher', '')} | {alt.get('content', '')} | {alt.get('capacity_left', 0)} | {alt.get('location', '')} | {match_desc} |\n"

    requested_status = "✅ 可约" if requested.get("is_available", False) else f"❌ 不可约（{requested.get('reason', '')}）"
    markdown_content = f"""## 档期查询结果

**目标日期**: {requested.get('requested_date', '')}
**状态**: {requested_status}

{alternatives_table if alternatives_table else "暂无替代方案"}

**原始数据**:
- 请求状态: {requested.get('is_available', False)}
- 原因: {requested.get('reason', '')}
- 替代方案数量: {len(alternatives)}
"""

    return {
        "type": "markdown",
        "data": [markdown_content],
        "raw": [data],
        "markdown": markdown_content,
        "field_headers": ["slot_id", "time", "teacher", "content", "capacity_left", "location", "match"],
        "chart_type": "",
        "dimension": "",
        "desc": f"查询档期结果：目标日期 {requested.get('requested_date', '')} {'可约' if requested.get('is_available', False) else '不可约'}，提供 {len(alternatives)} 个替代方案",
    }


def format_submit_result_to_card(data: Dict[str, Any]) -> Dict[str, Any]:
    """将 submit_schedule_change 的结果转换为卡片格式"""
    result_status = data.get("result", "")
    message_text = data.get("message", "")
    audit_info = data.get("audit")
    updated_schedule = data.get("updated_schedule") or {}  # 如果为 None 则使用空字典
    
    status_emoji = "✅" if result_status == "SUCCESS" else "⏳" if result_status == "PENDING_AUDIT" else "❌"
    
    # 只在有课程安排时才显示
    schedule_section = ""
    if updated_schedule:
        schedule_section = f"""
### 更新后的课程安排
- **时间**: {updated_schedule.get('time', '')}
- **老师**: {updated_schedule.get('teacher', '')}
- **地点**: {updated_schedule.get('location', '')}
"""
    
    markdown_content = f"""## 调班申请结果

**状态**: {status_emoji} {result_status}
**消息**: {message_text}
{schedule_section}
{f"**审核预计时间**: {audit_info.get('eta_seconds', 180)} 秒" if audit_info else ""}
"""
    
    return {
        "type": "markdown",
        "data": [markdown_content],
        "raw": [data],
        "markdown": markdown_content,
        "field_headers": ["result", "message", "time", "teacher", "location"],
        "chart_type": "",
        "dimension": "",
        "desc": f"调班申请结果：{result_status} - {message_text}",
    }

