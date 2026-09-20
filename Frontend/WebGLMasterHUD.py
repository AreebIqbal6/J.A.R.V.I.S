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

        # Subscribing to EventBus is no longer necessary as all real-time events
        # are now automatically routed through the FastAPI WebSocket in real_data.py
        # and natively handled by hud_index.html.


def launch_webgl_hud():
    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    hud = WebGLMasterHUD()
    # app.setQuitOnLastWindowClosed(False)
    hud.show()
    return hud
