from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QTextEdit, QStackedWidget, QWidget,
    QVBoxLayout, QHBoxLayout, QPushButton, QFrame, QLabel, QGraphicsOpacityEffect
)
from PyQt5.QtGui import QMovie, QFont, QPixmap, QColor
from PyQt5.QtCore import Qt, QSize, QTimer, QPropertyAnimation, QEasingCurve, QPoint
from dotenv import dotenv_values
import sys
import os

# ===================== CONFIG & PATHS =====================
if getattr(sys, 'frozen', False):
    current_dir = os.path.dirname(sys.executable)
else:
    current_dir = os.getcwd()

TempDirPath = os.path.join(current_dir, "Frontend", "Files")
GraphicsDirPath = os.path.join(current_dir, "Frontend", "Graphics")

os.makedirs(TempDirPath, exist_ok=True)
os.makedirs(GraphicsDirPath, exist_ok=True)

env_path = os.path.join(current_dir, ".env")
env_vars = dotenv_values(env_path)
Assistantname = env_vars.get("Assistantname", "J.A.R.V.I.S")

# ===================== PATH HELPERS =====================
def TempDirectoryPath(name): 
    return os.path.join(TempDirPath, name)

def GraphicsDirectoryPath(name): 
    return os.path.join(GraphicsDirPath, name)

# ===================== STATE HELPERS =====================
def SetAssistantStatus(status: str):
    with open(TempDirectoryPath("Status.data"), "w", encoding="utf-8") as f:
        f.write(status)

def GetAssistantStatus():
    try:
        with open(TempDirectoryPath("Status.data"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return ""

def SetMicrophoneStatus(val: str):
    with open(TempDirectoryPath("Mic.data"), "w", encoding="utf-8") as f:
        f.write(val)

def GetMicrophoneStatus():
    try:
        with open(TempDirectoryPath("Mic.data"), "r", encoding="utf-8") as f:
            return f.read().strip()
    except:
        return "False"

def ShowTextToScreen(text: str):
    with open(TempDirectoryPath("Responses.data"), "a", encoding="utf-8") as f:
        f.write(text + "\n")

def AnswerModifier(text: str): return text.strip()
def QueryModifier(text: str): return text.strip()

# ===================== STYLES =====================
MAIN_STYLE = """
QWidget {
    background-color: black;
    color: #E0E0E0;
    font-family: 'Segoe UI';
}
"""

# ===================== CHAT SECTION =====================
class ChatSection(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 20, 40, 40)

        self.chat = QTextEdit()
        self.chat.setReadOnly(True)
        self.chat.setFrameStyle(QFrame.NoFrame)
        self.chat.setFont(QFont("Segoe UI", 13))
        self.chat.setStyleSheet("background: transparent;")
        layout.addWidget(self.chat)

        self.last_line_count = 0
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.refresh)
        self.timer.start(50)

    def refresh(self):
        path = TempDirectoryPath("Responses.data")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    lines = f.read().splitlines()
                if len(lines) > self.last_line_count:
                    for line in lines[self.last_line_count:]:
                        self.chat.append(line)
                    self.last_line_count = len(lines)
            except:
                pass

# ===================== HOME SCREEN =====================
class InitialScreen(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 80)

        # 1. GIF
        self.gif = QLabel()
        gif_path = GraphicsDirectoryPath("Jarvis.gif")
        
        if os.path.exists(gif_path):
            movie = QMovie(gif_path)
            movie.setScaledSize(QSize(500, 400)) 
            self.gif.setMovie(movie)
            movie.start()
        else:
            self.gif.setText("GIF NOT FOUND")
            
        self.gif.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.gif)

        # 2. Dynamic Status Label
        self.status_label = QLabel("Available...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setFont(QFont("Segoe UI", 20, QFont.DemiBold))
        self.status_label.setStyleSheet("color: #888; letter-spacing:1px;")
        layout.addWidget(self.status_label)

        # Opacity effect for pulsing
        self.opacity_effect = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(self.opacity_effect)
        self.animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.animation.setDuration(1000)
        self.animation.setStartValue(1.0)
        self.animation.setEndValue(0.3)
        self.animation.setEasingCurve(QEasingCurve.InOutQuad)
        self.animation.setLoopCount(-1)

        # 3. Status Monitor
        self.status_timer = QTimer(self)
        self.status_timer.timeout.connect(self.poll_backend_status)
        self.status_timer.start(300) # Ping backend every 300ms

        self.current_status_state = ""

    def poll_backend_status(self):
        backend_status = GetAssistantStatus()
        if not backend_status:
            backend_status = "Available..."

        # Only update the UI if the status actually changed
        if backend_status != self.current_status_state:
            self.current_status_state = backend_status
            self.status_label.setText(backend_status)

            # Dynamic UI Colors based on explicit AI state
            if "Listening" in backend_status:
                self.status_label.setStyleSheet("color: #00ff00; font-size: 20px; font-weight: 600; letter-spacing:1px;") # Green Pulse
                self.animation.start()
            elif "Responding" in backend_status or "Processing" in backend_status:
                self.status_label.setStyleSheet("color: #00aaff; font-size: 20px; font-weight: 600; letter-spacing:1px;") # Blue Pulse
                self.animation.start()
            elif "Unavailable" in backend_status:
                self.status_label.setStyleSheet("color: #ff0000; font-size: 20px; font-weight: 500; letter-spacing:1px;") # Solid Red
                self.animation.stop()
                self.opacity_effect.setOpacity(1.0)
            else:
                self.status_label.setStyleSheet("color: #888; font-size: 20px; font-weight: 500; letter-spacing:1px;") # Solid Grey
                self.animation.stop()
                self.opacity_effect.setOpacity(1.0)

# ===================== TOP BAR =====================
class CustomTopBar(QWidget):
    def __init__(self, parent, stack):
        super().__init__(parent)
        self.stack = stack
        self.oldPos = None 
        self.setFixedHeight(50)
        self.setStyleSheet("background:black; border-bottom:1px solid #1a1a1a;")

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)

        # Title
        title = QLabel("J.A.R.V.I.S")
        title.setFont(QFont("Segoe UI", 16, QFont.Normal))
        title.setStyleSheet("color: #888; letter-spacing:3px;")
        layout.addWidget(title)
        layout.addStretch()

        # Buttons
        btn_home = QPushButton("Home")
        btn_chat = QPushButton("Chat")
        btn_min = QPushButton("—")
        btn_close = QPushButton("✕")

        flat_btn_style = """
        QPushButton {
            background-color: #1f1f1f;
            border: none;
            border-radius: 12px;
            padding: 6px 16px;
            color: #AAA;
        }
        QPushButton:hover {
            background-color: #333;
            color: white;
        }
        """
        btn_home.setStyleSheet("font-weight: bold;" + flat_btn_style)
        btn_chat.setStyleSheet("font-weight: bold;" + flat_btn_style)
        btn_min.setStyleSheet(flat_btn_style)

        btn_close.setStyleSheet("""
        QPushButton {
            background-color: #aa0000;
            border: none;
            border-radius: 12px;
            padding: 6px 16px;
            color: white;
            font-weight: bold;
        }
        QPushButton:hover {
            background-color: #ff0000;
        }
        """)

        btn_home.clicked.connect(lambda: self.stack.setCurrentIndex(0))
        btn_chat.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        btn_min.clicked.connect(self.window().showMinimized)
        btn_close.clicked.connect(self.window().close)

        layout.addWidget(btn_home)
        layout.addWidget(btn_chat)
        layout.addWidget(btn_min)
        layout.addWidget(btn_close)

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        if self.oldPos:
            delta = QPoint(event.globalPos() - self.oldPos)
            self.window().move(self.window().x() + delta.x(), self.window().y() + delta.y())
            self.oldPos = event.globalPos()

    def mouseReleaseEvent(self, event):
        self.oldPos = None

# ===================== MAIN =====================
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setStyleSheet(MAIN_STYLE)

        stack = QStackedWidget()
        stack.addWidget(InitialScreen())
        stack.addWidget(ChatSection())

        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(CustomTopBar(self, stack))
        layout.addWidget(stack)

        root = QWidget()
        root.setLayout(layout)
        self.setCentralWidget(root)
        self.showMaximized()

def GraphicalUserInterface():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == '__main__':
    GraphicalUserInterface()