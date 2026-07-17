"""
OrgMind REST API 路由
"""
import uuid
from typing import Optional, Dict
from fastapi import APIRouter, Depends, HTTPException, Request, Body
from fastapi.security import HTTPBearer
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from orgmind.database import get_db, set_db_session_context, rls_session
from orgmind.auth.jwt import create_token, verify_token, jwt_payload_to_context
from orgmind.auth.middleware import get_jwt_payload
from orgmind.retrieval.router import retrieve
from orgmind.skills.engine import match_skills, load_skill_level2
from orgmind.agents.registry import invoke_agent, register_agent
from orgmind.services.embedding import get_embedding
from orgmind.governance.validators import validate_content
from orgmind.governance.cleaners import clean_text
from orgmind.governance.dedup import compute_content_hash, check_memory_duplicate, DupResult
from orgmind.governance.pii import detect_pii, upgrade_sensitivity
from orgmind.governance.quality import compute_quality_score, QualityInput
from orgmind.models.memory import Memory
from orgmind.models.document import Document, DocumentChunk, DataLineage
from orgmind.graph.extractor import build_graph_from_text

router = APIRouter(prefix="/api/v1")
security = HTTPBearer()


# --- 请求模型 ---
class LoginRequest(BaseModel):
    email: str
    password: str

class MemoryCreateRequest(BaseModel):
    content: str
    type: str = Field(default="episodic")
    scope: str = Field(default="department")
    department_id: Optional[str] = None

class RetrieveRequest(BaseModel):
    query: str
    top_k: int = Field(default=5)
    mode: str = Field(default="auto")
    filters: Optional[Dict] = None

class SkillMatchRequest(BaseModel):
    query: str
    top_k: int = Field(default=5)

class AgentInvokeRequest(BaseModel):
    agent_name: str

class AgentRegisterRequest(BaseModel):
    name: str
    description: str
    content: str
    tools: list[str] = Field(default_factory=list)
    bound_skill_ids: list[str] = Field(default_factory=list)
    parent_id: Optional[str] = None
    scope: str = Field(default="department")


# --- 健康检查 ---
@router.get("/health")
async def health():
    return {"status": "ok", "service": "OrgMind"}


# --- 认证 ---
@router.post("/auth/login")
async def login(req: LoginRequest, session: AsyncSession = Depends(get_db)):
    """登录并返回JWT。生产环境应验证密码哈希。"""
    from sqlalchemy import select
    from orgmind.models.user import User
    stmt = select(User).where(User.email == req.email)
    result = await session.execute(stmt)
    user = result.scalars().first()
    if not user:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = create_token(
        user_id=user.id,
        org_id=user.org_id,
        role=user.role,
        department_id=user.department_id,
        project_ids=user.project_ids or [],
    )
    return {
        "token": token,
        "user": {"id": str(user.id), "email": user.email, "name": user.name, "role": user.role},
    }


# --- 记忆写入 (含清洗/去重/PII/质量分) ---
@router.post("/memory")
async def create_memory(
    req: MemoryCreateRequest,
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    """写入新记忆: 校验→清洗→PII→去重→质量分→入库→建图"""
    # 注入RLS
    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)

    # 清洗
    cleaned, meta = clean_text(req.content)
    validate_content(cleaned, "text")

    # PII
    pii_hits = detect_pii(cleaned)
    sensitivity = upgrade_sensitivity("normal", pii_hits)

    # 去重
    content_hash = compute_content_hash(cleaned)
    embedding = None
    try:
        embedding = await get_embedding(cleaned)
    except Exception:
        pass
    dup_result, dup_id, related_ids = await check_memory_duplicate(
        session, jwt_payload["org_id"], content_hash, embedding
    )
    if dup_result == DupResult.EXACT:
        return {"id": dup_id, "duplicate": True, "status": "existing"}

    # 质量分
    qscore = compute_quality_score(QualityInput(
        completeness=1.0, schema_valid=1.0,
        near_duplicate_count=1 if dup_result == DupResult.NEAR_DUPLICATE else 0,
        source_trust=0.5,
    ))

    # 入库
    memory = Memory(
        id=uuid.uuid4(),
        org_id=uuid.UUID(jwt_payload["org_id"]),
        department_id=uuid.UUID(req.department_id) if req.department_id else None,
        type=req.type,
        scope=req.scope,
        content=cleaned,
        summary=cleaned[:200] if len(cleaned) > 200 else cleaned,
        content_hash=content_hash,
        embedding=embedding,
        sensitivity=sensitivity,
        quality_score=qscore,
        status="active",
        created_by=uuid.UUID(jwt_payload["user_id"]),
        extra_metadata={"truncated": meta.get("truncated", False), "pii_detected": pii_hits},
    )
    if dup_result == DupResult.NEAR_DUPLICATE and dup_id:
        memory.status = "needs_review"
        memory.extra_metadata["duplicate_of"] = dup_id
    if related_ids:
        memory.extra_metadata["related_ids"] = related_ids

    session.add(memory)
    await session.commit()

    # 异步建图 (简单调用)
    try:
        build_graph_from_text(jwt_payload["org_id"], cleaned, str(memory.id), "memory")
        memory.graph_node_id = str(memory.id)[:20]
        session.add(memory)
        await session.commit()
    except Exception:
        pass

    return {
        "id": str(memory.id),
        "status": memory.status,
        "duplicate": dup_result == DupResult.NEAR_DUPLICATE,
        "quality_score": qscore,
        "sensitivity": sensitivity,
    }


# --- 检索引擎 ---
@router.post("/retrieve")
async def retrieve_api(
    req: RetrieveRequest,
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    """三路混合检索: vector + keyword + graph"""
    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)
    # org_id 只从JWT来, 忽略请求体中的org_id
    return await retrieve(session, jwt_payload, req.query, req.top_k, req.filters, req.mode)


# --- Skill 匹配 ---
@router.post("/skill/match")
async def skill_match(
    req: SkillMatchRequest,
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    """Skill三层加载: Level1目录 → 匹配 → Level2按需"""
    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)
    matched = await match_skills(
        session, jwt_payload["org_id"], req.query, jwt_payload["role"], req.top_k,
    )
    # 按需加载 Level2
    loaded = await load_skill_level2(session, [m["id"] for m in matched])
    return {"matched": loaded}


# --- Agent 调用 ---
@router.post("/agent/invoke")
async def agent_invoke(
    req: AgentInvokeRequest,
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)
    return await invoke_agent(session, jwt_payload["org_id"], req.agent_name, jwt_payload["role"])


@router.post("/agent/register")
async def agent_register(
    req: AgentRegisterRequest,
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)
    return await register_agent(
        session, jwt_payload["org_id"],
        req.name, req.description, req.content,
        req.tools, req.bound_skill_ids, jwt_payload["user_id"],
        req.parent_id, req.scope,
    )


# --- MCP Server 端点 (供外部Agent框架接入) ---
@router.post("/mcp/search")
async def mcp_search(
    query: str = Body(...),
    top_k: int = Body(default=5),
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    """MCP tool: memory_search - 暴露给外部Agent"""
    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)
    return await retrieve(session, jwt_payload, query, top_k, None, "auto")


@router.post("/mcp/document")
async def mcp_document(
    query: str = Body(...),
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    """MCP tool: document_query"""
    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)
    return await retrieve(session, jwt_payload, query, 5, None, "auto")


# --- 会话自动记录 (Easy Code 调用) ---
class AutoRecordRequest(BaseModel):
    session_text: str
    session_id: Optional[str] = None

@router.post("/session/auto-record")
async def auto_record_session(
    req: AutoRecordRequest,
    jwt_payload: Dict = Depends(get_jwt_payload),
    session: AsyncSession = Depends(get_db),
):
    """
    Easy Code 每次会话结束后调用此端点。
    自动: 提取决策/错误修复/重复模式 → 写记忆 → 检测Skill候选。
    """
    from orgmind.services.auto_memory import extract_memories_from_session, detect_repeated_pattern, generate_skill_draft

    async with session.begin():
        await set_db_session_context(await session.connection(), jwt_payload)

    # 1. 提取记忆
    extracted = extract_memories_from_session(req.session_text)
    written = []

    for mem in extracted:
        cleaned, _ = clean_text(mem["content"])
        ch = compute_content_hash(cleaned)
        dup_result, dup_id, _ = await check_memory_duplicate(session, jwt_payload["org_id"], ch, None)

        if dup_result == DupResult.EXACT:
            written.append({"id": dup_id, "content": mem["content"][:80], "type": mem["type"], "duplicate": True})
            continue

        try:
            embedding = await get_embedding(cleaned)
        except Exception:
            embedding = None

        pii_hits = detect_pii(cleaned)
        sensitivity = upgrade_sensitivity("normal", pii_hits)

        memory_obj = Memory(
            id=uuid.uuid4(),
            org_id=uuid.UUID(jwt_payload["org_id"]),
            type=mem["type"],
            scope="org",
            content=cleaned,
            summary=cleaned[:200],
            content_hash=ch,
            embedding=embedding,
            sensitivity=sensitivity,
            quality_score=mem.get("confidence", 0.7),
            status="active",
            created_by=uuid.UUID(jwt_payload["user_id"]),
            extra_metadata={"extracted_type": mem.get("extracted_type"), "auto_generated": True},
        )
        session.add(memory_obj)
        try:
            build_graph_from_text(jwt_payload["org_id"], cleaned, str(memory_obj.id), "memory")
            memory_obj.graph_node_id = str(memory_obj.id)[:20]
        except Exception:
            pass
        written.append({"id": str(memory_obj.id), "content": mem["content"][:80], "type": mem["type"], "duplicate": False})

    await session.commit()

    # 2. 检测Skill候选 (简单版: 查历史中同类型记忆 >=3次)
    skill_candidate = None
    from sqlalchemy import select, func
    stmt = select(
        Memory.extra_metadata['extracted_type'].astext,
        func.count().label("cnt")
    ).where(
        Memory.org_id == uuid.UUID(jwt_payload["org_id"]),
        Memory.extra_metadata['extracted_type'].isnot(None),
        Memory.extra_metadata['auto_generated'].astext == 'true',
    ).group_by(Memory.extra_metadata['extracted_type'].astext).having(func.count() >= 3)
    result = await session.execute(stmt)
    repeated = result.all()
    if repeated:
        top = repeated[0]
        skill_candidate = {
            "pattern": top[0],
            "count": top[1],
            "action": "Skill 草案已自动生成, 请在 Skill 管理中审核发布",
        }

    return {
        "memories_written": len(written),
        "memories": written,
        "skill_candidate": skill_candidate,
        "total_extracted": len(extracted),
    }
