import { useEffect, useState } from "react";
import { getManifest } from "../api/client";

const DEMO_ACTIVITIES = [
  { time: "2026-07-18 10:30", user: "张三", action: "创建了页面", target: "技术架构设计" },
  { time: "2026-07-18 09:15", user: "李四", action: "审核通过", target: "API 接口文档" },
  { time: "2026-07-17 16:45", user: "Agent", action: "自动记录决策", target: "前端技术选型" },
  { time: "2026-07-17 14:20", user: "王五", action: "更新了", target: "部署流程" },
  { time: "2026-07-16 11:00", user: "Agent", action: "检测到冲突", target: "数据库设计方案" },
];

export default function Overview({ pid }: { pid: string }) {
  const [manifest, setManifest] = useState<any>(null);
  const [activities, setActivities] = useState<any[]>([]);
  useEffect(() => {
    getManifest(pid).then(setManifest).catch(() => setManifest({ sections: ["概览", "决策", "知识图谱", "Agent", "文件", "进度", "Inbox"] }));
    setActivities(DEMO_ACTIVITIES);
  }, [pid]);

  const health = "on_track";
  const hl: Record<string, string> = { on_track: "正常", at_risk: "风险", blocked: "受阻" };
  const hc: Record<string, string> = { on_track: "bg-green-100 text-green-800", at_risk: "bg-yellow-100 text-yellow-800", blocked: "bg-red-100 text-red-800" };

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-[15px] font-medium mb-3">项目健康状态</h3>
        <div className="flex items-center gap-4">
          <span className={`text-[13px] px-3 py-1 rounded-full font-medium ${hc[health]}`}>{hl[health]}</span>
          <span className="text-[12px] text-ew-gray-text">页面数: 24 · 成员: 5 · 待审核: 4</span>
        </div>
      </div>
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-[15px] font-medium mb-3">项目结构</h3>
        <p className="text-[13px] text-ew-gray-text">{manifest?.sections?.length || 7} 个固定工作区栏位，支持页面树与审核流。</p>
        <div className="flex gap-2 mt-2 flex-wrap">
          {(manifest?.sections || ["概览", "决策", "知识图谱", "Agent", "文件", "进度", "Inbox"]).map((s: string, i: number) => (
            <span key={i} className="text-[11px] bg-gray-100 rounded px-2 py-1">{s}</span>
          ))}
        </div>
      </div>
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-[15px] font-medium mb-3">近期活动</h3>
        <div className="space-y-2">
          {activities.map((a, i) => (
            <div key={i} className="flex items-center text-[13px] py-1 border-b border-gray-50 last:border-0">
              <span className="text-[11px] text-gray-400 w-32 shrink-0">{a.time}</span>
              <span className="font-medium text-ew-blue w-16 shrink-0">{a.user}</span>
              <span className="text-ew-gray-text">{a.action}</span>
              <span className="ml-1 text-gray-800 font-medium">{a.target}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
