import { useEffect, useState } from "react";
import { listProjects, createProject } from "../api/client";

export default function ProjectList() {
  const [projects, setProjects] = useState<any[]>([]);
  const [name, setName] = useState("");

  const load = () => listProjects().then((r) => setProjects(r.projects));

  useEffect(() => { load(); }, []);

  const handleCreate = async () => {
    if (!name.trim()) return;
    await createProject(name);
    setName("");
    load();
  };

  return (
    <div>
      <h2 className="text-[16px] font-bold mb-4">我的项目</h2>
      <div className="flex gap-2 mb-4">
        <input
          className="border rounded px-2 py-1.5 text-[13px] w-64"
          value={name}
          onChange={(e) => setName(e.target.value)}
          placeholder="新项目名称"
          onKeyDown={(e) => e.key === "Enter" && handleCreate()}
        />
        <button onClick={handleCreate} className="bg-ew-blue text-white px-3 py-1.5 rounded text-[13px] hover:bg-ew-blue-dark">
          创建项目
        </button>
      </div>
      <div className="grid grid-cols-3 gap-3">
        {projects.map((p) => (
          <a
            key={p.id}
            href={`/project/${p.id}`}
            className="block bg-white border rounded-lg p-4 no-underline hover:shadow-md"
          >
            <div className="font-medium text-[14px] text-ew-blue">{p.name}</div>
            <div className="text-[12px] text-ew-gray-text mt-1">
              {p.health === "on_track" ? "✅ 正常" : p.health === "at_risk" ? "⚠️ 风险" : "🔴 受阻"}
              <span className="ml-2">{p.created_at?.slice(0, 10)}</span>
            </div>
          </a>
        ))}
      </div>
    </div>
  );
}
