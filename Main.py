import os
import sys
import threading
import struct
from time import sleep
from dotenv import load_dotenv, dotenv_values

os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
load_dotenv()
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Jarvis")

from Frontend.GUI import (
    GraphicalUserInterface, SetAssistantStatus, ShowTextToScreen,
    SetMicrophoneStatus, GetMicrophoneStatus
)
from Backend.SpeechToText import SpeechRecognition
from Backend.TextToSpeech import TextToSpeech
from Backend.core import process_intent
import json

def ShowDefaultChatIfNoChats():
    if not os.path.exists("Data"): 
        os.makedirs("Data")
    chat_log_path = "ChatLog.json"
    if not os.path.exists(chat_log_path):
        with open(chat_log_path, 'w', encoding='utf-8') as f: 
            json.dump([], f)

from Frontend.GUI import AnswerModifier, TempDirectoryPath

def ChatLogIntegration():
    try:
        if not os.path.exists("ChatLog.json"): 
            return
        with open("ChatLog.json", 'r', encoding='utf-8') as f:
            data = json.load(f)
        formatted = ""
        if data and isinstance(data, list):
            for e in data:
                role = Username if e.get("role") == "user" else Assistantname
                formatted += f"{role}: {e.get('content', '')}\\n"
        
        db_path = TempDirectoryPath('Database.data')
        with open(db_path, 'w', encoding='utf-8') as f:
            f.write(AnswerModifier(formatted))
    except Exception as e:
        print(f"ChatLogIntegration Error: {e}")


def MainExecution(Query=None):
    SetAssistantStatus("Listening...")
    if not Query:
        print(f"\n>> [{Assistantname.upper()}]: Listening for command...")
        Query = SpeechRecognition()
    
    if not Query or Query.strip() == "":
        SetAssistantStatus("Available...")
        return 
        
    print(f">> [USER]: {Query}")
    ShowTextToScreen(f"{Username} : {Query}")
    SetAssistantStatus("Responding...")
    
    try:
        if "exit" in Query.lower() or "shut down" in Query.lower():
            SetAssistantStatus("Unavailable...")
            ans = "Shutting down systems. Goodbye, sir."
            ShowTextToScreen(f"{Assistantname} : {ans}")
            TextToSpeech(ans)
            sleep(2)
            os._exit(0)
            
        ans = process_intent(Query)
        ShowTextToScreen(f"{Assistantname} : {ans}")
        TextToSpeech(ans)

    except Exception as e:
        print(f"!! Main Logic Error: {e}")
    
    sleep(0.2) 
    ChatLogIntegration()
    SetAssistantStatus("Available...")

def wake_word_listener():
    print(f">> [AUDIO]: Unified Mic Listener online (voice & UI button).")
    SetAssistantStatus("Available...")
    
    while True:
        try:
            # 1. UI Mic button trigger
            if str(GetMicrophoneStatus()) == "True":
                SetMicrophoneStatus("False")
                MainExecution()
                continue
                
            # 2. Continuous voice detection with half-duplex self-hearing prevention
            from Backend.TextToSpeech import is_speaking
            if not is_speaking():
                Query = SpeechRecognition()
                if Query and Query.strip():
                    MainExecution(Query)
            else:
                sleep(0.1)
        except Exception as e:
            sleep(0.2)

def launch_fastapi():
    try:
        import socket
        import subprocess
        # Check if port 8000 is occupied
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        res = s.connect_ex(('127.0.0.1', 8000))
        s.close()
        if res == 0:
            print(">> [SERVER]: Port 8000 occupied. Clearing lingering socket...")
            subprocess.run(
                'for /f "tokens=5" %a in (\'netstat -aon ^| findstr :8000 ^| findstr LISTENING\') do taskkill /F /PID %a',
                shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            sleep(0.8)

        import uvicorn
        from Backend.Server import app
        print(">> [SERVER]: Starting FastAPI WebSocket & REST on port 8000...")
        uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error")
    except Exception as e:
        print(f"!! [SERVER]: Error starting server: {e}")

if __name__ == "__main__":
    ShowDefaultChatIfNoChats()
    ChatLogIntegration()
    
    t1 = threading.Thread(target=wake_word_listener, daemon=True)
    t5 = threading.Thread(target=launch_fastapi, daemon=True)
    
    t1.start()
    t5.start()

    print(">> GUI: Launching...")
    GraphicalUserInterface()
