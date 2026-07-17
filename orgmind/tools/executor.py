"""
工具执行器 - 对应 IMPLEMENTATION_SPEC 3.2 强制流程
7步不可跳过的安全流程
"""
import time
import json
from typing import Dict, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from orgmind.models.tool import Tool, AuditLog
from orgmind.governance.pii import detect_pii, censor_pii
import jsonschema  # type: ignore

DANGEROUS_CATEGORIES = {
    "fs_write", "fs_delete", "shell_exec", "code_exec",
    "network_outbound", "permission_modify", "batch_modify",
}


async def execute_tool(
    session: AsyncSession,
    tool_name: str,
    arguments: Dict,
    caller_role: str,
    user_id: str,
) -> Dict:
    """
    执行工具, 完整7步安全流程。
    每一步失败都拒绝执行, 绝不允许跳过任何一步。
    """
    start_time = time.monotonic()

    # 第1步: 查 tools 表确认存在且未被禁用
    stmt = select(Tool).where(Tool.name == tool_name, Tool.is_disabled == False)
    result = await session.execute(stmt)
    tool = result.scalars().first()
    if not tool:
        return {"success": False, "error": "TOOL_NOT_FOUND", "detail": f"Tool '{tool_name}' not found or disabled"}

    # 第2步: 检查角色权限
    if caller_role not in tool.allowed_roles:
        await _audit(session, user_id, "tool_denied", "tool", str(tool.id), {
            "tool_name": tool_name, "reason": "PERMISSION_DENIED", "caller_role": caller_role,
        })
        return {"success": False, "error": "PERMISSION_DENIED", "detail": f"Role '{caller_role}' not allowed"}

    # 第3步: JSON Schema 参数校验
    try:
        jsonschema.validate(instance=arguments, schema=tool.input_schema)
    except jsonschema.ValidationError as e:
        return {"success": False, "error": "INVALID_ARGUMENTS", "detail": str(e)}

    # 第4步: 危险工具需二次确认
    if tool.requires_confirmation:
        if not arguments.get("_confirmed", False):
            return {
                "success": False, "error": "AWAITING_CONFIRMATION",
                "detail": f"Tool '{tool_name}' requires confirmation",
            }

    # 第5步: 执行工具
    try:
        result_data = await _dispatch_execute(tool, arguments)
        success = True
    except Exception as e:
        result_data = {"error": str(e)}
        success = False

    duration_ms = (time.monotonic() - start_time) * 1000

    # 第6步: 写审计日志 (敏感字段脱敏)
    safe_args = _censor_sensitive_args(arguments)
    await _audit(session, user_id, "tool_execute", "tool", str(tool.id), {
        "tool_name": tool_name,
        "arguments": safe_args,
        "result_summary": str(result_data)[:500],
        "duration_ms": round(duration_ms),
        "success": success,
    })

    # 第7步: 返回结构化结果
    return {
        "success": success,
        "tool_name": tool_name,
        "result": result_data,
        "duration_ms": round(duration_ms),
    }


async def _dispatch_execute(tool: Tool, arguments: Dict) -> Dict:
    """根据 execution_type 分发执行"""
    if tool.execution_type == "local_function":
        return {"message": "local_function execution placeholder", "args": arguments}
    elif tool.execution_type == "http_api":
        return {"message": "http_api execution placeholder", "endpoint": tool.endpoint}
    elif tool.execution_type == "mcp_server":
        return {"message": "mcp_server execution placeholder", "endpoint": tool.endpoint}
    return {"message": "unknown execution type"}


def _censor_sensitive_args(args: Dict) -> Dict:
    safe = {}
    for k, v in args.items():
        if isinstance(v, str):
            pii_hits = detect_pii(v)
            safe[k] = censor_pii(v) if pii_hits else v
        else:
            safe[k] = v
    return safe


async def _audit(session: AsyncSession, user_id: str, action: str, rtype: str, rid: str, details: Dict):
    from uuid import UUID
    log = AuditLog(
        user_id=UUID(user_id),
        action=action,
        resource_type=rtype,
        resource_id=UUID(rid) if rid else None,
        details=details,
    )
    session.add(log)
    await session.commit()
