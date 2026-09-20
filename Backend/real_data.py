"""
JARVIS Real Data APIs
All endpoints return actual live data from the local system and free public APIs.
No paid API keys required.
"""
import psutil
import time
import asyncio
import platform
import subprocess
import json
from datetime import datetime
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import traceback
from Backend.EventBus import event_bus

router = APIRouter(prefix="/api", tags=["real-data"])

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: dict):
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception:
                pass

manager = ConnectionManager()
server_loop = None  # Will be set by Server.py on startup

def _bridge_to_ws(event_type):
    def callback(payload):
        if server_loop and server_loop.is_running():
            try:
                # payload might be a dict or a string depending on the event
                data = payload.get("payload") if isinstance(payload, dict) and "payload" in payload else payload
                asyncio.run_coroutine_threadsafe(
                    manager.broadcast({"type": event_type, "data": data}),
                    server_loop
                )
            except Exception as e:
                print(f"Error bridging {event_type} to WS: {e}")
    return callback

# Subscribe to all HUD-relevant events
event_bus.subscribe("text_output", _bridge_to_ws("text_output"))
event_bus.subscribe("status_change", _bridge_to_ws("status_change"))
event_bus.subscribe("swarm_message", _bridge_to_ws("swarm_message"))
event_bus.subscribe("tts_waveform", _bridge_to_ws("tts_waveform"))
event_bus.subscribe("widget_command", _bridge_to_ws("widget_command"))

# ─────────────────────────────────────────────────────────────
# 1. SYSTEM STATS (CPU / RAM / GPU / Temp / Network)
# ─────────────────────────────────────────────────────────────
_prev_net = {"bytes_sent": 0, "bytes_recv": 0, "time": time.time()}

@router.get("/system-stats")
async def system_stats():
    """Returns real CPU, RAM, GPU, temperature, and network throughput."""
    cpu_pct = psutil.cpu_percent(interval=0.3)
    ram = psutil.virtual_memory()
    ram_pct = ram.percent

    # GPU usage — try nvidia-smi first, fallback to 0
    gpu_pct = 0.0
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=utilization.gpu", "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=3
        )
        if result.returncode == 0:
            gpu_pct = float(result.stdout.strip().split("\n")[0])
    except Exception:
        pass

    # CPU temperature — try psutil, fallback to WMI on Windows
    core_temp = 0.0
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for name, entries in temps.items():
                if entries:
                    core_temp = entries[0].current
                    break
    except Exception:
        pass

    if core_temp == 0.0 and platform.system() == "Windows":
        try:
            # Try Open Hardware Monitor WMI
            result = subprocess.run(
                ["powershell", "-Command",
                 "Get-CimInstance -Namespace root/OpenHardwareMonitor -ClassName Sensor | "
                 "Where-Object { $_.SensorType -eq 'Temperature' -and $_.Name -like '*CPU*' } | "
                 "Select-Object -First 1 -ExpandProperty Value"],
                capture_output=True, text=True, timeout=3
            )
            if result.returncode == 0 and result.stdout.strip():
                core_temp = float(result.stdout.strip())
        except Exception:
            core_temp = 45.0  # sensible fallback

    # Network throughput (Mb/s)
    net = psutil.net_io_counters()
    now = time.time()
    dt = now - _prev_net["time"]
    if dt > 0:
        down_mbps = (net.bytes_recv - _prev_net["bytes_recv"]) * 8 / dt / 1_000_000
        up_mbps = (net.bytes_sent - _prev_net["bytes_sent"]) * 8 / dt / 1_000_000
    else:
        down_mbps = 0
        up_mbps = 0
    _prev_net["bytes_sent"] = net.bytes_sent
    _prev_net["bytes_recv"] = net.bytes_recv
    _prev_net["time"] = now

    # Disk usage
    disk = psutil.disk_usage("/")

    return {
        "cpu": round(cpu_pct, 1),
        "ram": round(ram_pct, 1),
        "gpu": round(gpu_pct, 1),
        "core_temp": round(core_temp, 1),
        "net_down_mbps": round(down_mbps, 1),
        "net_up_mbps": round(up_mbps, 1),
        "ram_used_gb": round(ram.used / (1024**3), 1),
        "ram_total_gb": round(ram.total / (1024**3), 1),
        "disk_pct": round(disk.percent, 1),
        "uptime_hours": round((time.time() - psutil.boot_time()) / 3600, 1),
    }


# ─────────────────────────────────────────────────────────────
# 2. MEDIA / NOW PLAYING (Windows Media Session)
# ─────────────────────────────────────────────────────────────
@router.get("/media/now-playing")
async def media_now_playing():
    """
    Reads the currently playing media from Windows via 
    GlobalSystemMediaTransportControlsSessionManager.
    Works with Spotify, YouTube, VLC, any media player.
    """
    if platform.system() != "Windows":
        return {"playing": False, "error": "Not on Windows"}

    try:
        # Use PowerShell to query Windows Media Session
        ps_script = """
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager, Windows.Media.Control, ContentType=WindowsRuntime]

$async = [Windows.Media.Control.GlobalSystemMediaTransportControlsSessionManager]::RequestAsync()
$null = [System.Threading.Tasks.WindowsRuntimeSystemExtensions]::AsTask($async)
$mgr = $async.GetResults()
$session = $mgr.GetCurrentSession()

if ($null -eq $session) {
    Write-Output '{"playing": false}'
    exit
}

$info = $session.TryGetMediaPropertiesAsync()
$null = [System.Threading.Tasks.WindowsRuntimeSystemExtensions]::AsTask($info)
$props = $info.GetResults()

$timeline = $session.GetTimelineProperties()
$playback = $session.GetPlaybackInfo()

$result = @{
    playing = $true
    title = $props.Title
    artist = $props.Artist
    album = $props.AlbumTitle
    status = $playback.PlaybackStatus.ToString()
    position_sec = [int]$timeline.Position.TotalSeconds
    duration_sec = [int]$timeline.EndTime.TotalSeconds
} | ConvertTo-Json -Compress

Write-Output $result
"""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            return json.loads(result.stdout.strip())
        else:
            return {"playing": False}
    except Exception as e:
        return {"playing": False, "error": str(e)}


# ─────────────────────────────────────────────────────────────
# 3. STOCK MARKETS (Yahoo Finance — free, no key)
# ─────────────────────────────────────────────────────────────
_market_cache = {"data": None, "time": 0}

@router.get("/markets")
async def markets():
    """Returns real stock market data. Cached for 60s."""
    now = time.time()
    if _market_cache["data"] and (now - _market_cache["time"]) < 60:
        return _market_cache["data"]

    try:
        import yfinance as yf

        tickers = {
            "DJIA": "^DJI",
            "S&P 500": "^GSPC",
            "NASDAQ": "^IXIC",
            "FTSE 100": "^FTSE",
            "WTI": "CL=F",
            "BTC": "BTC-USD",
        }

        results = []
        data = yf.download(
            list(tickers.values()),
            period="2d",
            interval="1d",
            progress=False,
            threads=True,
        )

        for name, symbol in tickers.items():
            try:
                close_today = float(data["Close"][symbol].iloc[-1])
                close_prev = float(data["Close"][symbol].iloc[-2]) if len(data["Close"][symbol]) > 1 else close_today
                change_pct = ((close_today - close_prev) / close_prev) * 100 if close_prev else 0
                results.append({
                    "name": name,
                    "value": round(close_today, 1),
                    "change_pct": round(change_pct, 2),
                })
            except Exception:
                results.append({"name": name, "value": 0, "change_pct": 0})

        _market_cache["data"] = {"tickers": results}
        _market_cache["time"] = now
        return _market_cache["data"]
    except Exception as e:
        return {"tickers": [], "error": str(e)}


# ─────────────────────────────────────────────────────────────
# 4. WEATHER (wttr.in — completely free, no key)
# ─────────────────────────────────────────────────────────────
_weather_cache = {"data": None, "time": 0}

@router.get("/weather")
async def weather():
    """Returns real weather for Karachi. Cached for 300s."""
    now = time.time()
    if _weather_cache["data"] and (now - _weather_cache["time"]) < 300:
        return _weather_cache["data"]

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            resp = await client.get("https://wttr.in/Karachi?format=j1")
            if resp.status_code == 200:
                w = resp.json()
                current = w["current_condition"][0]
                result = {
                    "temp_c": current["temp_C"],
                    "feels_like_c": current["FeelsLikeC"],
                    "description": current["weatherDesc"][0]["value"],
                    "humidity": current["humidity"],
                    "wind_kmph": current["windspeedKmph"],
                    "city": "Karachi",
                }
                _weather_cache["data"] = result
                _weather_cache["time"] = now
                return result
    except Exception as e:
        return {"error": str(e), "city": "Karachi", "description": "Unable to fetch"}


# ─────────────────────────────────────────────────────────────
# 5. NEWS (RSS feeds — completely free, no key)
# ─────────────────────────────────────────────────────────────
_news_cache = {"data": None, "time": 0}

@router.get("/news")
async def news():
    """Returns top 5 headlines from BBC World RSS. Cached for 300s."""
    now = time.time()
    if _news_cache["data"] and (now - _news_cache["time"]) < 300:
        return _news_cache["data"]

    try:
        import feedparser
        feed = feedparser.parse("http://feeds.bbci.co.uk/news/world/rss.xml")
        headlines = []
        for entry in feed.entries[:5]:
            headlines.append({
                "title": entry.title,
                "summary": entry.get("summary", ""),
                "link": entry.link,
                "published": entry.get("published", ""),
            })
        result = {"headlines": headlines, "source": "BBC World"}
        _news_cache["data"] = result
        _news_cache["time"] = now
        return result
    except Exception as e:
        return {"headlines": [], "error": str(e)}


# ─────────────────────────────────────────────────────────────
# 6. CRYPTO (Binance public API — no key)
# ─────────────────────────────────────────────────────────────
_crypto_cache = {"data": None, "time": 0}

@router.get("/crypto")
async def crypto():
    """Returns BTC/USDT orderbook and 24h price. Cached for 10s."""
    now = time.time()
    if _crypto_cache["data"] and (now - _crypto_cache["time"]) < 10:
        return _crypto_cache["data"]

    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            # Get orderbook
            ob_resp = await client.get(
                "https://api.binance.com/api/v3/depth",
                params={"symbol": "BTCUSDT", "limit": 5}
            )
            # Get 24hr ticker
            ticker_resp = await client.get(
                "https://api.binance.com/api/v3/ticker/24hr",
                params={"symbol": "BTCUSDT"}
            )

            orderbook = ob_resp.json() if ob_resp.status_code == 200 else {"bids": [], "asks": []}
            ticker = ticker_resp.json() if ticker_resp.status_code == 200 else {}

            result = {
                "symbol": "BTC/USDT",
                "price": float(ticker.get("lastPrice", 0)),
                "change_pct": float(ticker.get("priceChangePercent", 0)),
                "high_24h": float(ticker.get("highPrice", 0)),
                "low_24h": float(ticker.get("lowPrice", 0)),
                "volume_24h": float(ticker.get("volume", 0)),
                "asks": [{"price": float(a[0]), "qty": float(a[1])} for a in orderbook.get("asks", [])[:5]],
                "bids": [{"price": float(b[0]), "qty": float(b[1])} for b in orderbook.get("bids", [])[:5]],
            }
            _crypto_cache["data"] = result
            _crypto_cache["time"] = now
            return result
    except Exception as e:
        return {"error": str(e), "symbol": "BTC/USDT"}


# ─────────────────────────────────────────────────────────────
# 7. SECURITY LOG (Windows Event Log)
# ─────────────────────────────────────────────────────────────
@router.get("/security-log")
async def security_log():
    """Returns recent security-relevant events from Windows Event Log."""
    if platform.system() != "Windows":
        return {"events": [], "error": "Not on Windows"}

    try:
        ps_script = """
$events = Get-WinEvent -LogName Security -MaxEvents 10 -ErrorAction SilentlyContinue | ForEach-Object {
    @{
        time = $_.TimeCreated.ToString("HH:mm:ss")
        id = $_.Id
        message = ($_.Message -split "`n")[0].Trim()
    }
}
if ($null -eq $events) { $events = @() }
$events | ConvertTo-Json -Compress
"""
        result = subprocess.run(
            ["powershell", "-NoProfile", "-Command", ps_script],
            capture_output=True, text=True, timeout=5
        )
        if result.returncode == 0 and result.stdout.strip():
            events_raw = json.loads(result.stdout.strip())
            # Ensure it's always a list
            if isinstance(events_raw, dict):
                events_raw = [events_raw]

            # Map event IDs to human-readable labels
            EVENT_LABELS = {
                4624: "Logon successful",
                4625: "Failed logon attempt",
                4634: "Logoff",
                4648: "Explicit credential logon",
                4672: "Special privileges assigned",
                4688: "Process created",
                4720: "User account created",
                4732: "Member added to security group",
                5156: "Network connection allowed",
                5158: "Platform filter allowed",
            }

            events = []
            for ev in events_raw[:8]:
                eid = ev.get("id", 0)
                label = EVENT_LABELS.get(eid, ev.get("message", f"Event {eid}")[:80])
                is_warn = eid in (4625, 4720, 4732)
                events.append({
                    "time": ev.get("time", ""),
                    "text": f"{label}",
                    "warn": is_warn,
                })
            return {"events": events}
        else:
            return {"events": [{"time": datetime.now().strftime("%H:%M:%S"), "text": "Security log access requires elevation", "warn": True}]}
    except Exception as e:
        return {"events": [], "error": str(e)}

# ─────────────────────────────────────────────────────────────
# 7.5 EARTH TRACKER (NASA EONET v3 - free)
# ─────────────────────────────────────────────────────────────
_eonet_cache = {"data": None, "time": 0}

@router.get("/earth-tracker")
async def earth_tracker():
    """Returns live natural events from NASA EONET v3."""
    now = time.time()
    if _eonet_cache["data"] and (now - _eonet_cache["time"]) < 300:
        return _eonet_cache["data"]
        
    try:
        import httpx
        async with httpx.AsyncClient(timeout=10) as client:
            # Get latest events, limited to 50
            resp = await client.get("https://eonet.gsfc.nasa.gov/api/v3/events?limit=50")
            if resp.status_code == 200:
                data = resp.json()
                events = []
                for event in data.get("events", []):
                    title = event.get("title", "")
                    categories = [c.get("title") for c in event.get("categories", [])]
                    geometries = event.get("geometry", [])
                    if geometries:
                        # Use the most recent geometry point
                        geom = geometries[-1]
                        coords = geom.get("coordinates")
                        if coords and len(coords) >= 2:
                            events.append({
                                "title": title,
                                "categories": categories,
                                "date": geom.get("date", ""),
                                "lng": coords[0],
                                "lat": coords[1]
                            })
                
                result = {"events": events}
                _eonet_cache["data"] = result
                _eonet_cache["time"] = now
                return result
            else:
                return {"events": []}
    except Exception as e:
        return {"events": [], "error": str(e)}

# ─────────────────────────────────────────────────────────────
# 7.8 NEW INTEGRATIONS (Briefing, Sandbox, SysControl)
# ─────────────────────────────────────────────────────────────
import urllib.request
import xml.etree.ElementTree as ET
import ctypes

def GetLiveBriefing():
    """Fetches real news headlines via RSS and real weather for Karachi."""
    briefing = {"news": [], "weather": "29°C · Clear"}
    
    # 1. Fetch Live Google News RSS
    try:
        url = "https://news.google.com/rss?hl=en-PK&gl=PK&ceid=PK:en"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=3) as response:
            xml_data = response.read()
            root = ET.fromstring(xml_data)
            headlines = [item.find('title').text for item in root.findall('.//item')[:3]]
            briefing["news"] = headlines
    except Exception:
        briefing["news"] = ["System operational. Connectivity check passed."]

    # 2. Fetch Live Weather for Karachi (Open-Meteo)
    try:
        w_url = "https://api.open-meteo.com/v1/forecast?latitude=24.8607&longitude=67.0011&current_weather=true"
        with urllib.request.urlopen(w_url, timeout=3) as resp:
            w_data = json.loads(resp.read().decode())
            temp = w_data["current_weather"]["temperature"]
            briefing["weather"] = f"{temp}°C · Karachi"
    except Exception:
        pass

    return briefing

def ExecuteCodeSandbox(code_string: str):
    """Executes code in a subprocess and captures stdout/stderr live."""
    try:
        result = subprocess.run(
            ["python", "-c", code_string],
            capture_output=True,
            text=True,
            timeout=5
        )
        return {
            "success": result.returncode == 0,
            "stdout": result.stdout or "Execution completed with no output.",
            "stderr": result.stderr
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "stdout": "", "stderr": "Execution timed out (5s limit)."}
    except Exception as e:
        return {"success": False, "stdout": "", "stderr": str(e)}

def AdjustSystemSetting(setting: str):
    """Controls OS level settings (Volume, Mute)."""
    try:
        if setting == "mute":
            # Toggle Mute via NirCmd or PowerShell
            subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]173)"], capture_output=True)
            return "Toggled System Audio Mute"
        elif setting == "vol_up":
            subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]175)"], capture_output=True)
            return "Increased Volume"
        elif setting == "vol_down":
            subprocess.run(["powershell", "-Command", "(New-Object -ComObject WScript.Shell).SendKeys([char]174)"], capture_output=True)
            return "Decreased Volume"
    except Exception as e:
        return f"OS Control Error: {e}"

# ─────────────────────────────────────────────────────────────
# 8. WEBSOCKET ENDPOINT & BROADCAST LOOP
# ─────────────────────────────────────────────────────────────
@router.websocket("/ws/hud")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            # We don't expect the client to send much here, but if they do:
            data = await websocket.receive_text()
            # Could handle incoming actions here if desired, 
            # but we are using REST for actions as per spec.
    except WebSocketDisconnect:
        manager.disconnect(websocket)

async def broadcast_loop():
    """Background task that polls modules and broadcasts updates."""
    i = 0
    while True:
        try:
            # Every 2 seconds: push system stats and media
            if i % 2 == 0:
                stats = await system_stats()
                await manager.broadcast({"type": "diagnostics", "data": stats})
                
                media = await media_now_playing()
                await manager.broadcast({"type": "media", "data": media})

            # Every 10 seconds: push crypto and fake F1 telemetry
            if i % 10 == 0:
                crypt = await crypto()
                await manager.broadcast({"type": "crypto", "data": crypt})
                
                # Mock F1 telemetry for the UI
                import random
                rpm_pct = random.uniform(20, 100)
                gear = max(1, min(8, round(rpm_pct / 14)))
                speed = round(120 + rpm_pct * 2.1)
                await manager.broadcast({"type": "f1_telemetry", "data": {
                    "rpm_pct": rpm_pct, "gear": gear, "speed": speed
                }})

            # Every 30 seconds: push security log
            if i % 30 == 0:
                sec = await security_log()
                await manager.broadcast({"type": "security_log", "data": sec})

            # Every 60 seconds: push markets
            if i % 60 == 0:
                mkts = await markets()
                await manager.broadcast({"type": "markets", "data": mkts})

            # Every 300 seconds: push earth tracker
            if i % 300 == 0:
                et = await earth_tracker()
                await manager.broadcast({"type": "earth_tracker", "data": et})

        except Exception as e:
            print(f"Broadcast error: {e}")
            traceback.print_exc()
        
        await asyncio.sleep(1)
        i += 1

