import { useState } from "react";
import { login, setToken } from "../api/client";

export default function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const res = await login(email, password);
      setToken(res.token);
      onLogin();
    } catch (err: any) {
      setError(err.message);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-ew-gray">
      <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-sm border w-80">
        <h1 className="text-[18px] font-bold text-ew-blue mb-4">EasyWiki</h1>
        {error && <div className="text-red-500 text-[12px] mb-2">{error}</div>}
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
      </form>
    </div>
  );
}
