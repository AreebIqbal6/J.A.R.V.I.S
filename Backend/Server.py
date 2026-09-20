from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import uvicorn
import asyncio
import psutil
import json

# Import your newly upgraded Agentic brain
from Backend.Chatbot import ChatBot
from Backend import real_data
from Backend.real_data import ExecuteCodeSandbox, AdjustSystemSetting, GetLiveBriefing

# Initialize the High-Speed API Server
app = FastAPI(title="J.A.R.V.I.S. Mark IV Central Nervous System")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import Backend.real_data as real_data
app.include_router(real_data.router)

active_websockets = []
last_net = {"sent": 0, "recv": 0, "time": 0}

async def telemetry_loop():
    global last_net
    while True:
        try:
            if active_websockets:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                
                temp = 45.0
                try:
                    temps = psutil.sensors_temperatures()
                    if temps:
                        for name, entries in temps.items():
                            if entries:
                                temp = entries[0].current
                                break
                except:
                    pass
                
                net = psutil.net_io_counters()
                import time
                now = asyncio.get_event_loop().time()
                dt = now - last_net["time"]
                
                if dt > 0 and last_net["time"] > 0:
                    net_down = round((net.bytes_recv - last_net["recv"]) * 8 / dt / 1_000_000, 1)
                    net_up = round((net.bytes_sent - last_net["sent"]) * 8 / dt / 1_000_000, 1)
                else:
                    net_down, net_up = 0.0, 0.0
                    
                last_net["sent"] = net.bytes_sent
                last_net["recv"] = net.bytes_recv
                last_net["time"] = now

                payload_data = {
                    "type": "telemetry",
                    "cpu": cpu,
                    "ram": ram,
                    "temp": temp,
                    "net_down": net_down,
                    "net_up": net_up
                }

                # Fetch GetLiveBriefing() every 60 seconds (approx every 40 iterations of 1.5s loop)
                if not hasattr(telemetry_loop, "counter"):
                    telemetry_loop.counter = 0
                if telemetry_loop.counter % 40 == 0:
                    try:
                        briefing_data = await asyncio.to_thread(GetLiveBriefing)
                        telemetry_loop.last_briefing = briefing_data
                    except Exception as e:
                        print(f"Briefing fetch error: {e}")
                        
                if hasattr(telemetry_loop, "last_briefing"):
                    payload_data["briefing"] = telemetry_loop.last_briefing
                    
                telemetry_loop.counter += 1

                payload = json.dumps(payload_data)
                
                for ws in active_websockets:
                    await ws.send_text(payload)
        except Exception as e:
            print(f"Telemetry error: {e}")
            
        await asyncio.sleep(1.5)

import threading

def run_hotword_stt_loop():
    print(">> [HOTWORD ENGINE]: Local STT background loop starting...")
    from Backend.SpeechToText import SpeechRecognition
    from Backend.Chatbot import ChatBot
    from Backend.TextToSpeech import TextToSpeech
    import time
    
    while True:
        try:
            query = SpeechRecognition()
            if query and query.strip():
                print(f">> [LOCAL VOICE]: {query}")
                
                # Push user query to frontend
                if getattr(real_data, 'server_loop', None):
                    msg = json.dumps({"type": "chat_user", "content": query})
                    for ws in active_websockets:
                        asyncio.run_coroutine_threadsafe(ws.send_text(msg), real_data.server_loop)
                
                response_text = ChatBot(query)
                print(f">> [LOCAL AI]: {response_text}")
                
                # Push AI response to frontend
                if getattr(real_data, 'server_loop', None):
                    msg = json.dumps({"type": "chat_response", "content": response_text})
                    for ws in active_websockets:
                        asyncio.run_coroutine_threadsafe(ws.send_text(msg), real_data.server_loop)
                
                TextToSpeech(response_text)
                
        except Exception as e:
            print(f"STT Hotword error: {e}")
            time.sleep(2)

@app.on_event("startup")
async def startup_event():
    real_data.server_loop = asyncio.get_running_loop()
    asyncio.create_task(real_data.broadcast_loop())
    asyncio.create_task(telemetry_loop())
    threading.Thread(target=run_hotword_stt_loop, daemon=True).start()

@app.get("/")
async def root():
    try:
        with open("index.html", "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content)
    except FileNotFoundError:
        return HTMLResponse(content="<h1>index.html not found</h1>", status_code=404)

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_websockets.append(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            try:
                payload = json.loads(data)
                if payload.get("type") == "chat" and "query" in payload:
                    query = payload["query"]
                    print(f">> [WS CHAT IN]: {query}")
                    
                    response_text = await asyncio.to_thread(ChatBot, query)
                    print(f">> [WS CHAT OUT]: {response_text}")
                    
                    await websocket.send_text(json.dumps({
                        "type": "chat_response",
                        "content": response_text
                    }))
                    
                    # Ignite Voice Output
                    from Backend.TextToSpeech import TextToSpeech
                    await asyncio.to_thread(TextToSpeech, response_text)
                    
                elif payload.get("type") == "code_run" and "code" in payload:
                    code = payload["code"]
                    result = await asyncio.to_thread(ExecuteCodeSandbox, code)
                    await websocket.send_text(json.dumps({
                        "type": "code_result",
                        "data": result
                    }))
                    
                elif payload.get("type") == "os_control" and "action" in payload:
                    setting = payload["action"]
                    result = await asyncio.to_thread(AdjustSystemSetting, setting)
                    print(f">> [SYS CONTROL]: {result}")
            except json.JSONDecodeError:
                pass
    except WebSocketDisconnect:
        active_websockets.remove(websocket)

@app.websocket("/pty")
async def pty_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        from winpty import PtyProcess
        import os
        moviebox_path = os.path.abspath(os.path.join("Tools", "MovieBox", "moviebox-tui.exe"))
        
        # Start MovieBox TUI in the PTY
        proc = PtyProcess.spawn(moviebox_path)
        
        async def read_from_pty():
            while proc.isalive():
                try:
                    data = await asyncio.to_thread(proc.read, 1024)
                    if not data: break
                    await websocket.send_text(data)
                except Exception:
                    break
                    
        asyncio.create_task(read_from_pty())
        
        while proc.isalive():
            data = await websocket.receive_text()
            proc.write(data)
            
    except WebSocketDisconnect:
        try:
            if 'proc' in locals() and proc.isalive():
                proc.terminate()
        except: pass
    except Exception as e:
        print(f"PTY Error: {e}")

class UserQuery(BaseModel):
    text: str

@app.post("/api/think")
@app.post("/api/chat")
async def process_query(query: UserQuery):
    try:
        response_text = ChatBot(query.text)
        return {"text": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/openclaw/webhook")
async def openclaw_webhook(payload: dict):
    try:
        user_message = payload.get("message", "")
        if not user_message:
            return {"status": "ignored", "reason": "empty message"}
        response_text = ChatBot(user_message)
        return {"status": "success", "reply": response_text}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    print("\n>> IGNITING FASTAPI SERVER ON PORT 8000...")
    uvicorn.run("Backend.Server:app", host="127.0.0.1", port=8000, reload=False)