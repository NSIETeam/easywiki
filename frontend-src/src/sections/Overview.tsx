import { useEffect, useState } from "react";
import { getManifest } from "../api/client";

export default function Overview({ pid }: { pid: string }) {
  const [manifest, setManifest] = useState<any>(null);
  useEffect(() => { getManifest(pid).then(setManifest).catch(() => {}); }, [pid]);

  const health = "on_track";
  const hl: Record<string, string> = { on_track: "正常", at_risk: "风险", blocked: "受阻" };
  const hc: Record<string, string> = { on_track: "bg-green-100 text-green-800", at_risk: "bg-yellow-100 text-yellow-800", blocked: "bg-red-100 text-red-800" };

  return (
    <div className="space-y-4">
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-[15px] font-medium mb-3">项目健康状态</h3>
        <span className={`text-[13px] px-3 py-1 rounded-full font-medium ${hc[health]}`}>{hl[health]}</span>
      </div>
      <div className="bg-white border rounded-lg p-4">
        <h3 className="text-[15px] font-medium mb-3">项目结构</h3>
        <p className="text-[13px] text-ew-gray-text">{manifest?.sections?.length || 7} 个固定工作区栏位，支持页面树与审核流。</p>
      </div>
      <div className="bg-white border rounded-lg p-4">
        <div className="text-ew-gray-text text-[13px] py-4 text-center">暂无近期活动记录</div>
      </div>
    </div>
  );
}
