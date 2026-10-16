import os
import time
import psutil
import sqlite3
import urllib.request
from datetime import datetime

START_TIME = time.time()
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
DB_PATH = os.path.join(ROOT_DIR, "Data", "JarvisMemory.db")

def check_database() -> dict:
    t0 = time.perf_counter()
    if not os.path.exists(DB_PATH):
        return {"status": "STANDBY", "latency_ms": 0.0, "journal_mode": "unknown"}
    try:
        conn = sqlite3.connect(DB_PATH, timeout=1.0)
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode;")
        mode = cursor.fetchone()[0]
        cursor.execute("SELECT 1;")
        conn.close()
        latency = round((time.perf_counter() - t0) * 1000, 2)
        return {"status": "HEALTHY", "latency_ms": latency, "journal_mode": mode}
    except Exception as e:
        return {"status": "ERROR", "error": str(e)}

def check_godseye_service() -> dict:
    t0 = time.perf_counter()
    try:
        req = urllib.request.Request("http://127.0.0.1:5173/", headers={"User-Agent": "JARVIS-Healthcheck"})
        with urllib.request.urlopen(req, timeout=1.0) as resp:
            latency = round((time.perf_counter() - t0) * 1000, 2)
            return {"status": "ONLINE" if resp.status == 200 else "DEGRADED", "port": 5173, "latency_ms": latency}
    except Exception:
        return {"status": "OFFLINE", "port": 5173}

def check_hardware() -> dict:
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    disk = psutil.disk_usage(ROOT_DIR).percent
    status = "HEALTHY"
    if cpu > 90 or ram > 90 or disk > 95:
        status = "CRITICAL"
    elif cpu > 75 or ram > 80 or disk > 85:
        status = "DEGRADED"
    return {"status": status, "cpu_pct": cpu, "ram_pct": ram, "disk_pct": disk}

def get_system_health(ws_client_count: int = 0) -> dict:
    uptime = round((time.time() - START_TIME) / 3600, 2)
    db_info = check_database()
    gods_eye = check_godseye_service()
    hw_info = check_hardware()

    # Tri-State System Status: NOMINAL / DEGRADED / CRITICAL
    overall_status = "NOMINAL"
    if hw_info["status"] == "CRITICAL" or db_info.get("status") == "ERROR":
        overall_status = "CRITICAL"
    elif hw_info["status"] == "DEGRADED" or gods_eye.get("status") == "OFFLINE":
        overall_status = "DEGRADED"

    return {
        "status": overall_status,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "uptime_hours": uptime,
        "checks": {
            "database": db_info,
            "websockets": {"status": "HEALTHY", "active_clients": ws_client_count},
            "gods_eye_view": gods_eye,
            "hardware": hw_info,
            "circuit_breakers": {
                "binance_crypto": "CLOSED",
                "weather_wttr": "CLOSED",
                "iss_tracker": "CLOSED"
            }
        }
    }
