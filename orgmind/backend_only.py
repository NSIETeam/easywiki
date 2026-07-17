"""
OrgMind Backend — FastAPI server only (for Electron wrapper)
No GUI, no pywebview. Just the API server.
"""
import sys
import os
import time
import ctypes
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

LOG_DIR = os.path.join(os.environ.get("APPDATA", os.path.expanduser("~")), "OrgMind")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "backend.log")

def log(msg):
    try:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    except:
        pass

log("=== BACKEND START ===")

# === Single Instance ===
def check_single_instance():
    mutex_name = "OrgMind_Backend_Mutex_v2.1"
    handle = ctypes.windll.kernel32.CreateMutexW(None, False, mutex_name)
    log(f"mutex: last_error={ctypes.windll.kernel32.GetLastError()}")
    if ctypes.windll.kernel32.GetLastError() == 183:
        log("already running, exiting")
        os._exit(0)

check_single_instance()

os.environ["ORGMIND_DB_PATH"] = os.path.join(LOG_DIR, "orgmind.db")
os.environ["ORGMIND_CONFIG_DIR"] = os.path.join(LOG_DIR, "config")
log(f"DB_PATH={os.environ['ORGMIND_DB_PATH']}")

if __name__ == "__main__":
    try:
        log("importing uvicorn...")
        import uvicorn
        log("importing orgmind.main_sqlite...")
        from orgmind.main_sqlite import app
        log("app imported OK, starting server")
        uvicorn.run(app, host="127.0.0.1", port=8080, log_level="warning")
    except Exception as e:
        import traceback
        log(f"FATAL: {e}\n{traceback.format_exc()}")
        ctypes.windll.user32.MessageBoxW(0, f"OrgMind Backend Error:\n\n{e}", "OrgMind", 0x10)
        os._exit(1)
