import { useEffect, useState, useRef } from "react";
import { listPages, createPage, getPage, updatePage } from "../api/client";
import BlockSuiteEditor from "../editor/BlockSuiteEditor";
import type { BlockSuiteEditorHandle } from "../editor/BlockSuiteEditor";

const SECTION = "decisions_experience";

export default function DecisionsExperience({ pid }: { pid: string }) {
  const [pages, setPages] = useState<any[]>([]);
  const [newTitle, setNewTitle] = useState("");
  const [selectedPage, setSelectedPage] = useState<any>(null);
  const [saving, setSaving] = useState(false);
  const [saveError, setSaveError] = useState<string | null>(null);
  const editorRef = useRef<BlockSuiteEditorHandle>(null);

  const DEMO_PAGES = [
    { id: "p1", title: "前端技术选型：React 19 + Vite" },
    { id: "p2", title: "数据库方案：SQLite WAL vs PostgreSQL" },
    { id: "p3", title: "部署架构：Docker + Caddy 反向代理" },
    { id: "p4", title: "API 设计规范：RESTful + JWT 认证" },
  ];

  const loadPages = () => {
    listPages(pid, SECTION).then((r) => setPages(r.pages)).catch(() => setPages(DEMO_PAGES));
  };

  useEffect(() => { loadPages(); }, [pid]);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    try { await createPage(pid, SECTION, newTitle); }
    catch { setPages([...pages, { id: "demo" + Date.now(), title: newTitle }]); }
    setNewTitle("");
    loadPages();
  };

  const handleSelect = async (pageId: string) => {
    try {
      const p = await getPage(pageId);
      setSelectedPage(p);
    } catch {
      const p = pages.find(x => x.id === pageId);
      setSelectedPage({ ...p, blocksuite_doc: "# " + (p?.title || "页面") + "\n\n这是一个演示页面。连接后端后即可编辑保存。\n\n## 内容\n\n- 演示模式运行中\n- 所有操作仅在本地生效\n- 刷新后重置", current_version_id: "demo" });
    }
    setSaveError(null);
  };

  const handleSave = async () => {
    if (!selectedPage || !editorRef.current) return;
    setSaving(true);
    setSaveError(null);
    try {
      const doc = editorRef.current.serialize();
      const res = await updatePage(selectedPage.id, doc, selectedPage.current_version_id);
      setSelectedPage((prev: any) => ({ ...prev, current_version_id: res.version_id }));
      if (res.merged_content) {
        setSaveError("检测到并发编辑，已自动合并不重叠的改动");
      }
    } catch (e: any) {
      setSaveError(e.message || "保存失败（可能存在编辑冲突）");
    }
    setSaving(false);
  };

  return (
    <div className="flex gap-4 h-full">
      {/* Page tree */}
      <div className="w-56 shrink-0 border-r pr-3">
        <h4 className="text-[13px] font-medium mb-2">页面</h4>
        <div className="flex gap-1 mb-3">
          <input
            className="border rounded px-2 py-1 text-[12px] flex-1"
            value={newTitle}
            onChange={(e) => setNewTitle(e.target.value)}
            placeholder="新建页面..."
            onKeyDown={(e) => e.key === "Enter" && handleCreate()}
          />
          <button onClick={handleCreate} className="text-[12px] bg-ew-blue text-white px-2 rounded">+</button>
        </div>
        {pages.map((p) => (
          <div
            key={p.id}
            onClick={() => handleSelect(p.id)}
            className={`text-[13px] px-2 py-1 rounded cursor-pointer ${
              selectedPage?.id === p.id ? "bg-ew-blue-light text-ew-blue" : "hover:bg-gray-100"
            }`}
          >
            {p.title}
            {p.is_clone_of && <span className="text-[10px] text-ew-gray-text ml-1">[共享]</span>}
          </div>
        ))}
      </div>

      {/* Editor */}
      <div className="flex-1 flex flex-col">
        {selectedPage ? (
          <>
            <div className="flex justify-between items-center mb-2">
              <h3 className="text-[14px] font-medium">{selectedPage.title}</h3>
              <div className="flex items-center gap-2">
                {saveError && <span className="text-[12px] text-orange-600">{saveError}</span>}
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className="text-[12px] bg-ew-blue text-white px-3 py-1 rounded disabled:opacity-50"
                >
                  {saving ? "保存中..." : "保存"}
                </button>
              </div>
            </div>
            <div className="flex-1">
              <BlockSuiteEditor
                key={selectedPage.id}
                ref={editorRef}
                initialDoc={selectedPage.blocksuite_doc || ""}
              />
            </div>
          </>
        ) : (
          <div className="text-ew-gray-text text-[13px] py-8 text-center">选择一个页面开始编辑</div>
        )}
      </div>
    </div>
  );
}
