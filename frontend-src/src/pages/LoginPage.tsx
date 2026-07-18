import { useState } from "react";
import { login, setToken } from "../api/client";

export default function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [demoMode, setDemoMode] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    try {
      const res = await login(email, password);
      setToken(res.token);
      onLogin();
    } catch (err: any) {
      // API不可用 → 演示模式
      if (email === "admin@local" && password === "admin123") {
        setToken("demo-token-" + Date.now());
        setDemoMode(true);
        setTimeout(() => onLogin(), 800);
      } else if (email === "demo" && password === "demo") {
        setToken("demo-token-" + Date.now());
        setDemoMode(true);
        setTimeout(() => onLogin(), 800);
      } else {
        setError("后端未连接。演示模式请输入 admin@local / admin123 或 demo / demo");
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ew-gray">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-sm border w-80">
        <h1 className="text-[18px] font-bold text-ew-blue mb-1">EasyWiki</h1>
        <p className="text-[11px] text-gray-400 mb-4">组织知识管理平台</p>
        {error && <div className="text-red-500 text-[12px] mb-2">{error}</div>}
        {demoMode && (
          <div className="text-green-600 text-[12px] mb-2">演示模式启动中...</div>
        )}
        <input
          className="w-full border rounded px-2 py-1.5 mb-2 text-[13px]"
          value={email} onChange={(e) => setEmail(e.target.value)} placeholder="Email"
        />
        <input
          type="password"
          className="w-full border rounded px-2 py-1.5 mb-3 text-[13px]"
          value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Password"
        />
        <button className="w-full bg-ew-blue text-white py-1.5 rounded text-[13px] hover:bg-ew-blue-dark">
          登录
        </button>
        <div className="mt-4 pt-3 border-t text-[11px] text-gray-400 text-center">
          演示账号：admin@local / admin123
        </div>
      </form>
    </div>
  );
}
