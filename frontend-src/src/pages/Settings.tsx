import { useState, useEffect, useCallback } from "react";
import {
  listCloneMounts, createCloneMount, removeCloneMount,
  listRemotes, addRemote, removeRemote, syncPull, syncPush, getChangeLog,
  listProjects, listPages,
} from "../api/client";

export default function Settings() {
  const [active, setActive] = useState("agent");

  return (
    <div>
      <h2 className="text-[16px] font-bold mb-4">⚙️ 设置</h2>
      <div className="flex gap-1 mb-4 border-b border-ew-gray-border">
        {[
          { key: "agent", label: "Agent 配置" },
          { key: "mcp", label: "MCP 连接" },
          { key: "clone", label: "知识分发" },
          { key: "sync", label: "跨实例同步" },
          { key: "general", label: "通用" },
        ].map((t) => (
          <button key={t.key} onClick={() => setActive(t.key)}
            className={`px-3 py-2 text-[13px] border-b-2 -mb-[1px] ${active === t.key ? "border-ew-blue text-ew-blue" : "border-transparent text-ew-gray-text"}`}>
            {t.label}
          </button>
        ))}
      </div>
      {active === "agent" && <AgentTab />}
      {active === "mcp" && <McpTab />}
      {active === "clone" && <CloneMountTab />}
      {active === "sync" && <SyncTab />}
      {active === "general" && <GeneralTab />}
    </div>
  );
}

function AgentTab() {
  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-[15px] font-medium mb-3">已启用的 Agent 工具</h3>
      <div className="text-[13px] text-ew-gray-text">本机已检测到的工具会在此处显示。在项目设置中启用对应工具的 MCP 连接后，Agent 可自动向 EasyWiki 上报工作过程。</div>
    </div>
  );
}

function McpTab() {
  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-[15px] font-medium mb-3">MCP 连接状态</h3>
      <div className="text-[13px] text-ew-gray-text">EasyWiki MCP Server 默认运行在本机，监听 stdio。各 Agent 工具通过各自配置文件中的 mcpServers.easywiki 条目连接。</div>
    </div>
  );
}

function GeneralTab() {
  return (
    <div className="bg-white border rounded-lg p-4">
      <h3 className="text-[15px] font-medium mb-3">通用设置</h3>
      <p className="text-[13px] text-ew-gray-text">更多设置项即将上线</p>
    </div>
  );
}

// ══════════════════════════════════════════════════
// Phase 2: Clone Mount — 跨项目知识分发
// ══════════════════════════════════════════════════

function CloneMountTab() {
  const [projects, setProjects] = useState<any[]>([]);
  const [selectedProject, setSelectedProject] = useState("");
  const [mounts, setMounts] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [sourcePages, setSourcePages] = useState<any[]>([]);
  const [sourceProjectId, setSourceProjectId] = useState("");
  const [sourceSection, setSourceSection] = useState("decisions");
  const [sourcePageId, setSourcePageId] = useState("");
  const [targetSection, setTargetSection] = useState("decisions");
  const [msg, setMsg] = useState("");

  useEffect(() => {
    listProjects().then(r => {
      const ps = r.projects || r;
      setProjects(ps);
      if (ps.length > 0) setSelectedProject(ps[0].id);
    }).catch(() => {});
  }, []);

  const loadMounts = useCallback(async (pid: string) => {
    if (!pid) return;
    setLoading(true);
    try {
      const m = await listCloneMounts(pid);
      setMounts(Array.isArray(m) ? m : []);
    } catch { setMounts([]); }
    setLoading(false);
  }, []);

  useEffect(() => { loadMounts(selectedProject); }, [selectedProject, loadMounts]);

  async function loadSourcePages(pid: string, section: string) {
    try {
      const r = await listPages(pid, section);
      setSourcePages(r.pages || []);
    } catch { setSourcePages([]); }
  }

  async function handleAdd() {
    if (!selectedProject || !sourcePageId || !targetSection) return;
    try {
      await createCloneMount(selectedProject, sourcePageId, targetSection);
      setMsg("✅ 克隆挂载已创建");
      setShowAdd(false);
      setSourcePageId("");
      loadMounts(selectedProject);
    } catch (e: any) {
      setMsg("❌ " + e.message);
    }
  }

  async function handleRemove(mid: string) {
    if (!confirm("确认移除此克隆挂载？")) return;
    try {
      await removeCloneMount(mid);
      loadMounts(selectedProject);
    } catch (e: any) {
      setMsg("❌ " + e.message);
    }
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-medium">知识分发 — 跨项目克隆挂载</h3>
        <button onClick={() => setShowAdd(!showAdd)}
          className="px-3 py-1.5 text-[12px] bg-ew-blue text-white rounded hover:opacity-90">
          {showAdd ? "取消" : "+ 添加挂载"}
        </button>
      </div>
      <p className="text-[12px] text-ew-gray-text">
        将其他项目的页面克隆挂载到当前项目，源页面更新时所有挂载点同步生效（Trilium-style）。
      </p>

      <select value={selectedProject} onChange={e => setSelectedProject(e.target.value)}
        className="border rounded px-2 py-1 text-[13px]">
        {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
      </select>

      {showAdd && (
        <div className="bg-white border rounded-lg p-3 space-y-2">
          <div className="text-[13px] font-medium">新建克隆挂载</div>
          <div className="grid grid-cols-2 gap-2">
            <label className="text-[12px]">源项目
              <select value={sourceProjectId} onChange={e => { setSourceProjectId(e.target.value); loadSourcePages(e.target.value, sourceSection); }}
                className="border rounded px-2 py-1 text-[13px] w-full">
                <option value="">选择项目...</option>
                {projects.map(p => <option key={p.id} value={p.id}>{p.name}</option>)}
              </select>
            </label>
            <label className="text-[12px]">源分区
              <select value={sourceSection} onChange={e => { setSourceSection(e.target.value); if (sourceProjectId) loadSourcePages(sourceProjectId, e.target.value); }}
                className="border rounded px-2 py-1 text-[13px] w-full">
                <option value="decisions">决策记录</option>
                <option value="experiences">经验总结</option>
                <option value="sop">标准流程</option>
              </select>
            </label>
          </div>
          <label className="text-[12px] block">源页面
            <select value={sourcePageId} onChange={e => setSourcePageId(e.target.value)}
              className="border rounded px-2 py-1 text-[13px] w-full">
              <option value="">选择页面...</option>
              {sourcePages.map(p => <option key={p.id} value={p.id}>{p.title}</option>)}
            </select>
          </label>
          <label className="text-[12px] block">挂载到分区
            <select value={targetSection} onChange={e => setTargetSection(e.target.value)}
              className="border rounded px-2 py-1 text-[13px] w-full">
              <option value="decisions">决策记录</option>
              <option value="experiences">经验总结</option>
              <option value="sop">标准流程</option>
            </select>
          </label>
          <button onClick={handleAdd} className="px-3 py-1.5 text-[12px] bg-ew-blue text-white rounded hover:opacity-90">
            确认创建
          </button>
        </div>
      )}

      {msg && <div className="text-[12px] text-ew-blue">{msg}</div>}

      {loading ? (
        <div className="text-[13px] text-ew-gray-text">加载中...</div>
      ) : mounts.length === 0 ? (
        <div className="bg-white border rounded-lg p-4 text-[13px] text-ew-gray-text">暂无克隆挂载</div>
      ) : (
        <div className="space-y-2">
          {mounts.map(m => (
            <div key={m.id} className="bg-white border rounded-lg p-3 flex items-center justify-between">
              <div>
                <div className="text-[13px] font-medium">{m.page_title || "未知页面"}</div>
                <div className="text-[11px] text-ew-gray-text">
                  来源: {m.source_project_id} → 分区: {m.target_section}
                </div>
              </div>
              <button onClick={() => handleRemove(m.id)}
                className="px-2 py-1 text-[12px] text-red-500 border border-red-200 rounded hover:bg-red-50">
                移除
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// ══════════════════════════════════════════════════
// Phase 3: Cross-instance Sync
// ══════════════════════════════════════════════════

function SyncTab() {
  const [remotes, setRemotes] = useState<any[]>([]);
  const [logs, setLogs] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [name, setName] = useState("");
  const [url, setUrl] = useState("");
  const [authToken, setAuthToken] = useState("");
  const [direction, setDirection] = useState("pull");
  const [msg, setMsg] = useState("");

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [r, l] = await Promise.all([listRemotes(), getChangeLog()]);
      setRemotes(Array.isArray(r) ? r : []);
      setLogs(Array.isArray(l) ? l : []);
    } catch {}
    setLoading(false);
  }, []);

  useEffect(() => { load(); }, [load]);

  async function handleAdd() {
    if (!name || !url) return;
    try {
      await addRemote(name, url, authToken, direction);
      setMsg("✅ 远程实例已添加");
      setShowAdd(false);
      setName(""); setUrl(""); setAuthToken("");
      load();
    } catch (e: any) { setMsg("❌ " + e.message); }
  }

  async function handleRemove(rid: string) {
    if (!confirm("确认删除此远程实例？")) return;
    try { await removeRemote(rid); load(); } catch {}
  }

  async function handleSync(action: "pull" | "push") {
    setMsg(action === "pull" ? "⏳ 正在拉取..." : "⏳ 正在推送...");
    try {
      const fn = action === "pull" ? syncPull : syncPush;
      const r = await fn();
      setMsg(`✅ ${action === "pull" ? "拉取" : "推送"}完成: ${JSON.stringify(r.results || r)}`);
      load();
    } catch (e: any) { setMsg("❌ " + e.message); }
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h3 className="text-[15px] font-medium">跨实例同步</h3>
        <div className="flex gap-2">
          <button onClick={() => handleSync("pull")} className="px-3 py-1.5 text-[12px] bg-ew-blue text-white rounded hover:opacity-90">
            ⬇ 拉取
          </button>
          <button onClick={() => handleSync("push")} className="px-3 py-1.5 text-[12px] border rounded hover:bg-gray-50">
            ⬆ 推送
          </button>
          <button onClick={() => setShowAdd(!showAdd)} className="px-3 py-1.5 text-[12px] border rounded hover:bg-gray-50">
            {showAdd ? "取消" : "+ 添加实例"}
          </button>
        </div>
      </div>

      {msg && <div className="text-[12px] text-ew-blue">{msg}</div>}

      {showAdd && (
        <div className="bg-white border rounded-lg p-3 space-y-2">
          <div className="text-[13px] font-medium">添加远程实例</div>
          <input value={name} onChange={e => setName(e.target.value)} placeholder="名称 (如: 研发部实例)"
            className="border rounded px-2 py-1 text-[13px] w-full" />
          <input value={url} onChange={e => setUrl(e.target.value)} placeholder="URL (如: http://10.0.1.5:8080)"
            className="border rounded px-2 py-1 text-[13px] w-full" />
          <input value={authToken} onChange={e => setAuthToken(e.target.value)} placeholder="Auth Token (可选)"
            className="border rounded px-2 py-1 text-[13px] w-full" />
          <select value={direction} onChange={e => setDirection(e.target.value)}
            className="border rounded px-2 py-1 text-[13px]">
            <option value="pull">仅拉取 (pull)</option>
            <option value="push">仅推送 (push)</option>
            <option value="both">双向 (both)</option>
          </select>
          <button onClick={handleAdd} className="px-3 py-1.5 text-[12px] bg-ew-blue text-white rounded hover:opacity-90">
            确认添加
          </button>
        </div>
      )}

      {loading ? (
        <div className="text-[13px] text-ew-gray-text">加载中...</div>
      ) : remotes.length === 0 ? (
        <div className="bg-white border rounded-lg p-4 text-[13px] text-ew-gray-text">
          暂无远程实例。点击「+ 添加实例」配置对端 EasyWiki。
        </div>
      ) : (
        <div className="space-y-2">
          {remotes.map(r => (
            <div key={r.id} className="bg-white border rounded-lg p-3 flex items-center justify-between">
              <div>
                <div className="text-[13px] font-medium">{r.name}</div>
                <div className="text-[11px] text-ew-gray-text">
                  {r.url} · {r.sync_direction} · {r.last_sync_at ? `上次同步: ${r.last_sync_at}` : "未同步"}
                </div>
              </div>
              <button onClick={() => handleRemove(r.id)}
                className="px-2 py-1 text-[12px] text-red-500 border border-red-200 rounded hover:bg-red-50">
                删除
              </button>
            </div>
          ))}
        </div>
      )}

      <div>
        <h4 className="text-[14px] font-medium mb-2">变更日志</h4>
        {logs.length === 0 ? (
          <div className="bg-white border rounded-lg p-3 text-[12px] text-ew-gray-text">暂无变更记录</div>
        ) : (
          <div className="bg-white border rounded-lg p-3 max-h-48 overflow-auto space-y-1">
            {logs.slice(0, 50).map((l, i) => (
              <div key={l.id || i} className="text-[11px] text-ew-gray-text border-b border-gray-50 pb-1">
                <span className="font-mono">{l.created_at}</span> · {l.action} · {l.resource_type} · {l.resource_id?.slice(0, 8)}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
