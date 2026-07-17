import { useState, useEffect } from "react";
import { listPending, approveEntry, rejectEntry, batchApprove } from "../api/client";

export default function AgentInbox({ pid }: { pid: string }) {
  const [entries, setEntries] = useState<any[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editedContent, setEditedContent] = useState("");
  const [rejectReason, setRejectReason] = useState<Record<string, string>>({});
  const [showRejectInput, setShowRejectInput] = useState<string | null>(null);

  const load = () => listPending(pid).then((r) => setEntries(r.entries));

  useEffect(() => { load(); }, [pid]);

  const handleApprove = async (id: string) => {
    if (editingId === id) {
      await approveEntry(id, editedContent);
      setEditingId(null);
    } else {
      await approveEntry(id);
    }
    load();
  };

  const handleReject = async (id: string) => {
    const reason = rejectReason[id] || "";
    await rejectEntry(id, reason);
    setShowRejectInput(null);
    setRejectReason((prev) => ({ ...prev, [id]: "" }));
    load();
  };

  const handleBatchApprove = async () => {
    await batchApprove(Array.from(selected));
    setSelected(new Set());
    load();
  };

  const toggleSelect = (id: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      next.has(id) ? next.delete(id) : next.add(id);
      return next;
    });
  };

  const typeLabels: Record<string, string> = {
    decision: "决策", bug_fix: "Bug修复", best_practice: "最佳实践",
    architecture: "架构选型", progress_update: "进度更新",
  };

  return (
    <div>
      <div className="flex justify-between items-center mb-3">
        <h3 className="text-[15px] font-medium">Agent 待审核队列</h3>
        {selected.size > 0 && (
          <button
            onClick={handleBatchApprove}
            className="bg-green-600 text-white px-3 py-1 rounded text-[12px]"
          >
            批量批准 ({selected.size})
          </button>
        )}
      </div>

      {entries.length === 0 && (
        <div className="text-ew-gray-text text-[13px] py-8 text-center">暂无待审核条目</div>
      )}

      <div className="space-y-2">
        {entries.map((e) => (
          <div
            key={e.id}
            className={`bg-white border rounded-lg p-3 ${selected.has(e.id) ? "border-ew-blue bg-ew-blue-light" : ""} ${
              e.pii_flag ? "border-l-4 border-l-orange-400" : ""
            }`}
          >
            <div className="flex gap-2 items-center mb-1">
              <input
                type="checkbox"
                checked={selected.has(e.id)}
                onChange={() => toggleSelect(e.id)}
                className="shrink-0"
              />
              <span className="text-[11px] bg-gray-200 rounded px-1.5 py-0.5">{e.tool_name}</span>
              <span className="text-[11px] bg-blue-100 text-blue-700 rounded px-1.5 py-0.5">
                {typeLabels[e.entry_type] || e.entry_type}
              </span>
              {e.dedup_hint !== "none" && (
                <span className="text-[11px] bg-yellow-100 text-yellow-700 rounded px-1.5 py-0.5">重复</span>
              )}
              {e.pii_flag && (
                <span className="text-[11px] bg-red-100 text-red-700 rounded px-1.5 py-0.5">PII</span>
              )}
              <span className="text-[11px] text-ew-gray-text ml-auto">{e.created_at?.slice(0, 16)}</span>
            </div>

            <div className="text-[13px] mb-2 whitespace-pre-wrap">
              {editingId === e.id ? (
                <textarea
                  className="w-full border rounded p-1.5 text-[13px] min-h-[60px]"
                  value={editedContent}
                  onChange={(ev) => setEditedContent(ev.target.value)}
                />
              ) : (
                e.raw_content?.slice(0, 300)
              )}
            </div>

            <div className="flex gap-2">
              {editingId === e.id ? (
                <>
                  <button onClick={() => handleApprove(e.id)} className="text-[12px] bg-ew-blue text-white px-2 py-1 rounded">
                    确认修改并批准
                  </button>
                  <button onClick={() => setEditingId(null)} className="text-[12px] border px-2 py-1 rounded">
                    取消
                  </button>
                </>
              ) : (
                <>
                  <button onClick={() => handleApprove(e.id)} className="text-[12px] bg-green-600 text-white px-2 py-1 rounded">
                    批准
                  </button>
                  <button
                    onClick={() => {
                      setEditingId(e.id);
                      setEditedContent(e.raw_content);
                    }}
                    className="text-[12px] bg-ew-blue text-white px-2 py-1 rounded"
                  >
                    编辑后批准
                  </button>
                  {showRejectInput === e.id ? (
                    <>
                      <input
                        className="border rounded px-2 py-1 text-[12px] flex-1"
                        placeholder="驳回理由"
                        value={rejectReason[e.id] || ""}
                        onChange={(ev) => setRejectReason((prev) => ({ ...prev, [e.id]: ev.target.value }))}
                      />
                      <button onClick={() => handleReject(e.id)} className="text-[12px] bg-red-500 text-white px-2 py-1 rounded">
                        确认驳回
                      </button>
                      <button onClick={() => setShowRejectInput(null)} className="text-[12px] border px-2 py-1 rounded">
                        取消
                      </button>
                    </>
                  ) : (
                    <button
                      onClick={() => setShowRejectInput(e.id)}
                      className="text-[12px] border border-red-300 text-red-600 px-2 py-1 rounded hover:bg-red-50"
                    >
                      驳回
                    </button>
                  )}
                </>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
