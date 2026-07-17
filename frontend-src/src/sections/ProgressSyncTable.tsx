import { useEffect, useState } from "react";
import { getManifest } from "../api/client";

export default function ProgressSyncTable({ pid }: { pid: string }) {
  const [fields, setFields] = useState<any[]>([]);
  useEffect(() => { getManifest(pid).then(m => setFields(m.progress_fields || [])).catch(() => {}); }, [pid]);

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
