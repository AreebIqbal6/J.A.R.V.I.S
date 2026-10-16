import speech_recognition as sr
import os
import sys
import io
import requests
from groq import Groq
from dotenv import dotenv_values, load_dotenv

# --- ROBUST ENV LOADING ---
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
env_path = os.path.join(root_dir, ".env")
env_vars = dotenv_values(env_path)

dg_key = env_vars.get("DEEPGRAM_API_KEY")
groq_key = env_vars.get("GroqAPIKey")

if not dg_key or not groq_key:
    load_dotenv(env_path)
    dg_key = dg_key or os.getenv("DEEPGRAM_API_KEY")
    groq_key = groq_key or os.getenv("GroqAPIKey")

# Lazy-loaded / cached Groq client
_groq_client = None
def get_groq_client():
    global _groq_client
    if _groq_client is None and groq_key:
        try:
            _groq_client = Groq(api_key=groq_key)
        except Exception:
            _groq_client = None
    return _groq_client

PROMPT_BIAS = "Jarvis, Areeb, Fariya, Karachi, Bitcoin, Spotify, thermostat, lights, plug, Ferrari, telemetry, Python, YouTube"

# --- HELPER FUNCTIONS ---
def QueryModifier(Query):
    if not Query: return ""
    new_query = Query.lower().strip()
    if not new_query: return ""
    
    # Clean up acronym variations of J.A.R.V.I.S. and common misheard wake-words
    import re
    new_query = re.sub(r'\bj\.?a\.?r\.?v\.?i\.?s\.?\b', 'jarvis', new_query)
    corrupted_names = ["harvest", "starves", "travis", "jairus", "ravish", "आवेश", "गार्विस", "west", "वेस्ट"]
    for name in corrupted_names:
        new_query = new_query.replace(name, "jarvis")

    # If it is just the wake word alone
    clean_stripped = new_query.strip('.,?! ')
    if clean_stripped == "jarvis":
        return "Jarvis"

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

def transcribe_audio_bytes(audio_bytes: bytes) -> str:
    """Ultra-fast STT with Groq Whisper-large-v3-turbo and Deepgram Nova-2 fallback."""
    # 1. Primary Engine: Groq Whisper-large-v3-turbo (p50 ~500ms)
    client = get_groq_client()
    if client:
        try:
            res = client.audio.transcriptions.create(
                file=("speech.wav", audio_bytes),
                model="whisper-large-v3-turbo",
                prompt=PROMPT_BIAS,
                language="en",
                temperature=0.0
            )
            text = (res.text or "").strip()
            if len(text) >= 2:
                return text
        except Exception as e:
            # Fall back to Deepgram if Groq rate-limits
            pass

    # 2. Secondary Engine: Deepgram Nova-2 with keyword biasing
    if dg_key:
        try:
            keywords = "keywords=Jarvis:3&keywords=Areeb:3&keywords=Fariya:2&keywords=Bitcoin:2&keywords=Karachi:2&keywords=thermostat:2&keywords=plug:2"
            url = f"https://api.deepgram.com/v1/listen?model=nova-2&smart_format=true&filler_words=false&{keywords}"
            headers = {
                "Authorization": f"Token {dg_key}",
                "Content-Type": "audio/wav"
            }
            resp = requests.post(url, headers=headers, data=audio_bytes, timeout=8)
            if resp.status_code == 200:
                data = resp.json()
                channels = data.get("results", {}).get("channels", [])
                if channels:
                    alts = channels[0].get("alternatives", [])
                    if alts:
                        # Confidence gating
                        confidence = alts[0].get("confidence", 1.0)
                        if confidence < 0.35:
                            return ""
                        return alts[0].get("transcript", "").strip()
        except Exception as e:
            print(f"!! Deepgram Fallback Error: {e}")

    return ""

# Persistent calibrated recognizer to avoid 500ms per-turn calibration
_calibrated_recognizer = None
_calibrated_mic = None

def get_calibrated_audio_source():
    global _calibrated_recognizer, _calibrated_mic
    if _calibrated_recognizer is None:
        _calibrated_recognizer = sr.Recognizer()
        _calibrated_recognizer.dynamic_energy_threshold = True
        # TUNED ENDPOINTING: 0.8s silence timeout for natural speaking cadence
        _calibrated_recognizer.pause_threshold = 0.8
        _calibrated_recognizer.non_speaking_duration = 0.4
        
        mic_idx = SelectMicrophone()
        _calibrated_mic = sr.Microphone(device_index=mic_idx, sample_rate=16000)
        with _calibrated_mic as src:
            # Run ambient calibration only ONCE at boot
            _calibrated_recognizer.adjust_for_ambient_noise(src, duration=0.4)
            if _calibrated_recognizer.energy_threshold < 300:
                _calibrated_recognizer.energy_threshold = 300
            elif _calibrated_recognizer.energy_threshold > 2500:
                _calibrated_recognizer.energy_threshold = 2000
    return _calibrated_recognizer, _calibrated_mic

# --- MAIN SPEECH RECOGNITION ---
def SpeechRecognition():
    from Backend.TextToSpeech import is_speaking, StopTTS

    recognizer, mic = get_calibrated_audio_source()

    try:
        with mic as source:
            SetAssistantStatus("Listening...")
            print("\r>> Listening...                ", end="", flush=True)
            try:
                from Backend.EventBus import EventBus
                EventBus.emit_state("listening")
            except Exception:
                pass
            
            try:
                # No long phrase timeout; 0.6s hangover silence
                audio_data = recognizer.listen(source, timeout=8, phrase_time_limit=15)
                
                # --- BARGE-IN INTERRUPTION ---
                if is_speaking():
                    StopTTS()
                
                SetAssistantStatus("Processing...")
                print("\r>> Transcribing...             ", end="", flush=True)

                raw_wav_bytes = audio_data.get_wav_data(convert_rate=16000, convert_width=2)
                transcribed = transcribe_audio_bytes(raw_wav_bytes)

                if not transcribed or len(transcribed) < 2:
                    SetAssistantStatus("Available...")
                    return ""
                
                final_text = QueryModifier(transcribed)
                print(f"\r>> User said: {final_text}           ")
                try:
                    from Backend.EventBus import EventBus
                    EventBus.emit_transcript(final_text, is_final=True)
                except Exception:
                    pass
                return final_text

            except sr.WaitTimeoutError:
                SetAssistantStatus("Available...")
                return ""
            except Exception as e:
                print(f"\n!! STT Audio Error: {e}")
                SetAssistantStatus("Available...")
                return ""
                
    except Exception as e:
        print(f"\n!! Hardware Audio Error: {e}")
        SetAssistantStatus("Mic Error")
        return ""

if __name__ == "__main__":
    print(">> Fast STT Engine Online.")
    while True:
        result = SpeechRecognition() 
        if result:
            print(f"Final Output: {result}")