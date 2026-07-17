"""
OrgMind 桌面壳 — 极简版, 确保窗口一定出现
"""
import sys
import os
import threading
import time
import ctypes
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

LOG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "OrgMind")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "shell_debug.log")


def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except Exception:
        pass


log("=== START ===")

# === 单实例锁 ===
def check_single_instance():
    mutex_name = "OrgMind_SingleInstance_Mutex_v2.1"
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    last_error = ctypes.windll.kernel32.GetLastError()
    log(f"single_instance check: last_error={last_error}")
    if last_error == 183:
        ctypes.windll.user32.MessageBoxW(
            0, "OrgMind 已经在运行中。\n\n请检查系统托盘或任务栏。", "OrgMind", 0x40
        )
        sys.exit(0)

check_single_instance()
log("single instance OK")

# === 全局异常兜底 ===
def global_excepthook(exc_type, exc_value, exc_tb):
    import traceback
    tb = ''.join(traceback.format_exception(exc_type, exc_value, exc_tb))
    log(f"UNCAUGHT MAIN EXCEPTION: {exc_value}\n{tb}")
    ctypes.windll.user32.MessageBoxW(0, f"OrgMind 遇到错误:\n\n{exc_value}\n\n{tb[-500:]}", "OrgMind", 0x10)
    sys.exit(1)

sys.excepthook = global_excepthook

def thread_excepthook(args):
    import traceback
    tb = ''.join(traceback.format_exception(args.exc_type, args.exc_value, args.exc_traceback))
    log(f"UNCAUGHT THREAD EXCEPTION: {args.exc_value}\n{tb}")
    ctypes.windll.user32.MessageBoxW(0, f"OrgMind 后台线程错误:\n\n{args.exc_value}\n\n{tb[-800:]}", "OrgMind", 0x10)
    os._exit(1)

threading.excepthook = thread_excepthook
log("exception hooks installed")

try:
    import webview
    log("webview imported")
    import uvicorn
    log("uvicorn imported")
except Exception as e:
    log(f"IMPORT ERROR: {e}")
    raise

PORT = 8080

def run_server():
    log("run_server thread started")
    try:
        os.environ["ORGMIND_DB_PATH"] = os.path.join(LOG_DIR, "orgmind.db")
        os.environ["ORGMIND_CONFIG_DIR"] = os.path.join(LOG_DIR, "config")
        log(f"env set, DB_PATH={os.environ['ORGMIND_DB_PATH']}")
        from orgmind.main_sqlite import app
        log("orgmind.main_sqlite imported OK")
        uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
        log("uvicorn.run returned (should not happen normally)")
    except Exception as e:
        import traceback
        log(f"run_server EXCEPTION: {e}\n{traceback.format_exc()}")
        raise

def main():
    log("main() started")
    threading.Thread(target=run_server, daemon=True).start()
    log("server thread launched, waiting for health check")

    # Wait for server
    import urllib.request
    ok = False
    for i in range(60):
        try:
            urllib.request.urlopen(f"http://127.0.0.1:{PORT}/health", timeout=1)
            ok = True
            log(f"health check OK after {i} tries")
            break
        except Exception as e:
            if i == 0:
                log(f"health check attempt failed: {e}")
            time.sleep(0.5)

    if not ok:
        log("health check TIMED OUT after 30s, creating window anyway")

    log("creating window")
    # Create window - minimal, just works
    webview.create_window(
        title="OrgMind v2.1",
        url=f"http://127.0.0.1:{PORT}",
        width=1280,
        height=800,
        min_size=(900, 600),
    )
    log("window created, starting webview.start()")
    webview.start()
    log("webview.start() returned, exiting")
    os._exit(0)

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        import traceback
        log(f"MAIN CRASHED: {e}\n{traceback.format_exc()}")
        raise
