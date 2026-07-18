const DEMO_FILES = [
  { name: "技术架构设计.md", size: "12.4 KB", author: "张三", updated: "2026-07-18" },
  { name: "API接口文档.md", size: "8.2 KB", author: "李四", updated: "2026-07-17" },
  { name: "部署流程.md", size: "5.1 KB", author: "王五", updated: "2026-07-17" },
  { name: "数据库设计.md", size: "15.7 KB", author: "张三", updated: "2026-07-16" },
  { name: "会议纪要-周会.zip", size: "2.3 KB", author: "李四", updated: "2026-07-15" },
  { name: "需求规格说明书.pdf", size: "324 KB", author: "王五", updated: "2026-07-14" },
];

export default function Files(_props: { pid: string }) {
  return (
    <div>
      <h3 className="text-[15px] font-medium mb-3">文件中心</h3>
      <div className="bg-white border rounded-lg overflow-hidden">
        <table className="w-full text-[13px]">
          <thead>
            <tr className="bg-gray-50 border-b">
              <th className="text-left px-4 py-2 font-medium text-ew-gray-text">文件名</th>
              <th className="text-left px-4 py-2 font-medium text-ew-gray-text">大小</th>
              <th className="text-left px-4 py-2 font-medium text-ew-gray-text">作者</th>
              <th className="text-left px-4 py-2 font-medium text-ew-gray-text">更新时间</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_FILES.map((f, i) => (
              <tr key={i} className="border-b last:border-0 hover:bg-gray-50">
                <td className="px-4 py-2 text-ew-blue font-medium">{f.name}</td>
                <td className="px-4 py-2 text-ew-gray-text">{f.size}</td>
                <td className="px-4 py-2">{f.author}</td>
                <td className="px-4 py-2 text-ew-gray-text">{f.updated}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
