import { useEffect, useState } from "react";
import { request } from "../api/client";

export default function AgentsSkills({ pid }: { pid: string }) {
  const [skills, setSkills] = useState<any[]>([]);
  const DEMO_SKILLS = [
    { id: "s1", name: "自动生成 API 文档", description: "从代码注释自动生成 OpenAPI 3.0 规范文档", object_type: "tool" },
    { id: "s2", name: "数据库 Schema 审查", description: "检查 SQL DDL 语句的索引覆盖、范式合规、命名规范", object_type: "tool" },
    { id: "s3", name: "会议纪要提取", description: "从会议录音转写文本中提取决策、行动项和负责人", object_type: "agent" },
    { id: "s4", name: "代码冲突检测", description: "检测多人并发编辑时的内容冲突并提供合并建议", object_type: "agent" },
    { id: "s5", name: "知识图谱构建", description: "从文档中自动抽取实体关系并构建可视化图谱", object_type: "agent" },
    { id: "s6", name: "安全漏洞扫描", description: "扫描代码中的 XSS、SQL注入、路径遍历等常见漏洞", object_type: "tool" },
  ];

  useEffect(() => {
    request("POST", "/api/v1/skill/match", { query: "", top_k: 20 })
      .then((r: any) => setSkills(r.matched || []))
      .catch(() => setSkills(DEMO_SKILLS));
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
