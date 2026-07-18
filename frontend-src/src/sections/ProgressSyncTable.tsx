import { useEffect, useState } from "react";
import { getManifest } from "../api/client";

export default function ProgressSyncTable({ pid }: { pid: string }) {
  const [fields, setFields] = useState<any[]>([]);
  const DEMO_FIELDS = [
    { field_name: "项目阶段", field_type: "text", current_value: "开发中" },
    { field_name: "完成度", field_type: "percentage", current_value: "65%" },
    { field_name: "预计上线", field_type: "date", current_value: "2026-07-25" },
    { field_name: "负责人", field_type: "text", current_value: "张三" },
    { field_name: "风险等级", field_type: "enum", current_value: "低" },
    { field_name: "本周里程碑", field_type: "text", current_value: "API 接口联调完成" },
  ];

  useEffect(() => { getManifest(pid).then(m => setFields(m.progress_fields || [])).catch(() => setFields(DEMO_FIELDS)); }, [pid]);

  return (
    <div>
      <h3 className="text-[15px] font-medium mb-3">进度同步表</h3>
      {fields.length === 0 ? (
        <div className="text-ew-gray-text text-[13px] py-8 text-center">暂无进度字段</div>
      ) : (
        <div className="bg-white border rounded-lg overflow-hidden">
          <table className="w-full text-[13px]">
            <thead className="bg-ew-gray border-b">
              <tr>
                <th className="text-left px-3 py-2">字段</th>
                <th className="text-left px-3 py-2">类型</th>
                <th className="text-left px-3 py-2">当前值</th>
              </tr>
            </thead>
            <tbody>
              {fields.map((f: any, i: number) => (
                <tr key={i} className="border-b last:border-b-0">
                  <td className="px-3 py-2">{f.field_name}</td>
                  <td className="px-3 py-2 text-ew-gray-text">{f.field_type}</td>
                  <td className="px-3 py-2">{f.current_value || "—"}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
