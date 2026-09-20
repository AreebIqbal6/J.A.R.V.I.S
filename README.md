# 🚀 PROJECT J.A.R.V.I.S. MARK IV - DEPLOYMENT GUIDE

Welcome to Project J.A.R.V.I.S. Mark IV. This isn't a basic chatbot you type into on a website. It’s a fully local, Phase 4 Autonomous AI Agent. It can see your screen, write and execute its own Python code, generate PowerPoint presentations, monitor your phone/emails in real-time, hijack Smart TVs over the local network, provide God's Eye View satellite reconnaissance, and natively cast torrent streams to VLC!

Since this runs natively on your actual hardware, you cannot just click an .exe and expect it to work without building the core engine first.

Follow these exact steps, in order. If you skip a step, J.A.R.V.I.S. will not function.

## STEP 1: The Core Engines (Python & Node.js)
J.A.R.V.I.S. is built on a 100% pure-Python architecture, but utilizes Node.js for its Tactical Overview servers.

**1. Install Python:**
- Go to python.org/downloads and download Python 3.11 or 3.12.
- Run the installer.
🚨 **CRITICAL**: At the very bottom of the very first installation screen, you MUST check the box that says "Add python.exe to PATH" before you click Install.

**2. Install Node.js:**
- Go to nodejs.org and download the LTS version.
- Install it with default settings (this gives JARVIS access to `npm` for the web terminals and God's Eye View).

## STEP 2: Install Ollama (The Visual Cortex)
J.A.R.V.I.S. needs this to be able to look at your screen and analyze images locally without sending private data to a server.

Go to ollama.com/download and install it for Windows.
Once installed, open your computer's "Command Prompt" (press the Windows key, type cmd, and hit Enter).
Type this exact command and hit Enter:
`ollama pull moondream`
Let it download 100%. You can close the window when it's done.

## STEP 3: The .env File (The Brain Keys)
J.A.R.V.I.S. needs API keys to communicate with cloud brains (like Groq, Llama 3, and Picovoice), as well as your local IPs to control your hardware.

Inside the main folder, right-click and create a new Text Document. Name it exactly `.env` (ensure Windows doesn't save it as `.env.txt`).

Paste this exact block into it and insert your keys. DO NOT put spaces before or after the `=` sign!

```plaintext
Username=User
Assistantname=J.A.R.V.I.S
InputLanguage=en
AssistantVoice=en-GB-RyanNeural

# --- CORE KEYS (REQUIRED) ---
GroqAPIKey=your_key_here
CohereAPIKey=your_key_here
BytezAPIKey=your_key_here
HuggingFaceAPIKey=your_key_here
OpenAI_API_Key=your_key_here
PICOVOICE_API_KEY=your_key_here
PUSHBULLET_API_KEY=your_key_here

# --- OPTIONAL / BACKUP KEYS ---
GeminiAPIKey=your_key_here
PollinationsAPIKey=your_key_here
WolframAPIKey=your_key_here
WeatherAPIKey=your_key_here
NewsAPIKey=your_key_here

# --- SENTRY MODE APIS ---
SPOTIFY_CLIENT_ID=your_id_here
SPOTIFY_CLIENT_SECRET=your_secret_here
SPOTIFY_REDIRECT_URI=http://127.0.0.1:8080/

EMAIL_USER=your_email@gmail.com
EMAIL_PASS=your_16_letter_app_password

# --- SMART HOME INTERFACES ---
# Dawlance/Android TV (Enable USB/ADB Debugging)
TV_IP=192.168.1.XX
# Tuya Smart Plug Settings
TUYA_DEVICE_ID=your_device_id
TUYA_LOCAL_KEY=your_local_key
TUYA_IP=192.168.1.XX
```
Save the file and close it.

## STEP 4: Launching Sequence
There are now two ways to wake J.A.R.V.I.S.:

**Method A (Standard Server Mode):**
Double-click `Setup_JARVIS.bat` (or `start.bat`). It will build the virtual environment and install packages. Then open `http://localhost:8000` in your browser.

**Method B (Native Desktop App - Mark IV Exclusive):**
If you want JARVIS to feel like a real standalone desktop application, go to `dist/` and double-click `JarvisApp.exe`. It will boot the FastAPI server silently in the background and launch a sleek, borderless native application window directly to the HUD!

## STEP 5: Mark IV Capabilities
Once the interface says "Available", you can talk to him or type.

**The Executive Suite:**
- "Jarvis, make a presentation about the future of Solar Energy."
- "Jarvis, architect an SQLite database for a fast food restaurant menu."

**The Coder:**
- "Jarvis, write a Python script to calculate the cost of buying 1 liter of oil..." *(He executes scripts instantly in his sandbox).*

**The Sentry (Background Monitoring):**
- He monitors WhatsApp, Spotify, and Emails silently and announces them out loud.

**Tactical & Entertainment (MARK IV NEW):**
- **"Jarvis, activate Tactical Overview."** *(He embeds the fully 3D God's Eye View map directly into the HUD).*
- **"Jarvis, play Inception."** *(He silently scrapes PirateBay and boots VLC Player via WebTorrent. If no stream is found, he falls back to the embedded MovieBox-TUI in the HUD and types your search query automatically!)*

**Smart Home & Environmental Awareness:**
- "Jarvis, turn the TV off." *(Dawlance TV via ADB)*
- "Jarvis, turn off the smart plug." *(Tuya Local integration)*
- "Look at my screen and tell me what you see." *(Local Vision via Ollama)*

**The Interrupter:**
- If he is talking too much, just Clap your hands loudly near the microphone to silence him.
