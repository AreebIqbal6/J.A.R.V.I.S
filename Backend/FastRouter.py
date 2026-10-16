import os
import re
import datetime
import psutil
from typing import Optional, Tuple, Dict, Any

class FastRouter:
    """Deterministic local intent router for zero-LLM fast-path commands.
    Executes in < 1ms with 0 API calls for high-frequency commands.
    """
    
    @staticmethod
    def match(query: str) -> Optional[Tuple[str, str, Dict[str, Any]]]:
        """Returns (intent_type, direct_spoken_response, event_payload) or None if requires LLM."""
        if not query:
            return None
        q = query.lower().strip()
        # Clean acronym periods (j.a.r.v.i.s. -> jarvis) and common misheard wake words
        q_norm = re.sub(r'\bj\.?a\.?r\.?v\.?i\.?s\.?\b', 'jarvis', q)
        q_norm = re.sub(r'\b(harvest|starves|travis|jairus|ravish)\b', 'jarvis', q_norm)
        q_norm = re.sub(r'jarvis\.', 'jarvis', q_norm).strip('.,?! ')
        
        # 0. WAKE WORD FAST PATH (<1ms, 0 API calls)
        wake_triggers = [
            "jarvis", "hey jarvis", "hello jarvis", "hi jarvis",
            "wake up", "wake up jarvis", "are you there", "are you there jarvis",
            "you there jarvis", "you there", "listen jarvis"
        ]
        if q_norm in wake_triggers:
            wake_options = [
                "Yes, sir?",
                "At your service, sir.",
                "Standing by, sir.",
                "Online and ready, sir."
            ]
            import random
            return ("wake", random.choice(wake_options), {"action": "wake"})

        # Clean leading jarvis or greetings for intent matching
        q_clean = re.sub(r'^(jarvis|hey jarvis|hello jarvis|hi jarvis|please jarvis)[,\s]*', '', q_norm).strip('.,?! ')
        if not q_clean or q_clean in wake_triggers:
            return ("wake", "Yes, sir?", {"action": "wake"})

        # 0b. PLEASANTRIES, CAPABILITIES & STATUS (<1ms)
        if any(p == q_clean for p in ["thank you", "thanks", "thank you jarvis", "thanks jarvis"]):
            return ("pleasantry", "Always a pleasure, sir.", {"action": "pleasantry"})

        if any(p == q_clean for p in ["how are you", "how are you doing", "how are you jarvis"]):
            return ("status", "Operating at peak efficiency, sir. How may I assist you?", {"action": "status"})

        if any(p in q_clean for p in ["what can you do", "what are your capabilities", "what can you perform", "help me", "what do you do"]):
            return ("capabilities", "I manage your smart home devices, deploy coding agents, monitor system telemetry, and automate your workflow, sir. What is our objective?", {"action": "help"})

        if any(p in q_clean for p in ["who are you", "what are you"]):
            return ("identity", "I am JARVIS, your personal artificial intelligence, sir.", {"action": "identity"})
        
        # 1. TIME & DATE
        if any(p in q_clean for p in ["what time is it", "current time", "tell me the time", "what's the time"]):
            now = datetime.datetime.now().strftime("%I:%M %p")
            return ("time", f"It is currently {now}, sir.", {"time": now})
            
        if any(p in q_clean for p in ["what is the date", "what's the date", "what day is today", "what day is it", "today's date"]):
            today = datetime.datetime.now().strftime("%A, %B %d, %Y")
            return ("date", f"Today is {today}, sir.", {"date": today})

        # 2. SMART HOME / HARDWARE LIGHTS & PLUG
        if any(p in q_clean for p in ["turn on the lights", "turn on the light", "turn on the plug", "turn on smart plug", "lights on", "it is too dark in here", "it's too dark", "too dark here"]):
            return ("hardware", "Illuminating the room now, sir.", {"tool": "smart_plug", "state": "on"})

        if any(p in q_clean for p in ["turn off the lights", "turn off the light", "turn off the plug", "turn off smart plug", "lights off"]):
            return ("hardware", "Power to the lights has been disengaged, sir.", {"tool": "smart_plug", "state": "off"})

        # 3. THERMOSTAT FAST PATH
        thermo_match = re.search(r'(?:set\s+the\s+)?thermostat\s+(?:to\s+)?(\d+)', q_clean)
        if thermo_match:
            deg = thermo_match.group(1)
            return ("thermostat", f"Thermostat adjusted to {deg} degrees, sir.", {"thermostat": int(deg)})

        # 4. SYSTEM DIAGNOSTICS
        if any(p in q_clean for p in ["cpu usage", "what is my cpu usage", "what is my cpu temp", "system diagnostics", "system stats", "ram usage"]):
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            return ("diagnostics", f"CPU load is at {cpu} percent, and memory utilization is at {ram} percent, sir.", {"cpu": cpu, "ram": ram})

        # 5. MEDIA CONTROLS & YOUTUBE
        if "play " in q_clean and ("youtube" in q_clean or "song" in q_clean or "music" in q_clean or "on youtube" in q_clean):
            song = q_clean.replace("play ", "").replace("on youtube", "").replace("youtube", "").strip()
            return ("media_play", f"Playing {song} on YouTube, sir.", {"action": "play", "query": song})

        if any(p in q_clean for p in ["pause music", "stop music", "pause playback"]):
            return ("media_pause", "Pausing media playback, sir.", {"action": "pause"})

        if any(p in q_clean for p in ["resume music", "continue music", "resume playback"]):
            return ("media_resume", "Resuming playback, sir.", {"action": "resume"})

        # 6. UI WIDGET NAVIGATION (setMode in UI)
        ui_widget_map = {
            "chat": ["open chat", "show chat", "open messages"],
            "camera": ["open camera", "show camera", "activate visual sensors", "optical feed"],
            "music": ["open music", "show music", "open media"],
            "diag": ["open diagnostics", "show diagnostics", "open diag", "show specs"],
            "home": ["open smart home", "show smart home", "open home"],
            "security": ["open security", "show security", "open security log"],
            "godseye": ["open gods eye", "show gods eye", "launch gods eye", "gods eye view", "spy satellite", "track flights and ships", "track aircraft", "orbital intelligence", "tactical overview"],
            "earth": ["open earth tracker", "show earth tracker", "open satellite", "satellite telemetry", "show natural disasters from nasa"],
            "coder": ["open terminal", "open code terminal", "open coder"],
            "data": ["open f1", "show f1 telemetry", "open telemetry", "open pit wall"]
        }
        for widget, triggers in ui_widget_map.items():
            if any(t in q_clean for t in triggers):
                if widget == "godseye":
                    try:
                        from Backend.GodsEyeManager import ensure_godseye_running
                        ensure_godseye_running()
                    except Exception:
                        pass
                return ("ui_open", f"Surfacing the {widget} module, sir.", {"widget": widget})

        # 7. JOKES
        if any(p in q_clean for p in ["tell me a joke", "say a joke", "make me laugh"]):
            jokes = [
                "I told my computer I needed a break, and now it refuses to send me notifications, sir.",
                "Why do programmers prefer dark mode? Because light attracts bugs, sir.",
                "There are 10 types of people in the world: those who understand binary, and those who do not, sir."
            ]
            import random
            selected = random.choice(jokes)
            return ("joke", selected, {"type": "joke"})

        return None

    route = match
