"""
员工画像 & Token 消耗评估 — v2.2
- 基于API调用记录分析员工工作模式
- Token消耗效率评估
- 自动生成员工能力画像
"""
import json
import time
from typing import Dict, List, Optional
from collections import defaultdict
from datetime import datetime, timedelta
from orgmind.database_sqlite import get_db


def record_token_usage(
    user_id: str,
    model: str,
    prompt_tokens: int,
    completion_tokens: int,
    task_type: str = "general",
    tool_calls: int = 0,
    session_id: Optional[str] = None,
):
    """记录一次Token使用"""
    db = get_db()
    db.execute("""
        CREATE TABLE IF NOT EXISTS token_usage_logs (
            id TEXT PRIMARY KEY,
            user_id TEXT NOT NULL,
            model TEXT NOT NULL,
            prompt_tokens INTEGER DEFAULT 0,
            completion_tokens INTEGER DEFAULT 0,
            task_type TEXT DEFAULT 'general',
            tool_calls INTEGER DEFAULT 0,
            session_id TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    import uuid
    db.execute(
        "INSERT INTO token_usage_logs (id,user_id,model,prompt_tokens,completion_tokens,task_type,tool_calls,session_id) VALUES (?,?,?,?,?,?,?,?)",
        (str(uuid.uuid4()), user_id, model, prompt_tokens, completion_tokens, task_type, tool_calls, session_id)
    )
    db.commit()


def get_employee_profile(user_id: str, days: int = 30) -> Dict:
    """生成员工能力画像"""
    db = get_db()
    since = (datetime.now() - timedelta(days=days)).isoformat()

    # Token使用统计
    usage = db.execute("""
        SELECT
            task_type, COUNT(*) as cnt,
            SUM(prompt_tokens) as total_prompt,
            SUM(completion_tokens) as total_completion,
            SUM(tool_calls) as total_tools
        FROM token_usage_logs
        WHERE user_id=? AND created_at >= ?
        GROUP BY task_type
        ORDER BY cnt DESC
    """, (user_id, since)).fetchall()

    # 记忆写入统计
    memories = db.execute("""
        SELECT COUNT(*) as cnt, type FROM memories
        WHERE created_by=? AND created_at >= ?
        GROUP BY type
    """, (user_id, since)).fetchall()

    total_tokens = sum(r['total_prompt'] + r['total_completion'] for r in usage)
    total_calls = sum(r['cnt'] for r in usage)

    # 效率评分: tokens_per_task, tool_usage_ratio
    efficiency = {}
    for r in usage:
        task = r['task_type']
        efficiency[task] = {
            'calls': r['cnt'],
            'avg_tokens_per_call': round((r['total_prompt'] + r['total_completion']) / max(r['cnt'], 1)),
            'tool_usage_ratio': round(r['total_tools'] / max(r['cnt'], 1), 2),
            'pct_of_total': round(r['cnt'] / max(total_calls, 1) * 100, 1),
        }

    # 能力标签推断
    tags = _infer_skill_tags(usage, memories)

    return {
        'user_id': user_id,
        'period_days': days,
        'total_tokens': total_tokens,
        'total_api_calls': total_calls,
        'task_breakdown': efficiency,
        'memory_contributions': [{'type': m['type'], 'count': m['cnt']} for m in memories],
        'inferred_skills': tags,
        'efficiency_score': _calc_efficiency_score(usage),
        'generated_at': datetime.now().isoformat(),
    }


def _infer_skill_tags(usage: List, memories: List) -> List[Dict]:
    """从使用模式推断能力标签"""
    tags = []
    for r in usage:
        task = r['task_type']
        if task == 'code_generation' and r['cnt'] > 20:
            tags.append({'tag': '代码生成', 'level': '熟练', 'confidence': 0.8})
        elif task == 'documentation' and r['cnt'] > 15:
            tags.append({'tag': '文档编写', 'level': '熟练', 'confidence': 0.75})
        elif task == 'analysis' and r['cnt'] > 10:
            tags.append({'tag': '数据分析', 'level': '掌握', 'confidence': 0.7})
        elif task == 'debugging' and r['cnt'] > 10:
            tags.append({'tag': '问题排查', 'level': '掌握', 'confidence': 0.7})

    memory_types = {m['type']: m['cnt'] for m in memories}
    if memory_types.get('best_practice', 0) > 3:
        tags.append({'tag': '最佳实践贡献者', 'level': '积极', 'confidence': 0.85})
    if memory_types.get('architecture', 0) > 2:
        tags.append({'tag': '架构设计', 'level': '掌握', 'confidence': 0.75})

    return tags


def _calc_efficiency_score(usage: List) -> float:
    """综合效率评分 0-100"""
    if not usage:
        return 0.0

    scores = []
    for r in usage:
        tokens = r['total_prompt'] + r['total_completion']
        # Efficient: fewer tokens per call, higher tool usage
        token_score = max(0, 100 - (tokens / max(r['cnt'], 1)) / 50)
        tool_score = min(100, r['total_tools'] / max(r['cnt'], 1) * 30)
        scores.append(token_score * 0.6 + tool_score * 0.4)

    return round(sum(scores) / len(scores), 1)


def get_team_token_report(org_id: str, days: int = 30) -> Dict:
    """团队Token消耗总览"""
    db = get_db()
    since = (datetime.now() - timedelta(days=days)).isoformat()

    rows = db.execute("""
        SELECT u.name, u.email, u.role, u.department_id,
               COALESCE(SUM(t.prompt_tokens + t.completion_tokens), 0) as total_tokens,
               COALESCE(COUNT(t.id), 0) as api_calls
        FROM users u
        LEFT JOIN token_usage_logs t ON u.id = t.user_id AND t.created_at >= ?
        WHERE u.org_id = ?
        GROUP BY u.id
        ORDER BY total_tokens DESC
    """, (since, org_id)).fetchall()

    total_org_tokens = sum(r['total_tokens'] for r in rows)

    return {
        'period_days': days,
        'total_org_tokens': total_org_tokens,
        'members': [
            {
                'name': r['name'],
                'email': r['email'],
                'role': r['role'],
                'tokens': r['total_tokens'],
                'api_calls': r['api_calls'],
                'share_pct': round(r['total_tokens'] / max(total_org_tokens, 1) * 100, 1),
            }
            for r in rows
        ],
        'generated_at': datetime.now().isoformat(),
    }


def get_token_cost_estimate(total_tokens: int, model: str = "gpt-4o-mini") -> Dict:
    """估算Token费用"""
    rates = {
        'gpt-4o': {'input': 2.50, 'output': 10.00},      # per 1M tokens
        'gpt-4o-mini': {'input': 0.15, 'output': 0.60},
        'gpt-4-turbo': {'input': 10.00, 'output': 30.00},
        'claude-sonnet-4': {'input': 3.00, 'output': 15.00},
    }
    rate = rates.get(model, rates['gpt-4o-mini'])
    # Assume 70% input, 30% output split
    input_tokens = int(total_tokens * 0.7)
    output_tokens = int(total_tokens * 0.3)
    cost = (input_tokens / 1_000_000) * rate['input'] + (output_tokens / 1_000_000) * rate['output']

    return {
        'model': model,
        'total_tokens': total_tokens,
        'estimated_cost_usd': round(cost, 4),
        'estimated_cost_cny': round(cost * 7.2, 2),
        'rate_per_1m_input': rate['input'],
        'rate_per_1m_output': rate['output'],
    }
