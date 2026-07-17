import { useEffect, useState } from "react";
import { request } from "../api/client";

export default function AgentsSkills({ pid }: { pid: string }) {
  const [skills, setSkills] = useState<any[]>([]);
  useEffect(() => {
    request("POST", "/api/v1/skill/match", { query: "", top_k: 20 })
      .then((r: any) => setSkills(r.matched || []))
      .catch(() => {});
  }, [pid]);

  return (
    <div>
      <h3 className="text-[15px] font-medium mb-3">Agent 与 Skill 库</h3>
      {skills.length === 0 ? (
        <div className="text-ew-gray-text text-[13px] py-8 text-center">暂无可用 Skill</div>
      ) : (
        <div className="grid grid-cols-2 gap-3">
          {skills.map((s: any, i: number) => (
            <div key={s.id || i} className="bg-white border rounded-lg p-3">
              <div className="font-medium text-[13px]">{s.name}</div>
              <div className="text-[12px] text-ew-gray-text mt-1">{s.description}</div>
              <span className="text-[10px] bg-blue-100 text-blue-700 rounded px-1.5 mt-1 inline-block">{s.object_type}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
