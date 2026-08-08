import speech_recognition as sr
import os
import sys
from groq import Groq
from dotenv import dotenv_values, load_dotenv
from mtranslate import translate

# --- ROBUST ENV LOADING ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
env_path = os.path.join(root_dir, ".env")
env_vars = dotenv_values(env_path)

# Initialize Groq Client
api_key = env_vars.get("GroqAPIKey")
if not api_key:
    load_dotenv(env_path)
    api_key = os.getenv("GroqAPIKey")

if not api_key:
    print(f"!! CRITICAL ERROR: GroqAPIKey not found in .env at {env_path}")
    sys.exit(1)

groq_client = Groq(api_key=api_key)

# --- HELPER FUNCTIONS ---
def QueryModifier(Query):
    new_query = Query.lower().strip()
    if not new_query: return ""
    
    # Clean up common misheard wake-words
    corrupted_names = ["harvest", "starves", "travis", "jairus", "ravish", "आवेश", "गार्विस", "west", "वेस्ट"]
    for name in corrupted_names:
        new_query = new_query.replace(name, "jarvis")

    question_words = ["how", "what", "who", "where", "when", "why", "which", "whose", "whom", "can you", "what's", "where's", "how's"]

    if any(word + " " in new_query for word in question_words):
        if new_query[-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "?"
        else:
            new_query += "?"
    else:
        if new_query[-1] in ['.', '?', '!']:
            new_query = new_query[:-1] + "."
        else:
            new_query += "."
    return new_query.capitalize()

def UniversalTranslator(Text):
    try:
        # Translates Urdu/Hindi/Devanagari directly into English for the Router
        return translate(Text, "en", "auto").capitalize()
    except:
        return Text

def SetAssistantStatus(Status):
    try:
        status_path = os.path.join(root_dir, "Frontend", "Files", "Status.data")
        os.makedirs(os.path.dirname(status_path), exist_ok=True)
        with open(status_path, "w", encoding='utf-8') as file:
            file.write(Status)
    except:
        pass

def SelectMicrophone():
    settings_file = os.path.join(root_dir, "Data", "MicIndex.txt")
    if os.path.exists(settings_file):
        try:
            with open(settings_file, "r") as f:
                return int(f.read().strip())
        except:
            pass 
    return None

# --- MAIN SPEECH RECOGNITION ---
def SpeechRecognition():
    recognizer = sr.Recognizer()
    recognizer.dynamic_energy_threshold = True 
    recognizer.energy_threshold = 300 
    recognizer.pause_threshold = 0.8 
    
    mic_index = SelectMicrophone()

    try:
        mic = sr.Microphone(device_index=mic_index)
        with mic as source:
            SetAssistantStatus("Listening...")
            print("\r>> Listening...                ", end="", flush=True)
            
            recognizer.adjust_for_ambient_noise(source, duration=0.5)
            
            try:
                audio_data = recognizer.listen(source, timeout=10, phrase_time_limit=12)
                
                SetAssistantStatus("Processing...")
                print("\r>> Transcribing (Groq LPU)...   ", end="", flush=True)

                temp_file = os.path.join(root_dir, "temp_voice.wav")
                with open(temp_file, "wb") as f:
                    f.write(audio_data.get_wav_data())

                # --- GROQ WHISPER API CALL ---
                with open(temp_file, "rb") as audio_file:
                    transcription = groq_client.audio.transcriptions.create(
                        file=(temp_file, audio_file.read()),
                        model="whisper-large-v3",
                        response_format="text",
                        prompt="Jarvis. Open Notepad. Jarvis, what is the weather today? Calculate the numbers."
                    )
                
                text = str(transcription)

                if not text or len(text.strip()) < 2:
                    return ""

                print(f"\r>> User said: {text}           ")
                SetAssistantStatus("Translating...")
                
                final_text = UniversalTranslator(text)
                
                return QueryModifier(final_text)

            except Exception as e:
                # Silently catch timeout errors so the terminal isn't flooded with warnings
                if "timeout" not in str(e).lower():
                    print(f"\n!! Groq Error: {e}")
                return ""
                
    except Exception as e:
        print(f"\n!! Hardware Error: {e}")
        SetAssistantStatus("Mic Error")
        return ""

if __name__ == "__main__":
    print(">> Groq Speech Engine Online.")
    while True:
        result = SpeechRecognition() 
        if result:
            print(f"Final Output: {result}")