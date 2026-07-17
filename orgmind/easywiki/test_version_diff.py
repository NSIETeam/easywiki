"""Unit tests for version_diff 3-way merge logic — run standalone, no DB needed for merge tests."""
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from orgmind.easywiki.version_diff import _line_merge

results = []

def check(name, actual, expected):
    ok = actual == expected
    results.append((name, ok, actual, expected))

# Test 1: No changes at all beyond base==current (should be caught before _line_merge, but test _line_merge directly)
base1 = "line0\nline1\nline2\n"
current1 = "line0\nline1\nline2\n"
proposed1 = "line0\nCHANGED\nline2\n"
merged, conflict = _line_merge(base1, current1, proposed1)
check("disjoint: current unchanged, proposed changes line1", merged, "line0\nCHANGED\nline2\n")
check("disjoint case1 no conflict", conflict, False)

# Test 2: Non-overlapping edits — current changes line0, proposed changes line2
base2 = "line0\nline1\nline2\n"
current2 = "HUMAN0\nline1\nline2\n"
proposed2 = "line0\nline1\nAGENT2\n"
merged2, conflict2 = _line_merge(base2, current2, proposed2)
check("disjoint edits merge cleanly", merged2, "HUMAN0\nline1\nAGENT2\n")
check("disjoint edits no conflict", conflict2, False)

# Test 3: Overlapping edits — both change line1 differently -> conflict
base3 = "line0\nline1\nline2\n"
current3 = "line0\nHUMAN_EDIT\nline2\n"
proposed3 = "line0\nAGENT_EDIT\nline2\n"
merged3, conflict3 = _line_merge(base3, current3, proposed3)
check("overlapping edits detected as conflict", conflict3, True)
check("overlapping edits keeps current", merged3, current3)

# Test 4: Pure appends at end from both sides (both appended -> should conflict per spec, since ambiguous ordering)
base4 = "line0\n"
current4 = "line0\nHUMAN_APPEND\n"
proposed4 = "line0\nAGENT_APPEND\n"
merged4, conflict4 = _line_merge(base4, current4, proposed4)
check("both append at same point -> conflict (ambiguous order)", conflict4, True)

# Test 5: Only one side appends, other side unchanged relative to base -> merges (agent appends only)
base5 = "line0\nline1\n"
current5 = "line0\nline1\n"  # unchanged
proposed5 = "line0\nline1\nAGENT_NEW\n"
merged5, conflict5 = _line_merge(base5, current5, proposed5)
check("only proposed appends -> merges", merged5, "line0\nline1\nAGENT_NEW\n")
check("only proposed appends -> no conflict", conflict5, False)

# Test 6: Only current appends (agent unchanged)
base6 = "line0\nline1\n"
current6 = "line0\nline1\nHUMAN_NEW\n"
proposed6 = "line0\nline1\n"  # unchanged
merged6, conflict6 = _line_merge(base6, current6, proposed6)
check("only current appends -> merges", merged6, "line0\nline1\nHUMAN_NEW\n")

# Test 7: current deletes a line, proposed edits a DIFFERENT line -> merge
base7 = "line0\nline1\nline2\nline3\n"
current7 = "line0\nline2\nline3\n"  # deleted line1
proposed7 = "line0\nline1\nline2\nCHANGED3\n"  # changed line3
merged7, conflict7 = _line_merge(base7, current7, proposed7)
check("delete + edit different line -> merges", merged7, "line0\nline2\nCHANGED3\n")
check("delete + edit different line -> no conflict", conflict7, False)

# Test 8: current deletes line1, proposed also touches line1 (edits it) -> conflict
base8 = "line0\nline1\nline2\n"
current8 = "line0\nline2\n"  # deleted line1
proposed8 = "line0\nEDITED1\nline2\n"  # edited line1
merged8, conflict8 = _line_merge(base8, current8, proposed8)
check("delete vs edit same line -> conflict", conflict8, True)

# Test 9: Progress field style single value via three_way_merge (import separately)
from orgmind.easywiki.version_diff import progress_field_merge
# monkeypatch: avoid DB call by testing the non-conflict branches only (no DB dependency)
merged9, cid9 = progress_field_merge("todo", "todo", "in_progress", "proj1", "field1")
check("progress field: base==current -> apply proposed", (merged9, cid9), ("in_progress", None))

merged10, cid10 = progress_field_merge("todo", "done", "done", "proj1", "field1")
check("progress field: current==proposed -> agree", (merged10, cid10), ("done", None))

merged11, cid11 = progress_field_merge("todo", "blocked", "todo", "proj1", "field1")
check("progress field: proposed==base (no real change) -> keep current", (merged11, cid11), ("blocked", None))

# Print results
passed = sum(1 for _, ok, _, _ in results if ok)
total = len(results)
print(f"\n=== version_diff unit tests: {passed}/{total} passed ===\n")
for name, ok, actual, expected in results:
    status = "PASS" if ok else "FAIL"
    line = f"[{status}] {name}"
    if not ok:
        line += f"\n    actual:   {actual!r}\n    expected: {expected!r}"
    print(line)

if passed != total:
    sys.exit(1)
