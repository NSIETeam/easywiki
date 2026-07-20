import { useEffect, useState } from "react";
import { detectAgents, connectAgent } from "../api/client";

export default function AgentActivityCenter() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [connecting, setConnecting] = useState<string | null>(null);
  const [messages, setMessages] = useState<Record<string, { ok: boolean; text: string }>>({});

  const load = () => {
    setLoading(true);
    detectAgents()
      .then((r) => { setAgents(r.agents || []); setLoading(false); })
      .catch(() => { setLoading(false); });
  };

  useEffect(() => { load(); }, []);

  const handleConnect = (agentType: string) => {
    setConnecting(agentType);
    connectAgent(agentType)
      .then((r) => {
        setMessages((m) => ({ ...m, [agentType]: { ok: true, text: r.message || "已连接" } }));
        load(); // refresh connection status
      })
      .catch((e) => {
        setMessages((m) => ({ ...m, [agentType]: { ok: false, text: String(e.message || e) } }));
      })
      .finally(() => setConnecting(null));
  };

  const handleConnectAll = () => {
    const unconnected = agents.filter((a) => !a.connected);
    unconnected.forEach((a, i) => {
      setTimeout(() => handleConnect(a.type), i * 500);
    });
  };

  const hasUnconnected = agents.some((a) => !a.connected);

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-[16px] font-bold">Agent 连接中心</h2>
        {hasUnconnected && (
          <button
            onClick={handleConnectAll}
            className="text-[13px] bg-ew-blue text-white rounded-lg px-4 py-1.5 hover:opacity-90 transition"
          >
            一键连接全部
          </button>
        )}
      </div>

      {/* Intro card */}
      <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border border-blue-100 rounded-xl p-5 mb-5">
        <div className="flex items-start gap-3">
          <div className="text-[28px]">🔌</div>
          <div>
            <h3 className="text-[14px] font-semibold text-gray-800 mb-1">
              连接你的 AI Agent，开启自动知识沉淀
            </h3>
            <p className="text-[13px] text-gray-500 leading-relaxed">
              点击下方按钮即可一键连接。连接后，Agent 在每次工作结束时自动提取决策和经验沉淀到 EasyWiki，
              下次开始类似任务时自动召回相关记忆。无需手动操作。
            </p>
          </div>
        </div>
      </div>

      {/* Agent list */}
      {loading ? (
        <div className="text-[13px] text-gray-400 text-center py-12">正在检测本机已安装的 Agent...</div>
      ) : agents.length === 0 ? (
        <div className="bg-white border rounded-xl p-12 text-center">
          <div className="text-[40px] mb-3">🔍</div>
          <h3 className="text-[14px] font-medium text-gray-600 mb-1">未检测到 AI Agent</h3>
          <p className="text-[12px] text-gray-400">
            请先安装 Claude Code、Codex 或其他 MCP 兼容的 Agent 工具
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {agents.map((agent) => {
            const msg = messages[agent.type];
            const isConnecting = connecting === agent.type;
            return (
              <div
                key={agent.type}
                className="bg-white border rounded-xl p-4 flex items-center justify-between"
              >
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-lg bg-gray-100 flex items-center justify-center text-[18px]">
                    {agent.type === "claude-code" ? "🤖" :
                     agent.type === "codex" ? "📦" :
                     agent.type === "easycode" ? "⚡" :
                     agent.type === "cursor" ? "🖱️" : "🔧"}
                  </div>
                  <div>
                    <div className="text-[14px] font-medium text-gray-800">{agent.name}</div>
                    <div className="text-[12px] text-gray-400">
                      {agent.connected ? (
                        <span className="text-green-600">● 已连接</span>
                      ) : agent.binary ? (
                        <span>已检测到，未连接</span>
                      ) : (
                        <span>检测到配置文件</span>
                      )}
                    </div>
                    {agent.config_path && (
                      <div className="text-[10px] text-gray-300 mt-0.5 truncate max-w-[200px]">
                        {agent.config_path}
                      </div>
                    )}
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  {msg && (
                    <span className={`text-[11px] ${msg.ok ? "text-green-600" : "text-red-500"}`}>
                      {msg.text}
                    </span>
                  )}
                  {agent.connected ? (
                    <span className="text-[12px] text-green-600 bg-green-50 rounded px-3 py-1">
                      ✓ 已连接
                    </span>
                  ) : (
                    <button
                      onClick={() => handleConnect(agent.type)}
                      disabled={isConnecting}
                      className="text-[12px] bg-ew-blue text-white rounded-lg px-4 py-1.5 hover:opacity-90 transition disabled:opacity-50"
                    >
                      {isConnecting ? "连接中..." : "一键连接"}
                    </button>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* How it works */}
      <div className="mt-6 bg-gray-50 rounded-xl p-5">
        <h4 className="text-[13px] font-medium text-gray-600 mb-3">连接后会发生什么？</h4>
        <div className="space-y-2">
          <div className="flex items-start gap-2">
            <span className="text-[14px]">1.</span>
            <span className="text-[12px] text-gray-500">Agent 每次会话结束时，自动提取决策、Bug修复、最佳实践</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-[14px]">2.</span>
            <span className="text-[12px] text-gray-500">高置信度知识自动入库，低置信度进入待审队列</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-[14px]">3.</span>
            <span className="text-[12px] text-gray-500">下次开始类似任务时，Agent 自动召回相关历史记忆</span>
          </div>
          <div className="flex items-start gap-2">
            <span className="text-[14px]">4.</span>
            <span className="text-[12px] text-gray-500">重复出现的模式自动生成 Skill 草稿，经审核后可复用</span>
          </div>
        </div>
      </div>
    </div>
  );
}
