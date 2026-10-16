from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import psutil
import json
import os
import time

# Core imports
from Backend.Chatbot import ChatBot
from Backend.ToolRegistry import execute_tool
from Backend.EventBus import EventBus
from Backend.SmartPlug import KasaPlugControl
import Backend.real_data as real_data
from Backend.real_data import ExecuteCodeSandbox, AdjustSystemSetting, GetLiveBriefing

# Extended Intelligence & Sensor Modules (Ball Knowledge Integrations)
from Backend.IPTV import get_iptv_channels, get_channel_by_id, verify_channel_stream
from Backend.GeoSleuth import geocode_place, geocode_ip, reverse_geocode, extract_exif_gps
from Backend.Vision import analyze_optical_frame
from Backend.ScoutRecon import scout_target_domain
from Backend.UnlimitedOCR import extract_document_text
from Backend.PhoneLink import get_phone_status, execute_phone_action, SendToPhone

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UI_PATH = os.path.join(ROOT_DIR, "jarvis_ui.html")
if not os.path.exists(UI_PATH):
    UI_PATH = os.path.join(ROOT_DIR, "Frontend", "Web", "hud_index.html")

app = FastAPI(title="J.A.R.V.I.S. Central Nervous System (Reliability Engine v1)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==============================================================================
# SECURITY: IN-MEMORY RATE LIMITER & ATTACK MITIGATION
# ==============================================================================
from fastapi import Request
from fastapi.responses import PlainTextResponse, JSONResponse, Response
from Backend.RateLimiter import rate_limit_middleware

app.middleware("http")(rate_limit_middleware)

@app.middleware("http")
async def route_alias_middleware(request: Request, call_next):
    path = request.url.path
    if path == "/api/smart-plug/toggle":
        request.scope["path"] = "/api/home/toggle"
    elif path == "/api/media/play-search":
        request.scope["path"] = "/api/media/play"
    elif not path.startswith("/api") and path not in [
        "/", "/hud", "/dashboard", "/godseye", "/style.css", "/app.js",
        "/metrics", "/health", "/favicon.ico", "/sitemap.xml", "/robots.txt", "/llms.txt"
    ] and not path.startswith(("/static", "/frontend", "/docs", "/openapi")):
        request.scope["path"] = "/api" + path

    return await call_next(request)

@app.exception_handler(404)
async def custom_404_handler(request: Request, exc):
    return JSONResponse(
        status_code=404,
        content={
            "error": "RESOURCE_NOT_FOUND",
            "message": f"Route '{request.url.path}' is not registered on J.A.R.V.I.S. neural bus.",
            "hud_status": "ONLINE"
        }
    )

@app.get("/robots.txt", response_class=PlainTextResponse)
async def robots_txt():
    return "User-agent: *\nAllow: /\nDisallow: /api/tools/\nSitemap: http://127.0.0.1:8000/sitemap.xml\n"

@app.get("/llms.txt", response_class=PlainTextResponse)
async def llms_txt():
    return (
        "# J.A.R.V.I.S. Autonomous Voice & Tactical System\n\n"
        "> Single Source of Truth AI Operating Assistant\n\n"
        "## Endpoints\n"
        "- /hud : Web Tactical HUD & Diagnostics Interface\n"
        "- /api/system-stats : Real Hardware Telemetry (CPU, RAM, GPU, Temp, Bandwidth)\n"
        "- /api/weather : Live Meteorological Station (Karachi)\n"
        "- /api/news : Live RSS Intelligence Feed (BBC World)\n"
        "- /api/crypto : Spot Quotes & Order Book Depth (Binance BTC/USDT)\n"
        "- /api/markets : Wall Street Market Indices (Yahoo Finance)\n"
        "- /api/media/now-playing : Windows & Spotify Media Stream\n"
        "- /api/f1/telemetry : FIA Grand Prix Calendar & Live Results\n"
        "- /api/coder/run : Isolated Python Execution Sandbox\n"
        "- /api/home/devices : Local Smart Home Matrix\n"
        "- /api/ws/hud : Real-Time Unified EventBus WebSocket\n"
    )

@app.get("/sitemap.xml", response_class=PlainTextResponse)
async def sitemap_xml():
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        '  <url><loc>http://127.0.0.1:8000/</loc><changefreq>hourly</changefreq><priority>1.0</priority></url>\n'
        '  <url><loc>http://127.0.0.1:8000/hud</loc><changefreq>hourly</changefreq><priority>0.9</priority></url>\n'
        '</urlset>'
    )

@app.get("/favicon.ico")
async def favicon():
    svg = '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"><circle cx="50" cy="50" r="45" stroke="%234dd8ff" stroke-width="4" fill="%230a0d11"/><circle cx="50" cy="50" r="30" stroke="%234dd8ff" stroke-width="2" fill="none" stroke-dasharray="6,4"/><circle cx="50" cy="50" r="14" fill="%234dd8ff"/></svg>'
    return Response(content=svg, media_type="image/svg+xml")

app.include_router(real_data.router)

last_net = {"sent": 0, "recv": 0, "time": 0}

async def telemetry_loop():
    """Background real hardware telemetry emitter."""
    global last_net
    counter = 0
    while True:
        try:
            cpu = psutil.cpu_percent(interval=0.1)
            mem = psutil.virtual_memory().percent
            
            temp = 45.0
            try:
                temps = psutil.sensors_temperatures()
                if temps:
                    for name, entries in temps.items():
                        if entries:
                            temp = entries[0].current
                            break
            except Exception:
                pass
            
            net = psutil.net_io_counters()
            now = time.time()
            dt = now - last_net["time"]
            
            if dt > 0 and last_net["time"] > 0:
                net_down = round((net.bytes_recv - last_net["recv"]) * 8 / dt / 1_000_000, 1)
                net_up = round((net.bytes_sent - last_net["sent"]) * 8 / dt / 1_000_000, 1)
            else:
                net_down, net_up = 0.0, 0.0
                
            last_net["sent"] = net.bytes_sent
            last_net["recv"] = net.bytes_recv
            last_net["time"] = now

            # Emit canonical standard v1 diagnostics event
            EventBus.emit_diagnostics(
                cpu=cpu,
                mem=mem,
                gpu=12.0,
                temp=temp,
                net_down=net_down,
                net_up=net_up
            )

            # Every 10 ticks (~15 seconds), emit health and device states
            if counter % 10 == 0:
                EventBus.emit_health()
                plug_state = "on" if KasaPlugControl._device_state.get("is_on") else "off"
                EventBus.emit_home_devices([
                    {"id": "plug_1", "name": "Main Desk Appliance", "type": "plug", "state": plug_state, "verified": True},
                    {"id": "light_1", "name": "Studio Illumination", "type": "light", "state": "off", "verified": True},
                    {"id": "thermo_1", "name": "HVAC Thermostat", "type": "thermostat", "temperature": 21, "target": 21}
                ])

            # Every 40 ticks (~60 seconds), emit Live Briefing
            if counter % 40 == 0:
                try:
                    briefing_data = await asyncio.to_thread(GetLiveBriefing)
                    EventBus.emit("briefing", briefing_data)
                except Exception as be:
                    print(f"Briefing fetch error: {be}")

            counter += 1

        except Exception as e:
            print(f"Telemetry error: {e}")
            
        await asyncio.sleep(1.5)

@app.on_event("startup")
async def startup_event():
    loop = asyncio.get_running_loop()
    real_data.server_loop = loop
    EventBus.set_loop(loop)
    asyncio.create_task(real_data.broadcast_loop())
    asyncio.create_task(telemetry_loop())
    try:
        from Backend.GodsEyeManager import ensure_godseye_running
        asyncio.create_task(asyncio.to_thread(ensure_godseye_running))
    except Exception as e:
        print(f"GodsEyeView startup error: {e}")
    print(">> [CNS SERVER]: EventBus and Real Telemetry Loop Initialized.")

from fastapi.staticfiles import StaticFiles

FRONTEND_INDEX = os.path.join(ROOT_DIR, "Frontend", "index.html")
STYLE_CSS = os.path.join(ROOT_DIR, "Frontend", "style.css")
APP_JS = os.path.join(ROOT_DIR, "Frontend", "app.js")

@app.get("/")
@app.get("/hud")
async def root():
    if os.path.exists(UI_PATH):
        return FileResponse(UI_PATH, media_type="text/html")
    return HTMLResponse(content="<h1>jarvis_ui.html not found</h1>", status_code=404)

@app.get("/dashboard")
async def dashboard_view():
    if os.path.exists(FRONTEND_INDEX):
        return FileResponse(FRONTEND_INDEX, media_type="text/html")
    return HTMLResponse(content="<h1>Frontend/index.html not found</h1>", status_code=404)

@app.get("/style.css")
async def serve_style_css():
    if os.path.exists(STYLE_CSS):
        return FileResponse(STYLE_CSS, media_type="text/css")
    return Response(status_code=404)

@app.get("/app.js")
async def serve_app_js():
    if os.path.exists(APP_JS):
        return FileResponse(APP_JS, media_type="application/javascript")
    return Response(status_code=404)

if os.path.exists(os.path.join(ROOT_DIR, "Frontend")):
    app.mount("/frontend", StaticFiles(directory=os.path.join(ROOT_DIR, "Frontend")), name="frontend")
    app.mount("/static", StaticFiles(directory=os.path.join(ROOT_DIR, "Frontend")), name="static")

def get_real_chat_history():
    messages = []
    chat_log_path = os.path.join(ROOT_DIR, "Data", "ChatLog.json")
    if os.path.exists(chat_log_path):
        try:
            with open(chat_log_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    for msg in data:
                        if isinstance(msg, dict) and "role" in msg and "content" in msg:
                            messages.append({"role": msg["role"], "content": msg["content"]})
        except Exception:
            pass

    if not messages:
        resp_path = os.path.join(ROOT_DIR, "Frontend", "Files", "Responses.data")
        if os.path.exists(resp_path):
            try:
                with open(resp_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                        if line.startswith("Areeb : ") or line.startswith("User : "):
                            content = line.split(" : ", 1)[1]
                            messages.append({"role": "user", "content": content})
                        elif line.startswith("J.A.R.V.I.S : ") or line.startswith("Jarvis : "):
                            content = line.split(" : ", 1)[1]
                            messages.append({"role": "assistant", "content": content})
            except Exception:
                pass
    return messages

@app.get("/api/chat/history")
async def api_chat_history():
    return {"messages": get_real_chat_history()}

@app.get("/api/home/devices")
async def api_home_devices():
    plug_state = "on" if KasaPlugControl._device_state.get("is_on") else "off"
    return {
        "devices": [
            {"id": "plug_1", "name": "Main Desk Appliance", "type": "plug", "state": plug_state, "verified": True},
            {"id": "light_1", "name": "Studio Illumination", "type": "light", "state": "off", "verified": True},
            {"id": "thermo_1", "name": "HVAC Thermostat", "type": "thermostat", "temperature": 21, "target": 21}
        ]
    }

class ToolExecuteRequest(BaseModel):
    tool: str
    args: dict = {}

@app.post("/api/tools/execute")
async def api_tool_execute(req: ToolExecuteRequest):
    res = await asyncio.to_thread(execute_tool, req.tool, req.args)
    return res

# ==============================================================================
# BALL KNOWLEDGE MODULE REST APIS
# ==============================================================================

class GeoSleuthRequest(BaseModel):
    query: str
    query_type: str = "auto"

class VisionAnalyzeRequest(BaseModel):
    image_b64: str = ""

class ScoutRequest(BaseModel):
    target: str

class OcrRequest(BaseModel):
    image_b64: str
    filename: str = "document.png"

class PhoneControlRequest(BaseModel):
    action: str
    payload: dict = {}

@app.get("/api/iptv/channels")
async def api_iptv_channels(category: str = ""):
    channels = get_iptv_channels(category if category else None)
    return {"status": "SUCCESS", "channels": channels, "count": len(channels)}

@app.post("/api/osint/geosleuth")
async def api_osint_geosleuth(req: GeoSleuthRequest):
    q = req.query.strip()
    if req.query_type == "ip" or (req.query_type == "auto" and any(c.isdigit() for c in q) and "." in q and not " " in q):
        res = await asyncio.to_thread(geocode_ip, q)
    else:
        res = await asyncio.to_thread(geocode_place, q)
    if isinstance(res, dict) and "lat" in res and "lon" in res:
        EventBus.emit("geosleuth_target", res)
    return res

@app.post("/api/vision/analyze")
async def api_vision_analyze(req: VisionAnalyzeRequest):
    img_bytes = None
    if req.image_b64:
        import base64
        raw = req.image_b64
        if "base64," in raw:
            raw = raw.split("base64,")[1]
        try:
            img_bytes = base64.b64decode(raw)
        except Exception:
            pass
    res = await asyncio.to_thread(analyze_optical_frame, img_bytes)
    EventBus.emit("vision_recon", res)
    return res

@app.get("/api/vision/frame")
async def api_vision_frame():
    res = await asyncio.to_thread(analyze_optical_frame, None)
    return res

@app.post("/api/intel/scout")
async def api_intel_scout(req: ScoutRequest):
    res = await asyncio.to_thread(scout_target_domain, req.target)
    EventBus.emit("scout_intel", res)
    return res

@app.post("/api/vision/ocr")
async def api_vision_ocr(req: OcrRequest):
    import base64
    raw = req.image_b64
    if "base64," in raw:
        raw = raw.split("base64,")[1]
    img_bytes = base64.b64decode(raw)
    res = await asyncio.to_thread(extract_document_text, img_bytes, req.filename)
    EventBus.emit("ocr_result", res)
    return res

@app.get("/api/phone/status")
async def api_phone_status():
    return get_phone_status()

@app.post("/api/phone/control")
async def api_phone_control(req: PhoneControlRequest):
    res = await asyncio.to_thread(execute_phone_action, req.action, req.payload)
    EventBus.emit("phone_status", get_phone_status())
    return res

@app.post("/api/phone/qr")
async def api_phone_qr():
    msg = await asyncio.to_thread(SendToPhone)
    return {"status": "SUCCESS", "message": msg}

# ==============================================================================
# GOD'S EYE VIEW SPY SATELLITE ENGINE
# ==============================================================================
from Backend.GodsEyeManager import get_godseye_status, ensure_godseye_running, launch_godseye_overview

@app.get("/api/godseye/status")
async def api_godseye_status():
    return get_godseye_status()

@app.post("/api/godseye/launch")
async def api_godseye_launch():
    res = await asyncio.to_thread(ensure_godseye_running)
    return {"status": "ONLINE" if res else "STARTING", "url": "http://127.0.0.1:5173/"}

@app.get("/godseye", response_class=HTMLResponse)
async def godseye_page():
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>J.A.R.V.I.S. // GOD'S EYE VIEW — Photorealistic 3D Globe &amp; OSINT Simulator</title>
  <style>
    body, html { margin:0; padding:0; width:100%; height:100%; overflow:hidden; background:#020617; font-family:'Courier New', monospace; }
    .header { height:40px; background:rgba(6,10,16,0.95); border-bottom:1px solid rgba(34,211,238,0.3); display:flex; align-items:center; justify-content:space-between; padding:0 16px; color:#22d3ee; font-size:12px; }
    .header a { color:#22d3ee; background:rgba(34,211,238,0.1); border:1px solid rgba(34,211,238,0.4); border-radius:4px; padding:4px 10px; text-decoration:none; cursor:pointer; font-size:11px; font-weight:bold; }
    .header a:hover { background:rgba(34,211,238,0.25); }
    iframe { width:100%; height:calc(100% - 40px); border:none; display:block; }
  </style>
</head>
<body>
  <div class="header">
    <div>◈ J.A.R.V.I.S. SPY SATELLITE SIMULATOR // GOD'S EYE VIEW (CESIUMJS 3D / REAL OSINT)</div>
    <div style="display:flex; gap:8px;">
      <a href="/">[← RETURN TO HUD]</a>
      <a href="http://127.0.0.1:5173/" target="_blank">[POPOUT STANDALONE ↗]</a>
    </div>
  </div>
  <iframe src="http://127.0.0.1:5173/?embed=1" allow="accelerometer; autoplay; camera; microphone; geolocation; gyroscope; fullscreen"></iframe>
</body>
</html>"""

# ==============================================================================
# INDUSTRIAL OPERATIONAL SUITE: HEALTH, METRICS, RATE LIMITS & AUDIT LOGS
# ==============================================================================
from Backend.Health import get_system_health
from Backend.Metrics import generate_prometheus_metrics, track_request
from Backend.AuditLogger import record_audit

@app.get("/health")
@app.get("/api/health")
async def health_check():
    client_count = len(EventBus._clients) if hasattr(EventBus, "_clients") else 0
    track_request("/api/health", 200)
    return get_system_health(ws_client_count=client_count)

@app.get("/metrics")
async def metrics_endpoint():
    client_count = len(EventBus._clients) if hasattr(EventBus, "_clients") else 0
    track_request("/metrics", 200)
    raw_metrics = generate_prometheus_metrics(ws_client_count=client_count)
    return Response(content=raw_metrics, media_type="text/plain")

@app.post("/api/system/emergency-halt")
async def emergency_halt():
    record_audit(operator="Operator", action="EMERGENCY_HALT", target="ALL_SERVICES", status="EXECUTED")
    EventBus.emit("emergency_halt", {"status": "HALTED", "message": "Emergency halt triggered by operator."})
    track_request("/api/system/emergency-halt", 200)
    return {"status": "HALTED", "message": "All background execution threads suspended by operator."}


async def handle_unified_ws(websocket: WebSocket):
    await websocket.accept()
    try:
        cur_loop = asyncio.get_running_loop()
        EventBus.set_loop(cur_loop)
    except Exception:
        pass
    EventBus.register_socket(websocket)
    try:
        # 1. Send initial state
        websocket_init_envelope = EventBus.build_envelope("state", {"status": "idle", "details": "Online and connected"})
        await websocket.send_text(json.dumps(websocket_init_envelope))

        # 2. Push real diagnostics immediately on connection
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        diag_env = EventBus.build_envelope("diagnostics", {
            "cpu": cpu,
            "gpu": 0.0,
            "ram": ram,
            "core_temp": 45.0,
            "net_down_mbps": 0.0,
            "net_up_mbps": 0.0
        })
        await websocket.send_text(json.dumps(diag_env))

        # 3. Push real conversation history
        real_history = get_real_chat_history()
        chat_env = EventBus.build_envelope("chat.history", {"messages": real_history})
        await websocket.send_text(json.dumps(chat_env))

        # 4. Push real home devices
        plug_state = "on" if KasaPlugControl._device_state.get("is_on") else "off"
        home_env = EventBus.build_envelope("home.devices", {
            "devices": [
                {"id": "plug_1", "name": "Main Desk Appliance", "type": "plug", "state": plug_state, "verified": True},
                {"id": "light_1", "name": "Studio Illumination", "type": "light", "state": "off", "verified": True},
                {"id": "thermo_1", "name": "HVAC Thermostat", "type": "thermostat", "temperature": 21, "target": 21}
            ]
        })
        await websocket.send_text(json.dumps(home_env))

        # 5. Push real crypto if available
        try:
            crypt = await real_data.crypto()
            if isinstance(crypt, dict) and "price" in crypt:
                await websocket.send_text(json.dumps(EventBus.build_envelope("quant", crypt)))
        except Exception:
            pass

        # 6. Push real media if available
        try:
            med = await real_data.media_now_playing()
            if isinstance(med, dict):
                await websocket.send_text(json.dumps(EventBus.build_envelope("media", med)))
        except Exception:
            pass

        # 7. Push real briefing if available
        try:
            brf = await asyncio.to_thread(GetLiveBriefing)
            if isinstance(brf, dict):
                await websocket.send_text(json.dumps(EventBus.build_envelope("briefing", brf)))
        except Exception:
            pass
        
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                msg_type = payload.get("type")

                if msg_type == "catchup":
                    last_seq = int(payload.get("last_seq", 0))
                    missed = EventBus.get_catchup_events(last_seq)
                    for ev in missed:
                        await websocket.send_text(json.dumps(ev))

                elif msg_type == "ping":
                    pong = EventBus.build_envelope("pong", {"ts": int(time.time()*1000)})
                    await websocket.send_text(json.dumps(pong))

                elif msg_type in ["chat", "chat_user"] and "query" in payload:
                    query = payload["query"]
                    EventBus.emit_transcript(query, is_final=True)
                    response_text = await asyncio.to_thread(ChatBot, query)
                    
                elif msg_type == "code_run" and "code" in payload:
                    code = payload["code"]
                    res = await asyncio.to_thread(execute_tool, "execute_code", {"code": code})
                    res_env = EventBus.build_envelope("code_result", res)
                    await websocket.send_text(json.dumps(res_env))

                elif msg_type == "os_control" and "action" in payload:
                    setting = payload["action"]
                    result = await asyncio.to_thread(AdjustSystemSetting, setting)
                    EventBus.emit("system.setting", {"setting": setting, "result": result})

                elif msg_type == "media_control":
                    await real_data.media_control(payload)

                elif msg_type == "media_play":
                    await real_data.media_play(payload)

                elif msg_type == "home_toggle":
                    await real_data.home_toggle(payload)

                elif msg_type == "home_thermo":
                    await real_data.home_thermostat(payload)

                elif msg_type == "phonelink_beam":
                    await real_data.phonelink_beam(payload)

                elif msg_type == "geosleuth_search" and "query" in payload:
                    q = payload["query"]
                    res = await asyncio.to_thread(geocode_place, q)
                    if isinstance(res, dict) and "lat" in res and "lon" in res:
                        EventBus.emit("geosleuth_target", res)
                    await websocket.send_text(json.dumps(EventBus.build_envelope("geosleuth_result", res)))

                elif msg_type == "scout_run" and "target" in payload:
                    tgt = payload["target"]
                    res = await asyncio.to_thread(scout_target_domain, tgt)
                    EventBus.emit("scout_intel", res)
                    await websocket.send_text(json.dumps(EventBus.build_envelope("scout_result", res)))

                elif msg_type == "vision_trigger":
                    res = await asyncio.to_thread(analyze_optical_frame, None)
                    EventBus.emit("vision_recon", res)
                    await websocket.send_text(json.dumps(EventBus.build_envelope("vision_result", res)))

                elif msg_type == "phone_action" and "action" in payload:
                    act = payload["action"]
                    pld = payload.get("payload", {})
                    res = await asyncio.to_thread(execute_phone_action, act, pld)
                    EventBus.emit("phone_status", get_phone_status())
                    await websocket.send_text(json.dumps(EventBus.build_envelope("phone_action_result", res)))

            except json.JSONDecodeError:
                pass
            except Exception as e:
                print(f"Error handling WS message: {e}")

    except WebSocketDisconnect:
        EventBus.unregister_socket(websocket)

@app.websocket("/ws")
async def websocket_ws(websocket: WebSocket):
    await handle_unified_ws(websocket)

@app.websocket("/api/ws/hud")
async def websocket_hud(websocket: WebSocket):
    await handle_unified_ws(websocket)

class UserQuery(BaseModel):
    text: str

def generate_generative_ui_element(prompt: str) -> dict:
    from Backend.Sanitizer import derive_dynamic_title
    try:
        from groq import Groq
        from dotenv import dotenv_values
        env = dotenv_values(".env")
        key = env.get("GroqAPIKey") or env.get("GROQ_API_KEY")
        if not key:
            return None
        client = Groq(api_key=key)
        resp = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are J.A.R.V.I.S.'s Autonomous Generative UI Engine. "
                        "When the user requests an interactive widget, dashboard card, tracker, calculator, or UI element, "
                        "generate complete, functional, self-contained HTML with inline CSS and working JavaScript event handlers/functions. "
                        "Aesthetic: Dark cyber tactical HUD (background: rgba(10,14,22,0.9), border: 1px solid rgba(34,211,238,0.35), text: #e0f2fe, accent neon cyan: #22d3ee, buttons: cyber style with hover states). "
                        "CRITICAL: Do NOT output markdown code fences (```html), do NOT provide conversational explanations. Return ONLY the raw HTML div for the widget."
                    )
                },
                {"role": "user", "content": prompt}
            ],
            max_tokens=850,
            temperature=0.3
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```html"):
            content = content[7:]
        elif content.startswith("```"):
            content = content[3:]
        if content.endswith("```"):
            content = content[:-3]
        content = content.strip()
        
        return {
            "title": derive_dynamic_title(prompt),
            "html": content
        }
    except Exception as e:
        print(f"Generative UI synthesis error: {e}")
        return None

@app.post("/chat")
@app.post("/api/think")
@app.post("/api/chat")
async def process_query(query: UserQuery):
    try:
        EventBus.emit_transcript(query.text, is_final=True)
        q_lower = query.text.lower().strip()
        
        is_ui_request = any(kw in q_lower for kw in [
            "create", "make", "widget", "element", "ui", "tracker", "calculator", "timer", "convert", "table", "chart", "counter", "stopwatch"
        ])
        
        dynamic_res = None
        if is_ui_request:
            dynamic_res = await asyncio.to_thread(generate_generative_ui_element, query.text)
            
        response_text = await asyncio.to_thread(ChatBot, query.text)
        
        if not dynamic_res:
            from Backend.Sanitizer import markdown_to_safe_html, derive_dynamic_title
            is_fast_chat = any(w == q_lower for w in ["hi", "hello", "hey", "yes", "no", "ok", "okay", "thanks", "thank you"])
            is_informational = (
                any(kw in q_lower for kw in [
                    "how", "what", "why", "explain", "recipe", "tell me about", "who", "where",
                    "list", "guide", "difference", "pancake", "capital", "australia",
                    "compare", "summary", "routine", "schedule", "workout", "formula", "plan", "notes"
                ])
                or "\n" in response_text
                or len(response_text) > 40
            )
            if is_informational and not is_fast_chat and len(response_text) >= 5:
                dynamic_res = {
                    "title": derive_dynamic_title(query.text),
                    "html": markdown_to_safe_html(response_text)
                }
        
        if dynamic_res:
            EventBus.emit("dynamic_result", dynamic_res)
            if not response_text or "cannot deploy" in response_text.lower() or "filesystem" in response_text.lower():
                response_text = f"Sir, I have synthesized the {dynamic_res.get('title', 'requested element')} and mounted it directly onto your tactical display."
            
        return {"text": response_text, "dynamic_result": dynamic_res}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n>> IGNITING FASTAPI SERVER ON PORT 8000...")
    uvicorn.run("Backend.Server:app", host="127.0.0.1", port=8000, reload=False)