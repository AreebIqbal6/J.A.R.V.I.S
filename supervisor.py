import os
import sys
import time
import urllib.request
import subprocess

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
LOGS_DIR = os.path.join(ROOT_DIR, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

PYTHON_EXE = os.path.join(ROOT_DIR, ".venv", "Scripts", "python.exe") if sys.platform == "win32" else "python3"
NPM_CMD = "npm.cmd" if sys.platform == "win32" else "npm"

def log_supervisor(msg: str):
    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
    formatted = f"[{timestamp}] [SUPERVISOR] {msg}"
    print(formatted)
    try:
        with open(os.path.join(LOGS_DIR, "supervisor.log"), "a", encoding="utf-8") as f:
            f.write(formatted + "\n")
    except Exception:
        pass

def is_alive(url: str) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Supervisor-Watchdog"})
        with urllib.request.urlopen(req, timeout=3.5) as resp:
            return resp.status == 200
    except Exception:
        return False

def kill_proc(proc):
    if proc is None:
        return
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/T", "/PID", str(proc.pid)], capture_output=True)
        else:
            proc.terminate()
            proc.wait(timeout=2)
    except Exception:
        try: proc.kill()
        except Exception: pass

def run_supervisor():
    log_supervisor("Starting Industrial Process Supervisor for J.A.R.V.I.S...")
    
    backend_proc = None
    godseye_proc = None
    backend_strikes = 0
    godseye_strikes = 0

    while True:
        try:
            # 1. Inspect Core Backend (Port 8000)
            if not is_alive("http://127.0.0.1:8000/api/health"):
                backend_strikes += 1
                if backend_proc is None or backend_proc.poll() is not None:
                    log_supervisor("Starting Core Backend service (Port 8000)...")
                    backend_proc = subprocess.Popen(
                        [PYTHON_EXE, "-m", "uvicorn", "Backend.Server:app", "--host", "127.0.0.1", "--port", "8000"],
                        cwd=ROOT_DIR
                    )
                    backend_strikes = 0
                elif backend_strikes >= 5:
                    log_supervisor("WARNING: Core Backend unresponsive for 25s. Restarting service...")
                    kill_proc(backend_proc)
                    time.sleep(1)
                    backend_proc = subprocess.Popen(
                        [PYTHON_EXE, "-m", "uvicorn", "Backend.Server:app", "--host", "127.0.0.1", "--port", "8000"],
                        cwd=ROOT_DIR
                    )
                    backend_strikes = 0
            else:
                backend_strikes = 0

            # 2. Inspect God's Eye View (Port 5173)
            gods_dir = os.path.join(ROOT_DIR, "Tools", "GodsEyeView")
            if os.path.exists(gods_dir):
                if not is_alive("http://127.0.0.1:5173/"):
                    godseye_strikes += 1
                    gev_env = {**os.environ, "GEV_EMBED_FRAME_ANCESTORS": "*"}
                    if godseye_proc is None or godseye_proc.poll() is not None:
                        log_supervisor("Starting God's Eye View Vite service (Port 5173)...")
                        godseye_proc = subprocess.Popen(
                            [NPM_CMD, "run", "dev"],
                            cwd=gods_dir,
                            env=gev_env,
                            shell=True
                        )
                        godseye_strikes = 0
                    elif godseye_strikes >= 4:
                        log_supervisor("WARNING: God's Eye View unresponsive for 20s. Restarting service...")
                        try:
                            godseye_proc.terminate()
                            godseye_proc.wait(timeout=2)
                        except Exception:
                            try: godseye_proc.kill()
                            except Exception: pass
                        godseye_proc = subprocess.Popen(
                            [NPM_CMD, "run", "dev"],
                            cwd=gods_dir,
                            env=gev_env,
                            shell=True
                        )
                        godseye_strikes = 0
                else:
                    godseye_strikes = 0

            time.sleep(5)
        except KeyboardInterrupt:
            log_supervisor("Shutdown signal received. Gracefully terminating child processes...")
            kill_proc(backend_proc)
            kill_proc(godseye_proc)
            break
        except Exception as e:
            log_supervisor(f"Error in watchdog loop: {e}")
            time.sleep(5)

if __name__ == "__main__":
    run_supervisor()
