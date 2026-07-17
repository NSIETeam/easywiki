"""
OrgMind 原生桌面应用 — PyWebView + FastAPI
- 使用 Windows Edge WebView2 原生渲染
- 后端 FastAPI 在同一进程内运行
- 无浏览器窗口、无地址栏、无 Electron
"""
import sys
import os
import threading
import time
from pathlib import Path

# 设置路径
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

import webview
import uvicorn


def start_server():
    """在后台线程启动 FastAPI"""
    from orgmind.main_sqlite import app
    os.environ["ORGMIND_DB_PATH"] = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), "OrgMind", "orgmind.db"
    )
    os.environ["ORGMIND_CONFIG_DIR"] = os.path.join(
        os.environ.get("APPDATA", os.path.expanduser("~")), "OrgMind", "config"
    )
    uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")


def main():
    # 启动后端线程
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 等待服务器就绪
    import requests
    for _ in range(30):
        try:
            requests.get("http://127.0.0.1:8080/health", timeout=1)
            break
        except Exception:
            time.sleep(0.5)

    # 创建原生窗口
    window = webview.create_window(
        title="OrgMind v2.1 — 组织知识库",
        url="http://127.0.0.1:8080",
        width=1280,
        height=800,
        min_size=(900, 600),
        confirm_close=True,
        text_select=True,
    )

    webview.start(debug=False)
    sys.exit(0)


if __name__ == "__main__":
    main()
