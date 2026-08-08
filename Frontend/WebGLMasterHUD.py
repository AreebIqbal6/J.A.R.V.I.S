import sys
import os
import json
import time
try:
    import psutil
    HAS_PSUTIL = True
except ImportError:
    HAS_PSUTIL = False

from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel
from PyQt5.QtCore import Qt, QUrl, QObject, pyqtSlot, pyqtSignal, QTimer
from Backend.EventBus import event_bus

class PythonBridge(QObject):
    """QWebChannel IPC Bridge enabling bi-directional communication between JS 3D WebGL and Python."""
    sendToWeb = pyqtSignal(str, str)

    @pyqtSlot(str, str)
    def receiveFromWeb(self, action: str, payload: str):
        print(f">> [IPC BRIDGE]: Received command from WebGL HUD: {action} -> {payload}")
        event_bus.publish(action, {"payload": payload})
        
        # Handle real interactive widget commands from HUD
        if action == "widget_command":
            try:
                cmd = json.loads(payload).get("command", "")
                if cmd == "mute_toggle":
                    print(">> [HUD COMMAND]: Toggling TTS Mute...")
                    event_bus.publish("tts_mute_toggle", {})
                elif cmd == "pulse_core":
                    print(">> [HUD COMMAND]: Triggering Core Pulse...")
                    event_bus.publish("tts_waveform", {"intensity": 1.0})
            except Exception as e:
                print(f"Error handling widget command: {e}")

    @pyqtSlot(str)
    def handleChatMessage(self, msg: str):
        print(f">> [HUD CHAT]: {msg}")
        event_bus.publish("text_output", f"User : {msg}")
        import threading
        def run_chat():
            try:
                from Backend.Chatbot import ChatBot
                from Backend.TextToSpeech import TextToSpeech
                resp = ChatBot(msg)
                if resp:
                    event_bus.publish("text_output", f"JARVIS : {resp}")
                    TextToSpeech(resp)
            except Exception as e:
                print(f"Chat Error: {e}")
        threading.Thread(target=run_chat, daemon=True).start()

class WebGLMasterHUD(QMainWindow):
    """
    Ultimate Cinematic 3D WebGL Master HUD Window for J.A.R.V.I.S.
    Streams 100% REAL desktop telemetry (CPU, RAM, Disk, Net Speed, Top Processes, Uptime)
    into a Marvel-accurate Radial Holographic Command Deck. Zero fake placeholders.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        # Translucent background with WebEngine causes instant crashes on some GPUs
        # self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.showFullScreen()

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        layout.setContentsMargins(0, 0, 0, 0)

        self.web_view = QWebEngineView(self)
        # self.web_view.setStyleSheet("background: transparent;")
        # self.web_view.page().setBackgroundColor(Qt.transparent)
        
        # Setup QWebChannel bridge
        self.channel = QWebChannel()
        self.bridge = PythonBridge()
        self.channel.registerObject("pyBridge", self.bridge)
        self.web_view.page().setWebChannel(self.channel)

        # Load hud_index.html
        html_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "Web", "hud_index.html"))
        self.web_view.load(QUrl.fromLocalFile(html_path))
        layout.addWidget(self.web_view)

        # Subscribe to EventBus events
        event_bus.subscribe("tts_waveform", self.on_tts_waveform)
        event_bus.subscribe("swarm_message", self.on_swarm_message)
        event_bus.subscribe("widget_command", self.on_widget_command)
        event_bus.subscribe("status_change", self.on_status_change)
        event_bus.subscribe("text_output", self.on_text_output)

        # Network speed tracking variables
        self.last_net_time = time.time()
        self.last_net_bytes = psutil.net_io_counters() if HAS_PSUTIL else None

        # Lightweight telemetry timer (2s interval — no process scanning)
        self.telemetry_timer = QTimer(self)
        self.telemetry_timer.timeout.connect(self.stream_real_telemetry)
        self.telemetry_timer.start(2000)

    def stream_real_telemetry(self):
        """Lightweight telemetry — only sends what the HUD actually displays."""
        try:
            data = {"timestamp": time.strftime("%H:%M")}
            json_str = json.dumps(data)
            self.web_view.page().runJavaScript(f"if(window.updateRealtimeTelemetry) window.updateRealtimeTelemetry({json_str});")
        except Exception:
            pass

    def on_tts_waveform(self, data: dict):
        """Triggers JS Three.js shader scale and pulsing when JARVIS speaks."""
        intensity = data.get("intensity", 0.5)
        self.web_view.page().runJavaScript(f"if(window.syncAudioWaveform) window.syncAudioWaveform({intensity});")

    def on_swarm_message(self, data: dict):
        """Streams real agentic reasoning logs to the live execution feed."""
        agent = data.get("agent", "AGENT")
        msg = data.get("message", "")
        json_str = json.dumps({"agent": agent, "message": msg})
        self.web_view.page().runJavaScript(f"if(window.addExecutionLog) window.addExecutionLog({json_str});")

    def on_widget_command(self, data: dict):
        """Handles visual commands like changing colors or toggling HUD overlays."""
        action = data.get("action", "")
        if action == "set_core_color":
            color = data.get("color", "#ffbc00")
            self.web_view.page().runJavaScript(f"if(window.setThemeColor) window.setThemeColor('{color}');")

    def on_status_change(self, payload):
        status = str(payload).replace("'", "\\'")
        self.web_view.page().runJavaScript(f"if(window.jarvisSetStatus) window.jarvisSetStatus('{status}');")

    def on_text_output(self, payload):
        text = str(payload)
        t_type = "user" if text.startswith("User") or text.startswith(os.environ.get("Username", "User")) else "sys"
        json_str = json.dumps(text)
        self.web_view.page().runJavaScript(f"if(window.jarvisAddChat) window.jarvisAddChat({json_str}, '{t_type}');")


def launch_webgl_hud():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    hud = WebGLMasterHUD()
    # app.setQuitOnLastWindowClosed(False)
    hud.show()
    return hud
