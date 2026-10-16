import time
import json
import asyncio
import threading
from typing import Dict, Any, Optional, List
from collections import deque

class EventBusManager:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(EventBusManager, cls).__new__(cls)
            cls._instance._init_bus()
        return cls._instance

    def _init_bus(self):
        self._seq = 0
        self._lock = threading.Lock()
        self._active_sockets = []
        self._event_history = deque(maxlen=100) # Ring buffer for reconnect catchup
        self._async_loop: Optional[asyncio.AbstractEventLoop] = None
        self._current_turn_id: Optional[str] = None
        self._current_state: str = "idle"
        self._subscribers: Dict[str, List[Any]] = {}

    def set_loop(self, loop: asyncio.AbstractEventLoop):
        self._async_loop = loop

    def set_turn_id(self, turn_id: Optional[str]):
        with self._lock:
            self._current_turn_id = turn_id

    def register_socket(self, websocket):
        with self._lock:
            if websocket not in self._active_sockets:
                self._active_sockets.append(websocket)
                print(f">> [EVENT BUS]: Client connected. Active clients: {len(self._active_sockets)}")

    def unregister_socket(self, websocket):
        with self._lock:
            if websocket in self._active_sockets:
                self._active_sockets.remove(websocket)
                print(f">> [EVENT BUS]: Client disconnected. Active clients: {len(self._active_sockets)}")

    def build_envelope(self, event_type: str, payload: Dict[str, Any], turn_id: Optional[str] = None) -> Dict[str, Any]:
        with self._lock:
            self._seq += 1
            seq = self._seq
            tid = turn_id or self._current_turn_id
        
        envelope = {
            "v": 1,
            "type": event_type,
            "turn_id": tid,
            "seq": seq,
            "ts": int(time.time() * 1000),
            "payload": payload
        }
        with self._lock:
            self._event_history.append(envelope)
        return envelope

    def broadcast(self, envelope: Dict[str, Any]):
        msg = json.dumps(envelope)
        with self._lock:
            sockets = list(self._active_sockets)
            loop = self._async_loop

        if not sockets:
            return

        async def _safe_send(websocket, text):
            try:
                await websocket.send_text(text)
            except Exception:
                self.unregister_socket(websocket)

        for ws in sockets:
            try:
                coro = _safe_send(ws, msg)
                if loop and loop.is_running():
                    try:
                        cur = asyncio.get_running_loop()
                        if cur == loop:
                            asyncio.create_task(coro)
                        else:
                            asyncio.run_coroutine_threadsafe(coro, loop)
                    except RuntimeError:
                        asyncio.run_coroutine_threadsafe(coro, loop)
            except Exception:
                self.unregister_socket(ws)

    def subscribe(self, event_type: str, callback):
        with self._lock:
            if event_type not in self._subscribers:
                self._subscribers[event_type] = []
            if callback not in self._subscribers[event_type]:
                self._subscribers[event_type].append(callback)

    def unsubscribe(self, event_type: str, callback):
        with self._lock:
            if event_type in self._subscribers and callback in self._subscribers[event_type]:
                self._subscribers[event_type].remove(callback)

    def emit(self, event_type: str, payload: Dict[str, Any], turn_id: Optional[str] = None):
        envelope = self.build_envelope(event_type, payload, turn_id)
        self.broadcast(envelope)
        
        with self._lock:
            subs = list(self._subscribers.get(event_type, [])) + list(self._subscribers.get("*", []))
        for cb in subs:
            try:
                cb(payload)
            except Exception as e:
                print(f"!! [EVENT BUS SUBSCRIBER ERROR]: {e}")
                
        return envelope

    # --- Convenience Emitters for Pipeline Stages ---

    def emit_state(self, status: str, details: str = ""):
        self._current_state = status
        return self.emit("state", {"status": status, "details": details})

    def emit_transcript(self, text: str, is_final: bool = False, confidence: float = 1.0):
        t_type = "transcript.final" if is_final else "transcript.partial"
        return self.emit(t_type, {"text": text, "confidence": confidence})

    def emit_assistant(self, text: str, is_final: bool = False):
        t_type = "assistant.final" if is_final else "assistant.token"
        payload = {"text": text} if is_final else {"token": text}
        return self.emit(t_type, payload)

    def emit_tool_start(self, tool: str, args: Dict[str, Any]):
        return self.emit("tool.start", {"tool": tool, "args": args})

    def emit_tool_result(self, tool: str, ok: bool, result: Any, error: Optional[str] = None):
        return self.emit("tool.result", {"tool": tool, "ok": ok, "result": result, "error": error})

    def emit_ui_open(self, widget: str):
        return self.emit("ui.open", {"widget": widget})

    def emit_diagnostics(self, cpu: float, mem: float, gpu: float = 0.0, temp: float = 45.0, net_down: float = 0.0, net_up: float = 0.0):
        return self.emit("diagnostics", {
            "cpu": cpu,
            "ram": mem,
            "gpu": gpu,
            "core_temp": temp,
            "net_down_mbps": net_down,
            "net_up_mbps": net_up
        })

    def emit_home_devices(self, devices: List[Dict[str, Any]]):
        return self.emit("home.devices", {"devices": devices})

    def emit_f1(self, leader: str = "VER", gap: str = "+2.4s", lap: int = 44, rpm_pct: int = 80, gear: int = 6, speed: int = 295):
        return self.emit("f1", {
            "leader": leader,
            "gap": gap,
            "lap": lap,
            "rpm_pct": rpm_pct,
            "gear": gear,
            "speed": speed
        })

    def emit_quant(self, symbol: str, price: float, change_pct: float = 0.0, candles: Optional[List[Dict[str, Any]]] = None, asks: Optional[list] = None, bids: Optional[list] = None):
        return self.emit("quant", {
            "symbol": symbol,
            "price": price,
            "change_pct": change_pct,
            "candles": candles or [],
            "asks": asks or [],
            "bids": bids or []
        })

    def emit_earth_track(self, target: str, lat: float, lon: float, altitude_km: float = 408.0, blips: Optional[list] = None):
        return self.emit("earth.track", {
            "target": target,
            "lat": lat,
            "lon": lon,
            "altitude_km": altitude_km,
            "blips": blips or []
        })

    def emit_dynamic_result(self, title: str, html: str):
        return self.emit("dynamic.result", {"title": title, "html": html})

    def emit_health(self, subsystems: Optional[Dict[str, str]] = None):
        subs = subsystems or {
            "stt": "ok",
            "llm": "ok",
            "tts": "ok",
            "iot": "ok",
            "fast_router": "ok"
        }
        return self.emit("health", {"subsystems": subs})

    def get_catchup_events(self, last_seq: int) -> List[Dict[str, Any]]:
        with self._lock:
            return [ev for ev in self._event_history if ev["seq"] > last_seq]

# Global singleton
EventBus = EventBusManager()
event_bus = EventBus
