# 🧠 ANTIGRAVITY HANDOVER PROTOCOL (PROJECT J.A.R.V.I.S. MARK IV)

> **ATTENTION ANTIGRAVITY AGENT:** 
> If you are reading this, you have just been deployed by Areeb to manage, upgrade, or debug this codebase on a new system. Read this journal carefully. It contains the architectural DNA and behavioral directives for Project J.A.R.V.I.S.

## 1. System Architecture
J.A.R.V.I.S. Mark IV is a unified, fully local AI Assistant designed to run on Windows as a native desktop application. 

- **The Nervous System:** `Backend/Server.py` runs a FastAPI web server. It handles HTTP routes and primary WebSockets (`/ws` for chat/telemetry, `/pty` for embedded terminals).
- **The Brain:** `Backend/Chatbot.py` handles the LLM logic, routing intents, and function calling.
- **The Hands (Automation):** `Backend/Automation.py` contains all the physical tools JARVIS can use (opening apps, creating files, searching for torrents).
- **The HUD (Frontend):** `index.html` is a highly customized, futuristic dashboard. **Rule #1: Never destroy the CSS structural layout.**
- **The Native Wrapper:** `JarvisApp.py` (compiled to `.exe` via PyInstaller) uses `pywebview` to render `index.html` in a borderless, fullscreen, hardware-accelerated desktop window, silently running the FastAPI server in the background.

## 2. Advanced Integrations (Mark IV)
- **God's Eye View:** A CesiumJS local server (`Tools/GodsEyeView`) running on port 5173, injected into the JARVIS HUD via `iframe`. Activated when the user says "Tactical Overview".
- **Hybrid Streaming (MovieBox & PirateBay):** When instructed to play a movie, JARVIS attempts **Option B** first (querying the PirateBay API and routing the magnet directly to VLC via `webtorrent-cli`). If it fails, he falls back to **Option A** (a headless `moviebox-tui` Rust executable embedded into the HUD via `pywinpty` and `xterm.js`, where a JavaScript macro acts as a "Ghost Typist" to search for the movie).
- **Sentry Mode:** Background loops actively monitor Spotify and Emails, pushing telemetry payloads to the frontend WebSocket.
- **Smart Home:** Integrated with Dawlance Android TVs (via ADB) and Tuya Smart Plugs (via `tuya-local`).

## 3. The User (Areeb)
- **Personality Directives:** J.A.R.V.I.S. must communicate with Areeb using a witty, highly competent, slightly sarcastic, and formal British tone (exactly like Paul Bettany's JARVIS from the MCU). 
- **Security:** Do not upload `.env` keys raw. We encrypt them into `jarvis_migration.aes` using `pyAesCrypt` (password: `areeb`).

## 4. Current State & Next Steps
- The system is incredibly stable.
- If you need to make changes to the frontend, modify `index.html` cautiously and use the WebSocket loop (`ws.onmessage`) to trigger UI state changes.
- If you need to add new capabilities, define them in `Backend/Automation.py` and register them in `Backend/Chatbot.py`.

Good luck, Agent. Ensure the Mark IV legacy remains flawless.
