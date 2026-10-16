# JARVIS Lite - Learning Journal & Documentation

This document serves as the architectural journal for the JARVIS Lite project. It explains the "whys" and "hows" of the entire system, documenting the design choices, features, and security considerations. This is designed to help explain the project during the university demonstration.

## 1. The "Whys": Architectural Decisions

### Why Groq and Llama-3.3-70b-versatile?
*   **Speed:** Groq's LPU (Language Processing Unit) architecture allows for near-instantaneous inference. For a voice assistant, latency ruins the illusion of intelligence.
*   **Function Calling:** Llama-3.3 natively supports JSON-based tool calling. This eliminates the need for fragile Regex parsing (which was a major weakness in previous builds where the LLM would output `<function/CreateFolder>` and crash the system if it hallucinated a typo).

### Why Whisper-Large-v3 for Speech-to-Text (STT)?
*   **True Bilingualism:** Previous iterations of JARVIS used a hardcoded translator (`mtranslate`) that converted Urdu to English *before* sending it to the brain. This meant the AI never knew the user spoke Urdu. Whisper accurately transcribes Roman Urdu and native Urdu script, passing the cultural context directly to the LLM so it can reply in the same language.

### Why TP-Link Kasa over Tuya for Smart Plugs?
*   **Local Control Reliability:** Tuya requires cloud developer accounts, local keys, and API tokens that frequently expire. TP-Link Kasa plugs (via `python-kasa`) operate entirely locally on the UDP/TCP network. It requires zero cloud authentication, making it bulletproof for a live classroom presentation.

### Why a Minimalist HTML/CSS Frontend?
*   **Focus & Performance:** A heavy React or WebGL frontend consumes CPU threads. By using a lightweight HTML/CSS glowing reactor (Iron Man HUD style) powered by pure CSS animations (avoiding heavy JS libraries unless necessary), the system allocates maximum CPU/RAM to Python's audio listening buffer.

---

## 2. The "Hows": System Features & Workflow

### How the Brain Works (The Loop)
1.  **Listen:** `speech_recognition` listens to the default microphone until silence is detected.
2.  **Transcribe:** The audio byte-data is temporarily saved to a `.wav` file and sent to Groq's Whisper API.
3.  **Process Intent (The Magic):** The text is sent to the LLM alongside a list of `TOOLS` (JSON definitions of what our Python scripts can do).
4.  **Execute Action:** If the LLM determines the user wants to play a song or turn on a light, it returns a `tool_call` instead of standard text. The Python backend intercepts this, runs the corresponding function (`play_music()`, `control_smart_plug()`), and speaks the result out loud.

### Implemented Software Automation
*   **MS Word Application Generator:** Uses `python-docx` to programmatically build a structured `.docx` file based on the user's vocal topic, then executes a shell command to open it natively in Windows.
*   **YouTube Player:** Uses Python's `webbrowser` and `urllib.parse` to safely encode the user's voice query into a URL and launch YouTube directly, avoiding the build errors associated with older scraping libraries.
*   **Screen Capture:** Uses `pyautogui` to grab the current pixel buffer of the monitor, save it via the `Pillow` library, and open the image viewer.
*   **App Launcher:** A mapped dictionary executes direct OS-level shell commands to launch local binaries (Calculator, Notepad).

---

## 3. Security & Vulnerability Considerations

While JARVIS Lite is a local application, it was built with standard security principles in mind to prevent common attack vectors:

*   **Secret Key Leakage:** API Keys (Groq) are strictly isolated using `python-dotenv`. They are loaded from a local `.env` file that is deliberately excluded from version control.
*   **Command Injection (OS / Shell):** The `open_application` tool does not pass raw LLM output into `os.system`. Instead, it uses a hardcoded dictionary map (e.g., `"notepad": "notepad"`). If the LLM hallucinates a malicious command, the dictionary lookup fails, neutralizing the threat.
*   **Replay Attacks & STT Buffering:** The system flushes the audio buffer after every transcription, ensuring that previously recorded audio (or background echoes) doesn't re-trigger commands in an infinite loop.

---
*Documented for University Presentation Defense.*
