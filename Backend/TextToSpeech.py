import pygame 
import random 
import asyncio 
import edge_tts 
import os 
import re
import pyttsx3 
from time import sleep 
from dotenv import dotenv_values 

# Load environment variables
env_vars = dotenv_values(".env")
AssistantVoice = env_vars.get("AssistantVoice", "en-GB-RyanNeural") 
UrduVoice = "ur-PK-AsadNeural" 

# --- FIX 1: ABSOLUTE PATHING ---
AUDIO_PATH = os.path.abspath(os.path.join(os.getcwd(), "Data", "speech.mp3"))
os.makedirs(os.path.dirname(AUDIO_PATH), exist_ok=True)

# --- URDU SCRIPT DETECTION ---
def contains_urdu(text):
    return bool(re.search(r'[\u0600-\u06FF]', text))

# --- OFFLINE FALLBACK ENGINE ---
def SpeakOffline(Text):
    print(">> [TTS DEBUG]: Using Offline Fallback (pyttsx3)...")
    try:
        engine = pyttsx3.init()
        voices = engine.getProperty('voices')
        engine.setProperty('voice', voices[0].id) 
        engine.setProperty('rate', 170) 
        engine.say(Text)
        engine.runAndWait()
    except Exception as e:
        print(f"!! Offline TTS also failed: {e}")

try:
    # --- FIX 2: STRICT AUDIO PARAMETERS ---
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=4096)
except Exception as e:
    print(f"!! Pygame Mixer Init Error: {e}")

async def TextToAudioFile(text) -> bool:
    if os.path.exists(AUDIO_PATH): 
        try: os.remove(AUDIO_PATH) 
        except: pass 

    is_urdu_text = contains_urdu(text)
    current_voice = UrduVoice if is_urdu_text else AssistantVoice
    
    print(f"   [TTS DEBUG] Language: {'Urdu' if is_urdu_text else 'English'} | Voice: {current_voice}")
    
    try:
        communicate = edge_tts.Communicate(text, current_voice)
        await communicate.save(AUDIO_PATH) 
        return True
    except Exception as e:
        print(f"!! Edge TTS Server Error: {e}")
        return False

def TTS(Text, func=lambda: None):
    try:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload()
        except: pass

        success = asyncio.run(TextToAudioFile(Text))

        if not success:
            SpeakOffline(Text)
            return True

        print("   [TTS DEBUG] Playing audio via Pygame...")
        pygame.mixer.music.load(AUDIO_PATH)
        pygame.mixer.music.play() 

        # --- FIX 3: THE RACE CONDITION PATCH ---
        sleep(0.2) 

        while pygame.mixer.music.get_busy():
            if func() == False: 
                pygame.mixer.music.stop()
                break
            sleep(0.1) 

        return True 

    except Exception as e: 
        print(f"!! Error in TTS: {e}")
        SpeakOffline(Text)
    finally:
        try:
            pygame.mixer.music.stop()
            pygame.mixer.music.unload() 
        except: pass

def TextToSpeech(Text, func=lambda r=None: True):
    if not Text: return

    # --- 1. GENERAL CLEANUP ---
    Text = Text.replace("J.A.R.V.I.S.", "Jarvis").replace("<s>", "").replace("</s>", "")
    
    # --- 2. THE PHONETIC DICTIONARY ---
    # Add any names or words the AI mispronounces here
    pronunciation_guide = {
        "عریب": "اریب",       # Fixes the 'Ain to an Alif for a clean "A" sound
        "Fariya": "Fariyah",  # Tweak English spelling for better TTS phonetics if needed
        "Kaaif": "Kaif"       # Fixes friends' names if it mispronounces them
    }
    
    for wrong_spelling, correct_pronunciation in pronunciation_guide.items():
        Text = Text.replace(wrong_spelling, correct_pronunciation)
    
    # --- 3. SPLIT AND PLAY ---
    Data = str(Text).split(".")
    
    if contains_urdu(Text):
        responses = [
            " باقی تفصیلات اسکرین پر موجود ہیں۔",
            " میں نے مکمل تفصیلات پرنٹ کر دی ہیں۔",
            " آپ باقی معلومات چیٹ میں پڑھ سکتے ہیں۔"
        ]
    else:
        responses = [
            " The rest is on the screen.",
            " I've printed the full details for you.",
            " You can read the rest in the chat."
        ]

    if len(Data) > 10 and len(Text) >= 600:
        TTS(". ".join(Data[0:3]) + "." + random.choice(responses), func)
    else: 
        TTS(Text, func)

if __name__ == "__main__":
    print(">> Dual-Accent TTS Engine Online (English/Urdu).")
    while True:
        text_input = input("Enter text: ")
        if text_input.lower() in ['exit', 'quit']:
            break
        TextToSpeech(text_input)