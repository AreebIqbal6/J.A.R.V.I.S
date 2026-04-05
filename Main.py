import os
import sys
import json
import threading
import asyncio
import warnings
import struct
import pyaudio
import pvporcupine
import requests
from time import sleep
from dotenv import load_dotenv, dotenv_values

# ==========================================
# --- THE WINERROR 1114 BYPASS ---
import torch
import torchaudio
# ==========================================

# THE NUCLEAR WARNINGS FILTER
warnings.filterwarnings("ignore")
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"

load_dotenv()
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Jarvis")
PICOVOICE_KEY = env_vars.get("PICOVOICE_API_KEY")

if not PICOVOICE_KEY:
    print("\n!! CRITICAL ERROR: Picovoice API Key missing in .env file.")
    print("!! Please add PICOVOICE_API_KEY=your_key_here to .env to enable the wake-word engine.\n")
    sys.exit()

try:
    from Frontend.GUI import (
        GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen,
        TempDirectoryPath, SetMicrophoneStatus, AnswerModifier,
        QueryModifier, GetMicrophoneStatus, GetAssistantStatus
    )
    from Backend.Model import FirstLayerDMM, funcs
    from Backend.RealtimeSearchEngine import RealtimeSearchEngine
    from Backend.Automation import Automation
    from Backend.SpeechToText import SpeechRecognition
    from Backend.Chatbot import ChatBot
    from Backend.TextToSpeech import TextToSpeech
    from Backend.Vision import VisionAnalysis, TakeScreenshot, CaptureWebcam
except ImportError as e:
    print(f"!! Import Error: {e}")
    sys.exit()

# --- EXECUTIVE SUITE IMPORTS ---
try:
    from Backend.Workspace import CreatePresentation, CreateExcel, CreateDatabase
    from Backend.LocalCoder import GenerateLocalCode, EngageOpenClaw
    from Backend.Sandbox import PythonSandbox
    sandbox = PythonSandbox()
except Exception as e:
    print(f"!! Executive Suite Offline: {e}")
    sandbox = None

# --- PHASE 4: BIOMETRIC IMPORTS ---
try:
    from Backend.VoiceAuth import VoiceAuthenticator
    voice_vault = VoiceAuthenticator()
except Exception as e:
    voice_vault = None
    print(f"!! Voice Vault Error: {e}")

# --- F1 TELEMETRY IMPORT ---
try:
    from Backend.F1_Engineer import RaceEngineer
    pit_wall = RaceEngineer()
except Exception as e:
    pit_wall = None
    print(f"!! F1 Module Offline: {e}")

# --- QUANTITATIVE BROKER IMPORT ---
try:
    from Backend.Quant_Broker import QuantBroker
    quant_desk = QuantBroker()
except Exception as e:
    quant_desk = None
    print(f"!! Quant Module Offline: {e}")

# --- SMART HOME IMPORTS ---
try:
    from Backend.SmartTV import ControlTV
except Exception as e:
    print(f"!! Smart Home Offline: {e}")
    ControlTV = None

FEMALE_VIPS = ["Fariya", "Rija", "Fabha", "Yusma", "Farah"]

# ==========================================
# --- BACKGROUND SENTRY (SPOTIFY, PHONE, EMAIL) ---
# ==========================================
def run_sentry_loop():
    """This runs parallel to the Wake Word. It monitors your digital environment."""
    print(">> [SENTRY]: Proactive background monitoring online.")
    try:
        from Backend.NervousSystem import SentryNerves
        nerves = SentryNerves()
    except Exception as e:
        print(f"!! Sentry Init Error: {e}")
        return

    while True:
        # 1. Check Spotify
        music_update = nerves.check_spotify()
        if music_update:
            print(f">> [SENTRY]: {music_update}")
            ShowTextToScreen(f"{Assistantname} : {music_update}")
            TextToSpeech(music_update)

        # 2. Check Phone
        phone_update = nerves.check_phone_notifications()
        if phone_update:
            print(f">> [SENTRY]: {phone_update}")
            ShowTextToScreen(f"{Assistantname} : {phone_update}")
            TextToSpeech(phone_update)
            
        # 3. Check Emails
        try:
            from Backend.EmailReader import CheckNewEmails
            email_update = CheckNewEmails()
            if email_update:
                print(f">> [SENTRY]: {email_update}")
                ShowTextToScreen(f"{Assistantname} : {email_update}")
                TextToSpeech(email_update)
        except Exception:
            pass

        sleep(10) # Loop every 10 seconds to avoid API rate limits

# ==========================================
# --- SYSTEM UTILITIES ---
# ==========================================
def ShowDefaultChatIfNoChats():
    if not os.path.exists("Data"): 
        os.makedirs("Data")
    chat_log_path = os.path.join("Data", "ChatLog.json")
    if not os.path.exists(chat_log_path):
        with open(chat_log_path, 'w', encoding='utf-8') as f: 
            json.dump([], f)

def ChatLogIntegration():
    try:
        if not os.path.exists(os.path.join("Data", "ChatLog.json")): 
            return
        with open(os.path.join("Data", "ChatLog.json"), 'r', encoding='utf-8') as f:
            data = json.load(f)
        formatted = ""
        if data and isinstance(data, list):
            for e in data:
                role = Username if e["role"] == "user" else Assistantname
                formatted += f"{role}: {e['content']}\n"
        
        db_path = TempDirectoryPath('Database.data')
        with open(db_path, 'w', encoding='utf-8') as f:
            f.write(AnswerModifier(formatted))
    except Exception:
        pass

async def ExecuteAutomation(commands):
    results = []
    async for res in Automation(commands):
        results.append(res)
    return results

# ==========================================
# --- THE MAIN AI BRAIN (EXECUTED ON WAKE) ---
# ==========================================
def MainExecution():
    SetAssistantStatus("Listening...")
    print(f"\n>> [{Assistantname.upper()}]: Listening for command...")
    
    Query = SpeechRecognition()
    
    if not Query or Query.strip() == "":
        SetAssistantStatus("Available...")
        print(f">> [{Assistantname.upper()}]: No command detected. Returning to sleep.")
        return 
    
    speaker_identity = "Unknown"
    salutation = "sir" 
    
    if voice_vault:
        speaker_identity, score = voice_vault.identify_speaker_from_temp_file()
        if speaker_identity in FEMALE_VIPS:
            salutation = "ma'am"
        elif speaker_identity == "Unknown":
            salutation = "sir" 
            
        print(f">> [BIOMETRICS]: Identity: {speaker_identity} (Confidence: {score:.2f})")
    
    ShowTextToScreen(f"{speaker_identity} ({salutation.title()}) : {Query}")
    SetAssistantStatus("Responding...")
    
    identity_context = f"[IDENTITY: {speaker_identity} | ADDRESS_AS: {salutation}] "
    processing_query = identity_context + Query

    try:
        Decision = FirstLayerDMM(Query) 
        print(f"\n>> Intent Detected : {Decision}\n")

        for q in Decision:
            if "generate " in q:
                file_path = os.path.join("Frontend", "Files", "ImageGeneration.data")
                os.makedirs(os.path.dirname(file_path), exist_ok=True)
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(f"{q},True")
                ShowTextToScreen(f"{Assistantname} : Initiating image generation...")
                TextToSpeech(f"Generating image, {salutation}.")

        for q in Decision:
            if "vision" in q:
                ans = ""
                if "screenshot" in q:
                    ShowTextToScreen(f"{Assistantname} : Analyzing screen...")
                    img = TakeScreenshot()
                    ans = VisionAnalysis(img)
                elif "camera" in q or "what is in front of you" in Query.lower():
                    ShowTextToScreen(f"{Assistantname} : Accessing camera...")
                    img = CaptureWebcam()
                    ans = VisionAnalysis(img) if img else "Camera unavailable."
                
                if ans:
                    ShowTextToScreen(f"{Assistantname} : {ans}")
                    TextToSpeech(ans)

        excluded = ["general", "realtime", "generate image", "vision screenshot", "vision camera", "exit", "sentry", "f1", "quant", "memory", "presentation", "excel", "database", "code", "tv", "nasa"]
        auto_queries = [q for q in Decision if any(q.startswith(f) for f in funcs if f not in excluded)]
        
        if any("sentry" in d for d in Decision):
            auto_queries.append("sentry")

        # ==============================================================
        # --- HOTFIX: HARD ROUTER OVERRIDES ---
        # ==============================================================
        q_lower = Query.lower()
        
        # 1. SMART TV OVERRIDE
        if "tv" in q_lower or "television" in q_lower:
            Decision = [d for d in Decision if not d.startswith("exit")]
            auto_queries = []

        # 2. NASA EONET OVERRIDE
        elif any(word in q_lower for word in ["nasa", "wildfire", "volcano", "hurricane", "natural disaster", "global event"]):
            auto_queries = []

        # 3. FILE AUTOMATION OVERRIDE
        elif any(word in q_lower for word in ["write ", "create folder ", "delete "]):
            print(">> [ROUTER OVERRIDE]: Intercepting file request. Bypassing Vocal Agent.")
            
            if speaker_identity == "Unknown":
                denial_msg = "I'm sorry, but biometric authentication is required to modify system files."
                ShowTextToScreen(f"{Assistantname} : {denial_msg}")
                TextToSpeech(denial_msg)
                Decision = [] 
            else:
                Decision = [d for d in Decision if not d.startswith("general") and not d.startswith("realtime")]
                
                clean_cmd = q_lower.replace("jarvis", "").replace(",", "").strip()
                if "write " in clean_cmd:
                    auto_queries.append(clean_cmd[clean_cmd.find("write "):])
                elif "create folder " in clean_cmd:
                    auto_queries.append(clean_cmd[clean_cmd.find("create folder "):])
                elif "delete " in clean_cmd:
                    auto_queries.append(clean_cmd[clean_cmd.find("delete "):])
        # ==============================================================

        if auto_queries:
            res_list = asyncio.run(ExecuteAutomation(auto_queries))
            for r in res_list:
                if r and isinstance(r, str):
                    dynamic_response = r.replace("sir.", f"{salutation}.").replace(" sir", f" {salutation}")
                    ShowTextToScreen(f"{Assistantname} : {dynamic_response}")
                    TextToSpeech(dynamic_response)

        processing_query_for_agent = Query
        for tag in ["general ", "realtime ", "automation ", "f1 ", "quant ", "memory ", "presentation ", "excel ", "database ", "code ", "tv ", "nasa "]:
            processing_query_for_agent = processing_query_for_agent.lower().replace(tag, "")
        
        processing_query_for_agent = identity_context + processing_query_for_agent

        # ==============================================================
        # --- PHASE 5: EXECUTIVE SUITE, LOCAL CODER & SMART HOME ---
        # ==============================================================
        if any(i.startswith("presentation") for i in Decision):
            ShowTextToScreen(f"{Assistantname} : Drafting presentation...")
            TextToSpeech(f"Drafting slides now, {salutation}.")
            ans = CreatePresentation(Query)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)

        elif any(i.startswith("excel") for i in Decision):
            ShowTextToScreen(f"{Assistantname} : Compiling spreadsheet...")
            TextToSpeech(f"Compiling data sheet, {salutation}.")
            ans = CreateExcel(Query)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)

        elif any(i.startswith("database") for i in Decision):
            ShowTextToScreen(f"{Assistantname} : Architecting database schema...")
            TextToSpeech(f"Building relational database, {salutation}.")
            ans = CreateDatabase(Query)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)

        elif any(i.startswith("code") for i in Decision):
            ShowTextToScreen(f"{Assistantname} : Engaging Cloud Compiler...")
            TextToSpeech(f"Writing script via Groq, {salutation}.")
            ans = GenerateLocalCode(Query)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)
            
            if "SUCCESS" in ans.upper() and sandbox:
                with open(os.path.join("Workspace", "Code", "jarvis_script.py"), "r") as f:
                    code_content = f.read()
                exec_result = sandbox.execute(code_content)
                ShowTextToScreen(f"{Assistantname} : Script Output -> {exec_result}")

        elif any(i.startswith("agent") for i in Decision):
            ShowTextToScreen(f"{Assistantname} : Deploying OpenClaw agent to the codebase...")
            TextToSpeech(f"Deploying Open Claw sub-agent, {salutation}.")
            ans = EngageOpenClaw(processing_query_for_agent)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)

        elif any(i.startswith("tv") for i in Decision) or "tv" in Query.lower() or "television" in Query.lower():
            if ControlTV:
                ShowTextToScreen(f"{Assistantname} : Accessing local network...")
                TextToSpeech(f"Sending command to the television, {salutation}.")
                ans = ControlTV(Query)
            else:
                ans = f"The Smart TV module is currently offline, {salutation}."
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)

        elif any(word in Query.lower() for word in ["nasa", "wildfire", "volcano", "hurricane", "natural disaster", "global event"]):
            ShowTextToScreen(f"{Assistantname} : Connecting to NASA Earth Observatory...")
            TextToSpeech(f"Establishing uplink to NASA satellite telemetry, {salutation}.")
            
            try:
                from Backend.EarthTracker import GetEarthEvents
                ans = GetEarthEvents(Query)
            except Exception as e:
                ans = f"Earth Tracker module offline. {e}"
                
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)

        elif any(i.startswith("realtime") for i in Decision):
            ans = RealtimeSearchEngine(processing_query_for_agent)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)
            
        elif any(i.startswith("f1") for i in Decision):
            ShowTextToScreen(f"{Assistantname} : Accessing FIA telemetry databases...")
            TextToSpeech(f"Accessing pit wall telemetry, {salutation}.")
            if pit_wall:
                ans = pit_wall.process_query(Query)
            else:
                ans = f"I'm sorry {salutation}, the F1 module is currently offline."
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)
            
        elif any(i.startswith("quant") for i in Decision):
            ShowTextToScreen(f"{Assistantname} : Accessing Wall Street terminal...")
            TextToSpeech(f"Accessing market data, {salutation}.")
            if quant_desk:
                ans = quant_desk.process_query(Query)
            else:
                ans = f"I'm sorry {salutation}, the financial module is currently offline."
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)
            
        elif any(i.startswith("memory") for i in Decision) or any(phrase in Query.lower() for phrase in ["remember that", "what do you remember", "forget that", "wipe memory"]):
            from Backend.Memory import Remember, Recall, Forget 
            if "remember" in Query.lower():
                ans = Remember(Query)
            elif "forget" in Query.lower():
                ans = Forget(Query)
            else:
                ans = Recall(Query)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)
            
        elif any(i.startswith("general") for i in Decision):
            ans = ChatBot(processing_query)
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)

        if any("exit" in d for d in Decision):
            SetAssistantStatus("Unavailable...")
            ans = f"Shutting down systems. Goodbye, {salutation}."
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)
            sleep(2)
            os._exit(0)

    except Exception as e:
        print(f"!! Main Logic Error: {e}")
    
    Query = "" 
    sleep(0.5) 
    ChatLogIntegration()
    SetAssistantStatus("Available...")

# ==========================================
# --- THE WAKE WORD ENGINE (EARS) ---
# ==========================================
def wake_word_listener():
    """Listens offline, using 0% CPU, until it hears 'Jarvis' or UI Mic is clicked."""
    try:
        porcupine = pvporcupine.create(
            access_key=PICOVOICE_KEY,
            keywords=['jarvis']
        )
        
        pa = pyaudio.PyAudio()
        audio_stream = pa.open(
            rate=porcupine.sample_rate,
            channels=1,
            format=pyaudio.paInt16,
            input=True,
            frames_per_buffer=porcupine.frame_length
        )
        
        print(f">> [AUDIO]: Wake word engine online. Say 'Jarvis' to activate.")
        SetAssistantStatus("Available...")
        
        CLAP_THRESHOLD = 8000  # Adjust if it's too sensitive or not sensitive enough
        
        while True:
            if GetMicrophoneStatus() == "True":
                SetMicrophoneStatus("False")
                MainExecution()
                continue
                
            pcm = audio_stream.read(porcupine.frame_length, exception_on_overflow=False)
            audio_data = struct.unpack_from("h" * porcupine.frame_length, pcm)
            
            # --- THE SNAP & CLAP INTERRUPTER ---
            peak = max(abs(x) for x in audio_data) # Native Python, flawless math
            
            if peak > CLAP_THRESHOLD:
                try:
                    import pygame
                    if pygame.mixer.get_init():
                        if pygame.mixer.music.get_busy() or pygame.mixer.get_busy():
                            print(f"\n>> [INTERRUPT]: Snap/Clap detected (Peak Volume: {peak}). Silencing!")
                            pygame.mixer.music.stop() 
                            pygame.mixer.stop()       
                except Exception:
                    pass
            
            keyword_index = porcupine.process(audio_data)
            
            if keyword_index >= 0:
                MainExecution()
                
    except Exception as e:
        print(f"!! Wake Word Error: {e}")
    finally:
        if 'audio_stream' in locals():
            audio_stream.close()
            pa.terminate()
        if 'porcupine' in locals():
            porcupine.delete()

def LaunchCloudServices():
    try:
        sleep(5) 
        import Backend.ImageGeneration
        print(">> Image Generation Service: Monitoring active.")
        Backend.ImageGeneration.ListenForPrompts()
    except Exception as e:
        print(f"!! Cloud Service Error: {e}")

# ==========================================
# --- BOOT SEQUENCE ---
# ==========================================
if __name__ == "__main__":
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    
    t1 = threading.Thread(target=wake_word_listener, daemon=True)
    t2 = threading.Thread(target=LaunchCloudServices, daemon=True)
    t3 = threading.Thread(target=run_sentry_loop, daemon=True)
    
    try:
        from Backend.VisionSentry import StartGestureSentry
        t4 = threading.Thread(target=StartGestureSentry, daemon=True)
        t4_ready = True
    except ImportError as e:
        print(f"!! [VISION SENTRY]: Module missing or import error: {e}")
        t4_ready = False

    t1.start()
    t2.start()
    t3.start()
    if t4_ready:
        t4.start()

    print(">> GUI: Launching...")
    GraphicalUserInterface()