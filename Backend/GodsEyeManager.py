import os
import sys
import time
import urllib.request
import subprocess
import webbrowser
from threading import Thread

GODS_EYE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "Tools", "GodsEyeView"))
GODS_EYE_PORT = 5173
GODS_EYE_URL = f"http://127.0.0.1:{GODS_EYE_PORT}/"
_process = None

def is_godseye_running() -> bool:
    try:
        req = urllib.request.Request(GODS_EYE_URL, headers={"User-Agent": "JARVIS-Healthcheck"})
        with urllib.request.urlopen(req, timeout=1.5) as resp:
            return resp.status == 200
    except Exception:
        return False

def ensure_godseye_running(timeout: int = 15) -> bool:
    global _process
    if is_godseye_running():
        return True

    if not os.path.exists(GODS_EYE_DIR):
        print(f"!! [GODS EYE ERROR]: Directory not found at {GODS_EYE_DIR}")
        return False

    npm_cmd = "npm.cmd" if sys.platform == "win32" else "npm"
    try:
        print(">> [GOD'S EYE VIEW]: Igniting geospatial spy satellite simulator on port 5173...")
        creationflags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        _process = subprocess.Popen(
            [npm_cmd, "run", "dev"],
            cwd=GODS_EYE_DIR,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            creationflags=creationflags
        )

        start = time.time()
        while time.time() - start < timeout:
            if is_godseye_running():
                print(">> [GOD'S EYE VIEW]: Intelligence console ONLINE at http://127.0.0.1:5173/")
                return True
            time.sleep(0.5)

        return is_godseye_running()
    except Exception as e:
        print(f"!! [GODS EYE START ERROR]: {e}")
        return False

def launch_godseye_overview() -> str:
    """Ensures server is running and opens the tactical spy satellite globe."""
    running = ensure_godseye_running()
    try:
        webbrowser.open(GODS_EYE_URL)
        from Backend.EventBus import EventBus
        EventBus.emit("godseye_launched", {"url": GODS_EYE_URL, "status": "ONLINE"})
    except Exception:
        pass

    if running:
        return "Tactical Overview (God's Eye View) spy satellite console is active and displayed on your screen, sir."
    return "Tactical Overview service was initiated and will be available shortly on port 5173, sir."

def get_godseye_status() -> dict:
    running = is_godseye_running()
    return {
        "status": "ONLINE" if running else "OFFLINE",
        "url": GODS_EYE_URL,
        "embed_url": f"{GODS_EYE_URL}?embed=1",
        "port": GODS_EYE_PORT,
        "features": [
            "Real-time 3D Photorealistic CesiumJS Globe",
            "Live ADS-B Aircraft Tracking (OpenSky)",
            "Live AIS Maritime Vessel Tracking",
            "Orbital Satellite Catalog & ISS Trajectory",
            "USGS Real-Time Earthquake Monitoring",
            "NASA Active Wildfire Thermal Detection",
            "Public CCTV Surveillance Feeds",
            "FLIR / Cyber Sonar Thermal Reconnaissance"
        ]
    }
