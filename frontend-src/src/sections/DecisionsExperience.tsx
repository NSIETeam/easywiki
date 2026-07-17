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

  const loadPages = () => listPages(pid, SECTION).then((r) => setPages(r.pages));

  useEffect(() => { loadPages(); }, [pid]);

  const handleCreate = async () => {
    if (!newTitle.trim()) return;
    await createPage(pid, SECTION, newTitle);
    setNewTitle("");
    loadPages();
  };

  const handleSelect = async (pageId: string) => {
    const p = await getPage(pageId);
    setSelectedPage(p);
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
