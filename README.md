# J.A.R.V.I.S. Mark IV // Autonomous Intelligence Operating System

> **Industrial-Grade Cognitive Engine & Real-Time Geospatial HUD**  
> *Sub-Millisecond Intent Routing | 3D Cesium Telemetry | Real Hardware Control | OSINT & Multi-Modal Perception*

---

## 🏛️ System Architecture

J.A.R.V.I.S. Mark IV operates as a distributed, event-driven operating system designed for low latency, zero crash tolerance, and strict data authenticity.

```
                              +---------------------------------------------+
                              |         3D God's Eye View HUD (Port 5173)   |
                              |   (Cesium / Three.js Geospatial Telemetry)  |
                              +----------------------+----------------------+
                                                     |
                                                     v (WebSockets / HTTP)
                              +---------------------------------------------+
                              |         FastAPI Central Nervous System      |
                              |              (Backend/Server.py : 8000)     |
                              +----------------------+----------------------+
                                                     |
            +----------------------------------------+----------------------------------------+
            |                                        |                                        |
            v                                        v                                        v
+-----------------------+                +-----------------------+                +-----------------------+
|  FastRouter Engine    |                |    Async EventBus     |                |   Real Hardware Hub   |
|  - Sub-ms Regex Cache |                |  - Telemetry Pipeline |                |  - TP-Link Kasa/Tapo  |
|  - Groq Llama 3.3 70B |                |  - SRE System Metrics |                |  - Smart TV / HDMI    |
|  - Bilingual (EN/UR)  |                |  - Windows Media Sync |                |  - IoT MQTT Matrix    |
+-----------------------+                +-----------------------+                +-----------------------+
```

---

## 📂 Project Structure

```
├── Backend/                     # Core Operating System & Services
│   ├── FastRouter.py            # Sub-millisecond regex router & intent classifier
│   ├── Server.py                # FastAPI server, WebSockets bridge & rate limiter
│   ├── real_data.py             # Live telemetry APIs (system, media, crypto, NASA)
│   ├── EventBus.py              # Asynchronous pub/sub event distribution matrix
│   ├── SmartPlug.py             # Wireless local TP-Link Kasa & Tapo controller
│   ├── SpotifyController.py     # Spotify API & native Windows media dispatch
│   ├── F1_Engineer.py           # Formula 1 telemetry and race engineer logic
│   ├── EarthTracker.py          # NASA EONET v3 & ISS orbital coordinate tracking
│   ├── GeoSleuth.py             # EXIF geolocation & IP geocoding
│   ├── UnlimitedOCR.py          # Optical document character recognition
│   ├── Vision.py                # Visual frame analysis
│   ├── PhoneLink.py             # QR clipboard beam & cellular synchronization
│   ├── IPTV.py                  # IPTV channel verification and streaming
│   ├── Security.py              # Security auditing & event validation
│   └── ToolRegistry.py          # Verified tool implementations with readback
├── Frontend/                    # Industrial User Interface & HUD
│   ├── Web/
│   │   └── hud_index.html       # Cyberpunk glassmorphic tactical dashboard
│   ├── Graphics/                # Visual assets, icons, and interface animations
│   ├── app.js                   # Client WebSocket telemetry synchronizer
│   └── style.css                # Interface styling & HUD themes
├── Tools/
│   └── GodsEyeView/             # 3D Cesium.js geospatial situational map
├── tests/                       # Comprehensive automated test suite
│   ├── bench_endpoints.py       # Latency and throughput benchmarks
│   ├── check_routes.py          # FastAPI endpoint validation
│   ├── frontend_audit.py        # DOM and WebSocket verification
│   └── verify_demo.py           # Verification script for presentation scenarios
├── docs/                        # Architectural documentation & engineering journals
│   ├── journal.md               # Development trajectory & design rationale
│   └── learning_journal.md      # Performance optimizations and benchmark logs
├── Main.py                      # Core local loop runner
├── supervisor.py                # Industrial process supervisor with health restarts
├── requirements.txt             # Production dependencies
├── .env.example                 # Environment configuration template
└── .gitignore                   # Scalable repository exclusion rules
```

---

## ⚡ Key Architectural Capabilities

### 1. Zero-Mock Real Telemetry Guarantee
Every metric streamed to the frontends originates from genuine hardware or live public feeds:
- **System Metrics**: Real CPU, RAM, GPU, and network throughput via `psutil` and `nvidia-smi`.
- **Media Tracking**: Real Windows Session Manager (`GlobalSystemMediaTransportControlsSessionManager`) and Spotify API.
- **Crypto & Financials**: Live Binance depth/ticker orderbooks and Yahoo Finance.
- **Geospatial & Space**: Live ISS coordinates from `wheretheiss.at` and real natural hazards from NASA EONET.
- **Smart Hardware**: Direct local UDP/KLAP communication to physical plugs. Never simulates numbers if hardware is disconnected.

### 2. Dual-Engine Intent Resolution
- **Tier 1 (Sub-Millisecond)**: Regex pre-parser executes device toggles, volume changes, and core controls in under $1.5\text{ ms}$.
- **Tier 2 (Cognitive LLM)**: Deep queries and open-domain conversations route to Groq's `llama-3.3-70b-versatile` with bilingual English and Urdu understanding.

### 3. Industrial Process Supervisor
Running `python supervisor.py` spawns and monitors both the FastAPI backend (port 8000) and the 3D God's Eye View (port 5173). If any component degrades or crashes, the supervisor automatically performs state cleanup and instant recovery.

---

## 🚀 Quickstart & Installation

```bash
# 1. Clone repository
git clone https://github.com/AreebIqbal6/J.A.R.V.I.Sv.git
cd J.A.R.V.I.Sv

# 2. Set up virtual environment
python -m venv .venv
.\.venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env

# 5. Launch via Supervisor
python supervisor.py
```

Access the systems:
- **Core Tactical HUD**: `http://127.0.0.1:8000`
- **3D God's Eye View**: `http://127.0.0.1:5173`

---

## 🧪 Verification & Testing

```bash
python tests/check_routes.py
python tests/bench_endpoints.py
```

---

## 🛡️ License

MIT License. Designed with precision for autonomous industrial intelligence.
