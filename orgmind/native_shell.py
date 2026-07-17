"""
OrgMind Native Desktop Shell — tkinter GUI, zero web dependency
"""
import sys
import os
import json
import threading
import time
import ctypes
import urllib.request
import urllib.error
import tkinter as tk
from tkinter import ttk, messagebox, font
from pathlib import Path

# === Bootstrap ===
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

LOG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "OrgMind")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "native_shell.log")

def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except:
        pass

# === Single Instance ===
def check_single_instance():
    mutex_name = "OrgMind_SingleInstance_Mutex_v3.0"
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    if ctypes.windll.kernel32.GetLastError() == 183:
        ctypes.windll.user32.MessageBoxW(0, "OrgMind 已经在运行中。", "OrgMind", 0x40)
        sys.exit(0)

check_single_instance()
log("=== NATIVE SHELL START ===")

# === Server Thread ===
PORT = 8080
BASE_URL = f"http://127.0.0.1:{PORT}"

def run_server():
    try:
        os.environ["ORGMIND_DB_PATH"] = os.path.join(LOG_DIR, "orgmind.db")
        os.environ["ORGMIND_CONFIG_DIR"] = os.path.join(LOG_DIR, "config")
        from orgmind.main_sqlite import app
        import uvicorn
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
    except Exception as e:
        log(f"Server crash: {e}")
        import traceback
        log(traceback.format_exc())

threading.Thread(target=run_server, daemon=True).start()
log("server thread launched")

# === API Helper ===
TOKEN = None

def api(endpoint, method="GET", data=None, auth=True):
    url = f"{BASE_URL}{endpoint}"
    body = json.dumps(data).encode() if data else None
    headers = {"Content-Type": "application/json"}
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method=method)
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        err = json.loads(e.read().decode()) if e.fp else {"detail": str(e)}
        raise Exception(err.get("detail", str(e)))
    except Exception as e:
        raise Exception(f"Network error: {e}")

# === Colors & Style ===
BG = "#f5f5f5"
FG = "#171717"
ACCENT = "#2563eb"
ACCENT_HOVER = "#1d4ed8"
BORDER = "#d4d4d4"
WHITE = "#ffffff"
MUTED = "#a3a3a3"
DANGER = "#ef4444"

# === Main Application ===
class OrgMindNative:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("OrgMind v3.0")
        self.root.geometry("1100x700")
        self.root.minsize(900, 600)
        self.root.configure(bg=BG)

        # Icon
        try:
            icon_path = ROOT / "orgmind" / "assets" / "icon.ico"
            if icon_path.exists():
                self.root.iconbitmap(str(icon_path))
        except:
            pass

        # Fonts
        self.title_font = font.Font(family="Microsoft YaHei UI", size=14, weight="bold")
        self.body_font = font.Font(family="Microsoft YaHei UI", size=10)
        self.small_font = font.Font(family="Microsoft YaHei UI", size=9)

        # State
        self.token = None
        self.user = None
        self.current_page = None

        # Start with login
        self.show_login()

    def clear(self):
        for w in self.root.winfo_children():
            w.destroy()

    # ========= LOGIN PAGE =========
    def show_login(self):
        self.clear()

        frame = tk.Frame(self.root, bg=BG)
        frame.place(relx=0.5, rely=0.5, anchor="center")

        tk.Label(frame, text="OrgMind", font=font.Font(family="Microsoft YaHei UI", size=24, weight="bold"), fg=ACCENT, bg=BG).pack(pady=(0,5))
        tk.Label(frame, text="组织知识管理平台", font=self.small_font, fg=MUTED, bg=BG).pack(pady=(0,20))

        # Error label
        error_var = tk.StringVar()
        error_label = tk.Label(frame, textvariable=error_var, fg=DANGER, bg=BG, font=self.small_font)
        error_label.pack(pady=(0,10))

        tk.Label(frame, text="邮箱", font=self.body_font, fg=FG, bg=BG, anchor="w").pack(fill="x")
        email_entry = tk.Entry(frame, font=self.body_font, relief="solid", bd=1)
        email_entry.insert(0, "admin@local")
        email_entry.pack(fill="x", ipady=4, pady=(2,10))

        tk.Label(frame, text="密码", font=self.body_font, fg=FG, bg=BG, anchor="w").pack(fill="x")
        pw_entry = tk.Entry(frame, font=self.body_font, relief="solid", bd=1, show="•")
        pw_entry.insert(0, "orgmind2026")
        pw_entry.pack(fill="x", ipady=4, pady=(2,10))
        pw_entry.bind("<Return>", lambda e: do_login())

        def do_login():
            email = email_entry.get().strip()
            pw = pw_entry.get().strip()
            if not email or not pw:
                error_var.set("请输入邮箱和密码")
                return
            error_var.set("登录中...")
            self.root.update()
            try:
                global TOKEN
                result = api("/api/v1/auth/login", "POST", {"email": email, "password": pw}, auth=False)
                TOKEN = result["token"]
                self.user = result["user"]
                log(f"Login OK: {self.user['email']}")
                self.show_main()
            except Exception as e:
                error_var.set(f"登录失败: {e}")
                log(f"Login failed: {e}")

        login_btn = tk.Button(frame, text="登  录", font=self.body_font, bg=ACCENT, fg=WHITE, relief="flat",
                             activebackground=ACCENT_HOVER, activeforeground=WHITE, command=do_login, cursor="hand2")
        login_btn.pack(fill="x", ipady=6, pady=(5,0))

        email_entry.focus_set()

    # ========= MAIN LAYOUT =========
    def show_main(self):
        self.clear()

        # Sidebar
        sidebar = tk.Frame(self.root, bg="#f0f0f0", width=180)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        tk.Label(sidebar, text="OrgMind", font=font.Font(family="Microsoft YaHei UI", size=13, weight="bold"),
                fg=ACCENT, bg="#f0f0f0").pack(pady=(15,20))

        nav_items = [
            ("总  览", self.show_dashboard),
            ("记  忆", self.show_memories),
            ("文  档", self.show_documents),
            ("技  能", self.show_skills),
            ("管  理", self.show_admin),
        ]

        self.nav_buttons = []
        for text, cmd in nav_items:
            btn = tk.Button(sidebar, text=text, font=self.body_font, fg=FG, bg="#f0f0f0",
                          relief="flat", anchor="w", padx=20, cursor="hand2",
                          activebackground="#e0e0e0", activeforeground=ACCENT,
                          command=lambda c=cmd, b=None: self.nav_click(c, b))
            btn.pack(fill="x", ipady=8)
            self.nav_buttons.append((btn, text, cmd))

        tk.Frame(sidebar, bg=BORDER, height=1).pack(fill="x", padx=15, pady=10)

        tk.Label(sidebar, text=f"👤 {self.user.get('name','User')}", font=self.small_font, fg=FG, bg="#f0f0f0").pack()
        tk.Label(sidebar, text=self.user.get('email',''), font=("Microsoft YaHei UI", 8), fg=MUTED, bg="#f0f0f0").pack()

        tk.Button(sidebar, text="退出登录", font=self.small_font, fg=ACCENT, bg="#f0f0f0",
                 relief="flat", cursor="hand2", command=self.do_logout).pack(pady=(10,0))

        # Content area
        self.content = tk.Frame(self.root, bg=BG)
        self.content.pack(side="right", expand=True, fill="both")

        self.show_dashboard()

    def nav_click(self, callback, btn_widget=None):
        for b, t, c in self.nav_buttons:
            b.configure(fg=FG, bg="#f0f0f0")
        callback()

    def do_logout(self):
        global TOKEN
        TOKEN = None
        self.user = None
        self.show_login()

    def clear_content(self):
        for w in self.content.winfo_children():
            w.destroy()

    # ========= DASHBOARD =========
    def show_dashboard(self):
        self.clear_content()
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(f, text="总览", font=self.title_font, fg=FG, bg=BG).pack(anchor="w")
        tk.Label(f, text=f"欢迎回来, {self.user.get('name','User')}", font=self.small_font, fg=MUTED, bg=BG).pack(anchor="w", pady=(2,15))

        # Stats cards
        stats_frame = tk.Frame(f, bg=BG)
        stats_frame.pack(fill="x")

        labels = [("记忆总数", "memories"), ("文档总数", "docs"), ("技能数", "skills"), ("在线", "1")]
        self.stats_vars = {}
        for i, (label, key) in enumerate(labels):
            card = tk.Frame(stats_frame, bg=WHITE, relief="solid", bd=1)
            card.grid(row=0, column=i, padx=(0,10 if i<3 else 0), sticky="ew")
            stats_frame.columnconfigure(i, weight=1)
            var = tk.StringVar(value="加载中...")
            self.stats_vars[key] = var
            tk.Label(card, textvariable=var, font=font.Font(family="Microsoft YaHei UI", size=22, weight="bold"),
                    fg=FG, bg=WHITE).pack(pady=(15,2))
            tk.Label(card, text=label, font=self.small_font, fg=MUTED, bg=WHITE).pack(pady=(0,15))

        # Quick note
        note_frame = tk.LabelFrame(f, text="快速记录", font=self.body_font, fg=FG, bg=BG, padx=10, pady=10)
        note_frame.pack(fill="x", pady=15)

        note_text = tk.Text(note_frame, font=self.body_font, height=3, relief="solid", bd=1, wrap="word")
        note_text.pack(fill="x")
        note_status = tk.StringVar()
        tk.Label(note_frame, textvariable=note_status, font=self.small_font, fg=MUTED, bg=BG).pack(anchor="w")

        def save_note():
            content = note_text.get("1.0", "end-1c").strip()
            if not content:
                return
            note_status.set("保存中...")
            self.root.update()
            try:
                api("/api/v1/memory/create", "POST", {"content": content, "type": "episodic", "scope": "org"})
                note_text.delete("1.0", "end")
                note_status.set("已保存 ✓")
                self.load_stats()
            except Exception as e:
                note_status.set(f"❌ {e}")

        tk.Button(note_frame, text="保存记录", font=self.small_font, bg=ACCENT, fg=WHITE, relief="flat",
                 cursor="hand2", command=save_note).pack(pady=(8,0))

        # Recent memories
        mem_frame = tk.LabelFrame(f, text="最近记忆", font=self.body_font, fg=FG, bg=BG, padx=10, pady=10)
        mem_frame.pack(fill="both", expand=True)

        self.mem_list = tk.Text(mem_frame, font=self.body_font, height=10, relief="flat", bg=BG, wrap="word", state="disabled")
        self.mem_list.pack(fill="both", expand=True)

        self.load_stats()
        self.load_recent()

    def load_stats(self):
        try:
            data = api("/api/v1/memory/list?limit=1")
            self.stats_vars["memories"].set(str(data.get("total", "?")))
        except:
            self.stats_vars["memories"].set("?")
        self.stats_vars["docs"].set("?")
        self.stats_vars["skills"].set("?")

    def load_recent(self):
        try:
            data = api("/api/v1/memory/list?limit=8")
            memories = data.get("memories", [])
            self.mem_list.configure(state="normal")
            self.mem_list.delete("1.0", "end")
            for m in memories:
                snippet = (m.get("content_snippet") or "")[:150]
                score = m.get("score", 0)
                stype = m.get("source_type", "")
                self.mem_list.insert("end", f"• {snippet}\n")
                self.mem_list.insert("end", f"  {(score*100):.0f}% / {stype}\n\n")
            self.mem_list.configure(state="disabled")
        except Exception as e:
            self.mem_list.configure(state="normal")
            self.mem_list.delete("1.0", "end")
            self.mem_list.insert("end", f"加载失败: {e}")
            self.mem_list.configure(state="disabled")

    # ========= MEMORIES =========
    def show_memories(self):
        self.clear_content()
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(f, text="记忆管理", font=self.title_font, fg=FG, bg=BG).pack(anchor="w", pady=(0,15))

        # Search bar
        search_frame = tk.Frame(f, bg=BG)
        search_frame.pack(fill="x")
        search_var = tk.StringVar()
        search_entry = tk.Entry(search_frame, textvariable=search_var, font=self.body_font, relief="solid", bd=1)
        search_entry.pack(side="left", fill="x", expand=True, ipady=4)
        search_entry.bind("<Return>", lambda e: do_search())

        tk.Button(search_frame, text="搜索", font=self.small_font, bg=ACCENT, fg=WHITE, relief="flat",
                 cursor="hand2", command=do_search).pack(side="left", padx=(5,0), ipady=4)

        # Results list
        result_frame = tk.Frame(f, bg=BG)
        result_frame.pack(fill="both", expand=True, pady=10)

        canvas = tk.Canvas(result_frame, bg=BG, highlightthickness=0)
        scrollbar = ttk.Scrollbar(result_frame, orient="vertical", command=canvas.yview)
        scrollable = tk.Frame(canvas, bg=BG)
        scrollable.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0,0), window=scrollable, anchor="nw", tags="scrollable")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        def _on_mousewheel(event):
            canvas.yview_scroll(-1 * (event.delta // 120), "units")
        canvas.bind_all("<MouseWheel>", _on_mousewheel)

        def do_search(query=None):
            for w in scrollable.winfo_children():
                w.destroy()
            q = query or search_var.get().strip()
            tk.Label(scrollable, text=f"{'搜索中...' if q else '加载中...'}", font=self.small_font, fg=MUTED, bg=BG).pack(pady=10)
            self.root.update()
            try:
                if q:
                    data = api(f"/api/v1/memory/search?q={urllib.parse.quote(q)}&limit=20")
                    results = data.get("results", [])
                else:
                    data = api("/api/v1/memory/list?limit=20")
                    results = data.get("memories", [])
                for w in scrollable.winfo_children():
                    w.destroy()
                if not results:
                    tk.Label(scrollable, text="没有找到记忆", font=self.small_font, fg=MUTED, bg=BG).pack(pady=10)
                for m in results:
                    card = tk.Frame(scrollable, bg=WHITE, relief="solid", bd=1)
                    card.pack(fill="x", pady=3)
                    snippet = (m.get("content_snippet") or "")[:200]
                    score = m.get("score", 0)
                    stype = m.get("source_type", "")
                    tk.Label(card, text=snippet, font=self.body_font, fg=FG, bg=WHITE, anchor="w", justify="left",
                            wraplength=700).pack(padx=12, pady=(10,2), anchor="w")
                    tk.Label(card, text=f"{(score*100):.0f}% / {stype}", font=self.small_font, fg=MUTED, bg=WHITE).pack(padx=12, pady=(0,10), anchor="w")
            except Exception as e:
                for w in scrollable.winfo_children():
                    w.destroy()
                tk.Label(scrollable, text=f"❌ {e}", font=self.small_font, fg=DANGER, bg=BG).pack(pady=10)

        do_search()
        search_entry.focus_set()

    # ========= DOCUMENTS =========
    def show_documents(self):
        self.clear_content()
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(f, text="文档管理", font=self.title_font, fg=FG, bg=BG).pack(anchor="w", pady=(0,15))

        result_text = tk.Text(f, font=self.body_font, relief="flat", bg=BG, wrap="word", state="disabled", height=15)
        result_text.pack(fill="both", expand=True)

        try:
            data = api("/api/v1/memory/search?q=document&limit=20")
            results = data.get("results", [])
            if not results:
                result_text.configure(state="normal")
                result_text.insert("end", "\n尚无文档。上传功能开发中。\n")
                result_text.configure(state="disabled")
            else:
                result_text.configure(state="normal")
                for d in results:
                    snippet = (d.get("content_snippet") or "")[:150]
                    stype = d.get("source_type", "")
                    result_text.insert("end", f"📄 {snippet}\n   {stype}\n\n")
                result_text.configure(state="disabled")
        except Exception as e:
            result_text.configure(state="normal")
            result_text.insert("end", f"加载失败: {e}")
            result_text.configure(state="disabled")

    # ========= SKILLS =========
    def show_skills(self):
        self.clear_content()
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(f, text="技能管理", font=self.title_font, fg=FG, bg=BG).pack(anchor="w", pady=(0,15))

        result_text = tk.Text(f, font=self.body_font, relief="flat", bg=BG, wrap="word", state="disabled", height=15)
        result_text.pack(fill="both", expand=True)

        try:
            data = api("/api/v1/skill/list?limit=20")
            skills = data.get("matched", data.get("skills", []))
            result_text.configure(state="normal")
            if not skills:
                result_text.insert("end", "\n尚无技能注册。\n")
            for s in skills:
                name = s.get("name", "未知")
                desc = s.get("description", "")
                otype = s.get("object_type", "skill")
                result_text.insert("end", f"🔧 {name} ({otype})\n   {desc}\n\n")
            result_text.configure(state="disabled")
        except Exception as e:
            result_text.configure(state="normal")
            result_text.insert("end", f"加载失败: {e}")
            result_text.configure(state="disabled")

    # ========= ADMIN =========
    def show_admin(self):
        self.clear_content()
        f = tk.Frame(self.content, bg=BG)
        f.pack(fill="both", expand=True, padx=25, pady=20)

        tk.Label(f, text="管理面板", font=self.title_font, fg=FG, bg=BG).pack(anchor="w", pady=(0,15))

        tk.Label(f, text=f"当前用户: {self.user.get('name','')} ({self.user.get('email','')})",
                font=self.body_font, fg=FG, bg=BG).pack(anchor="w", pady=(0,5))
        tk.Label(f, text=f"角色: {self.user.get('role','')}", font=self.small_font, fg=MUTED, bg=BG).pack(anchor="w")

        tk.Frame(f, bg=BORDER, height=1).pack(fill="x", pady=15)

        tk.Label(f, text="数据库位置:", font=self.small_font, fg=MUTED, bg=BG).pack(anchor="w")
        tk.Label(f, text=os.path.join(LOG_DIR, "orgmind.db"), font=self.body_font, fg=FG, bg=BG).pack(anchor="w", pady=(0,10))

        tk.Label(f, text="日志位置:", font=self.small_font, fg=MUTED, bg=BG).pack(anchor="w")
        tk.Label(f, text=LOG_PATH, font=self.body_font, fg=FG, bg=BG).pack(anchor="w", pady=(0,10))

        # Health check
        h_status = tk.StringVar(value="检查中...")
        tk.Label(f, textvariable=h_status, font=self.small_font, fg=ACCENT, bg=BG).pack(anchor="w", pady=(10,0))
        try:
            data = api("/health", auth=False)
            h_status.set(f"✅ 服务器健康 | Backend: {data.get('backend','?')} | v{data.get('version','?')}")
        except:
            h_status.set("❌ 服务器不可用")

    def run(self):
        self.root.mainloop()

# === Start ===
def main():
    # Wait for server
    log("waiting for server...")
    for i in range(120):
        try:
            urllib.request.urlopen(f"{BASE_URL}/health", timeout=1)
            log(f"server ready after {(i+1)*0.5:.1f}s")
            break
        except:
            time.sleep(0.5)
    else:
        log("TIMEOUT: server never started")
        ctypes.windll.user32.MessageBoxW(0, "OrgMind 服务启动超时，请重试。", "OrgMind", 0x10)
        os._exit(1)

    log("starting native GUI")
    app = OrgMindNative()
    app.run()
    log("GUI closed, exiting")
    os._exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log(f"MAIN CRASHED: {e}\n{traceback.format_exc()}")
        ctypes.windll.user32.MessageBoxW(0, f"OrgMind 发生错误: {e}", "OrgMind", 0x10)
        os._exit(1)
