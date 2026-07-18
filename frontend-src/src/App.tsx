import { useState } from "react";
import { HashRouter, Routes, Route, Navigate } from "react-router-dom";
import { getToken } from "./api/client";
import LoginPage from "./pages/LoginPage";
import ProjectList from "./pages/ProjectList";
import ProjectWorkspace from "./pages/ProjectWorkspace";
import OrgKnowledgeBase from "./pages/OrgKnowledgeBase";
import AgentActivityCenter from "./pages/AgentActivityCenter";
import Settings from "./pages/Settings";

export default function App() {
  const [loggedIn, setLoggedIn] = useState(!!getToken());

  if (!loggedIn) {
    return <LoginPage onLogin={() => setLoggedIn(true)} />;
  }

  return (
    <HashRouter>
      <div className="flex h-screen bg-ew-gray text-[13px] text-gray-800">
        {/* Sidebar */}
        <nav className="w-56 bg-white border-r border-ew-gray-border flex flex-col p-3 gap-1 shrink-0">
          <div className="font-bold text-[15px] text-ew-blue px-2 py-2 mb-2 border-b border-ew-gray-border">
            EasyWiki
          </div>
          <NavItem href="/" label="我的项目" />
          <NavItem href="/org-kb" label="组织知识库" />
          <NavItem href="/agent-center" label="Agent活动中心" />
          <div className="mt-auto pt-2 border-t border-ew-gray-border">
            <NavItem href="/settings" label="设置" />
          </div>
        </nav>

        {/* Main */}
        <main className="flex-1 overflow-auto p-4">
          <Routes>
            <Route path="/" element={<ProjectList />} />
            <Route path="/project/:projectId/*" element={<ProjectWorkspace />} />
            <Route path="/org-kb" element={<OrgKnowledgeBase />} />
            <Route path="/agent-center" element={<AgentActivityCenter />} />
            <Route path="/settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </main>
      </div>
    </HashRouter>
  );
}

function NavItem({ href, label }: { href: string; label: string }) {
  const hash = window.location.hash;
  const isActive = hash === `#${href}` || (href !== "/" && hash.startsWith(`#${href}`));
  return (
    <a
      href={`#${href}`}
      className={`px-2 py-1.5 rounded text-[13px] no-underline ${
        isActive ? "bg-ew-blue-light text-ew-blue font-medium" : "text-ew-gray-text hover:bg-gray-100"
      }`}
    >
      {label}
    </a>
  );
}
