import { useParams } from "react-router-dom";
import Overview from "../sections/Overview";
import DecisionsExperience from "../sections/DecisionsExperience";
import KnowledgeGraphView from "../sections/KnowledgeGraphView";
import AgentsSkills from "../sections/AgentsSkills";
import Files from "../sections/Files";
import ProgressSyncTable from "../sections/ProgressSyncTable";
import AgentInbox from "../sections/AgentInbox";
import { useState } from "react";

const SECTIONS = [
  { key: "overview", label: "概览" },
  { key: "decisions_experience", label: "决策与经验" },
  { key: "knowledge_graph", label: "知识图谱" },
  { key: "agents_skills", label: "Agent与Skill" },
  { key: "files", label: "文件" },
  { key: "progress_table", label: "进度表" },
  { key: "agent_inbox", label: "Agent Inbox" },
];

export default function ProjectWorkspace() {
  const { projectId } = useParams<{ projectId: string }>();
  const [active, setActive] = useState(SECTIONS[0].key);

  if (!projectId) return null;

  return (
    <div className="flex flex-col h-full">
      {/* Tab bar */}
      <div className="flex gap-0 border-b border-ew-gray-border mb-3">
        {SECTIONS.map((s) => (
          <button
            key={s.key}
            onClick={() => setActive(s.key)}
            className={`px-3 py-2 text-[13px] border-b-2 -mb-[1px] ${
              active === s.key
                ? "border-ew-blue text-ew-blue font-medium"
                : "border-transparent text-ew-gray-text hover:text-gray-700"
            }`}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Section content */}
      <div className="flex-1 overflow-auto">
        {active === "overview" && <Overview pid={projectId} />}
        {active === "decisions_experience" && <DecisionsExperience pid={projectId} />}
        {active === "knowledge_graph" && <KnowledgeGraphView pid={projectId} />}
        {active === "agents_skills" && <AgentsSkills pid={projectId} />}
        {active === "files" && <Files pid={projectId} />}
        {active === "progress_table" && <ProgressSyncTable pid={projectId} />}
        {active === "agent_inbox" && <AgentInbox pid={projectId} />}
      </div>
    </div>
  );
}
