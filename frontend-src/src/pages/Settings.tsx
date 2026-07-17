import { useState } from "react";

export default function Settings() {
  const [active, setActive] = useState("agent");

  return (
    <div>
      <h2 className="text-[16px] font-bold mb-4">⚙️ 设置</h2>
      <div className="flex gap-1 mb-4 border-b border-ew-gray-border">
        {[{key:"agent",label:"Agent 配置"},{key:"mcp",label:"MCP 连接"},{key:"general",label:"通用"}].map(t => (
          <button key={t.key} onClick={() => setActive(t.key)}
            className={`px-3 py-2 text-[13px] border-b-2 -mb-[1px] ${active===t.key?"border-ew-blue text-ew-blue":"border-transparent text-ew-gray-text"}`}>
            {t.label}
          </button>
        ))}
      </div>
      {active === "agent" && (
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-[15px] font-medium mb-3">已启用的 Agent 工具</h3>
          <div className="text-[13px] text-ew-gray-text">本机已检测到的工具会在此处显示。在项目设置中启用对应工具的 MCP 连接后，Agent 可自动向 EasyWiki 上报工作过程。</div>
        </div>
      )}
      {active === "mcp" && (
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-[15px] font-medium mb-3">MCP 连接状态</h3>
          <div className="text-[13px] text-ew-gray-text">EasyWiki MCP Server 默认运行在本机，监听 stdio。各 Agent 工具通过各自配置文件中的 mcpServers.easywiki 条目连接。</div>
        </div>
      )}
      {active === "general" && (
        <div className="bg-white border rounded-lg p-4">
          <h3 className="text-[15px] font-medium mb-3">通用设置</h3>
          <p className="text-[13px] text-ew-gray-text">更多设置项即将上线</p>
        </div>
      )}
    </div>
  );
}
