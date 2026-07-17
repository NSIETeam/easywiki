"""
Version diff & 3-way merge — Section 3.5 of EASYWIKI_EXECUTION_SPEC.md

Git-style 3-way merge:
- base: content at the version the agent read (based_on_version)
- current: latest approved version at approval time
- proposed: agent's proposed content

Correctness strategy (gap-based overlap detection):
Base lines 0..n-1 have n+1 "gap" boundary points (0..n). Any diff opcode
(insert/delete/replace) against base "touches" a set of gap points:
  - insert at i1 (i1 == i2) touches exactly {i1}
  - delete/replace over [i1, i2) touches {i1, i1+1, ..., i2}
Two edits (current-vs-base and proposed-vs-base) are considered overlapping
iff their touched-gap sets intersect. This correctly detects insert-vs-insert
at the same point, insert-vs-replace covering that point, and
replace-vs-replace with overlapping ranges — while genuinely disjoint edits
(e.g. current edits line 0, proposed edits line 2) auto-merge cleanly.

Reconstruction walks base line-by-line (position 0..n). At each position it
first flushes any zero-width insert anchored there (from current or
proposed — never both, guaranteed by the overlap check), then checks whether
a replace/delete range starts there (from current or proposed) and if so
emits the replacement and jumps past the range; otherwise it copies the base
line through unchanged and advances by one.
"""
import difflib
import uuid
from typing import Optional, Tuple, List, Dict
from orgmind.db import get_db


def three_way_merge(
    base: str, current: str, proposed: str,
    target_type: str, target_id: str,
    project_id: str
) -> Tuple[str, Optional[str]]:
    if base == current:
        return proposed, None
    if current == proposed:
        return proposed, None
    if proposed == base:
        return current, None

    merged, has_conflict = _line_merge(base, current, proposed)
    if not has_conflict:
        return merged, None

    conflict_id = _create_conflict(target_type, target_id, project_id, base, current, proposed)
    return current, conflict_id


def _non_equal_opcodes(base_lines: List[str], other_lines: List[str]):
    sm = difflib.SequenceMatcher(a=base_lines, b=other_lines, autojunk=False)
    return [op for op in sm.get_opcodes() if op[0] != "equal"]


def _touched_gaps(opcodes) -> set:
    gaps = set()
    for _tag, i1, i2, _j1, _j2 in opcodes:
        if i1 == i2:
            gaps.add(i1)
        else:
            gaps.update(range(i1, i2))
    return gaps


def _line_merge(base: str, current: str, proposed: str) -> Tuple[str, bool]:
    base_lines = base.splitlines(keepends=True)
    current_lines = current.splitlines(keepends=True)
    proposed_lines = proposed.splitlines(keepends=True)

    current_ops = _non_equal_opcodes(base_lines, current_lines)
    proposed_ops = _non_equal_opcodes(base_lines, proposed_lines)

    if _touched_gaps(current_ops) & _touched_gaps(proposed_ops):
        return current, True  # overlapping edit regions -> conflict

    # Disjoint edits: index them by start position for O(1) lookup during the walk.
    # inserts_at[i]: list of zero-width insertions anchored at gap i
    # ranges_at[i]: (end, replacement_lines) for a replace/delete starting at i
    inserts_at: Dict[int, List[str]] = {}
    ranges_at: Dict[int, Tuple[int, List[str]]] = {}

    for tag, i1, i2, j1, j2 in current_ops:
        (inserts_at.setdefault(i1, []).extend(current_lines[j1:j2]) if i1 == i2
         else ranges_at.__setitem__(i1, (i2, current_lines[j1:j2])))
    for tag, i1, i2, j1, j2 in proposed_ops:
        (inserts_at.setdefault(i1, []).extend(proposed_lines[j1:j2]) if i1 == i2
         else ranges_at.__setitem__(i1, (i2, proposed_lines[j1:j2])))

    merged_lines: List[str] = []
    n = len(base_lines)
    pos = 0
    while pos <= n:
        if pos in inserts_at:
            merged_lines.extend(inserts_at[pos])
        if pos == n:
            break
        if pos in ranges_at:
            end, repl = ranges_at[pos]
            merged_lines.extend(repl)
            pos = end
        else:
            merged_lines.append(base_lines[pos])
            pos += 1

    return "".join(merged_lines), False


def _create_conflict(
    target_type: str, target_id: str, project_id: str,
    base_content: str, current_content: str, proposed_content: str
) -> str:
    db = get_db()
    cid = str(uuid.uuid4())
    escalated_to = _find_escalation_target(project_id)
    db.execute(
        "INSERT INTO easywiki_conflicts (id,target_type,target_id,base_version_id,human_version_id,agent_version_id,escalated_to_user_id,status) VALUES (?,?,?,?,?,?,?,?)",
        (cid, target_type, target_id, _content_prefix(base_content), _content_prefix(current_content),
         _content_prefix(proposed_content), escalated_to, "open")
    )
    db.commit()
    return cid


def _find_escalation_target(project_id: str) -> Optional[str]:
    """Find who to escalate to based on project/department hierarchy."""
    db = get_db()
    proj = db.execute("SELECT department_id FROM easywiki_projects WHERE id=?", (project_id,)).fetchone()
    if not proj or not proj["department_id"]:
        admin = db.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
        return admin["id"] if admin else None
    mgr = db.execute("SELECT id FROM users WHERE role='manager' AND department_id=? LIMIT 1", (proj["department_id"],)).fetchone()
    if mgr:
        return mgr["id"]
    admin = db.execute("SELECT id FROM users WHERE role='admin' LIMIT 1").fetchone()
    return admin["id"] if admin else None


def _content_prefix(content: str, max_len: int = 200) -> str:
    return content[:max_len]


def progress_field_merge(base_value: str, current_value: str, proposed_value: str,
                         project_id: str, field_id: str) -> Tuple[str, Optional[str]]:
    """Merge for progress fields (single-value, atomic — no partial overlap concept)."""
    if base_value == current_value:
        return proposed_value, None
    if current_value == proposed_value:
        return proposed_value, None
    if proposed_value == base_value:
        return current_value, None
    conflict_id = _create_conflict("progress_field", field_id, project_id,
                                   base_value, current_value, proposed_value)
    return current_value, conflict_id
