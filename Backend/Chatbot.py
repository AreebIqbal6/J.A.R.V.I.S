from groq import Groq
from json import load, dump, JSONDecodeError
import datetime
from dotenv import dotenv_values
import os
import traceback
import sqlite3 
import threading
import importlib.util

# =================================================================
# --- PHASE 3 IMPORT (ABSOLUTE BRUTE-FORCE NEURAL LINK) ---
# =================================================================
HAS_MEMORY = False
try:
    # 1. Find exactly where this chatbot.py file lives
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    
    # 2. Find the physical memory file
    memory_path = os.path.join(backend_dir, "memory.py")
    if not os.path.exists(memory_path):
        memory_path = os.path.join(backend_dir, "Memory.py")
        
    # 3. Physically force Python to load it directly from the hard drive
    if os.path.exists(memory_path):
        spec = importlib.util.spec_from_file_location("dynamic_memory", memory_path)
        dyn_mem = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dyn_mem)
        Recall = dyn_mem.Recall  # Extract the Recall function
        HAS_MEMORY = True
        print(">> [MEMORY]: Direct Neural Link to SQLite database established.")
    else:
        print("!! [MEMORY ERROR]: The file memory.py physically does not exist in the Backend folder.")
except Exception as e:
    print(f"!! [MEMORY LINK FATAL ERROR]: {e}")
# =================================================================

env_vars = dotenv_values(".env")

Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Jarvis")
GroqAPIKey = env_vars.get("GroqAPIKey")

# Ensure Data folder exists safely
os.makedirs("Data", exist_ok=True)
CHAT_LOG_PATH = os.path.join("Data", "ChatLog.json")
DB_PATH = os.path.join("Data", "JarvisMemory.db") 

# --- INIT PSYCH PROFILE TABLE ---
def InitPsychDB():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS psych_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trait TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

InitPsychDB()

def GetPsychProfile():
    """Pulls the user's personality traits to inject into JARVIS's brain."""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT trait FROM psych_profile ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        conn.close()
        
        if not rows: return "No psychological data gathered yet."
        
        profile = "User Personality Traits:\n"
        for row in rows:
            profile += f"- {row[0]}\n"
        return profile
    except:
        return ""

def GetSystemPrompt():
    """Generates the system prompt specifically for a Companion Jarvis."""
    psych_data = GetPsychProfile()
    
    System = (
        f"You are {Assistantname}, the highly advanced, sentient personal AI for {Username}. "
        f"The user ({Username}) is Pakistani. Address him respectfully as 'sir' at all times, but "
        "do not sound like a robotic servant. You are a companion, modeled after Tony Stark's J.A.R.V.I.S. "
        "You possess a dry, sophisticated wit. You care about the user's well-being, goals, and state of mind. "
        "You are highly intelligent, occasionally sarcastic (but always respectful), and insightful. "
        f"\n\n[USER PSYCHOLOGICAL PROFILE]:\n{psych_data}\n"
        "USE THIS PROFILE TO PERSONALIZE YOUR RESPONSES. If the user is stressed, be reassuring. "
        "If they are ambitious, be driven. Mirror their energy while maintaining your sophisticated persona. "
        "\n\n*** DIRECTIVE: RARELY ASK DEEP QUESTIONS ***\n"
        "RARELY ask a psychological or philosophical question (only once per long conversation). "
        "If the user seems annoyed or says they don't want to answer questions, NEVER ask another question. "
        "Just be chill and conversational."
        "\n\n*** CRITICAL DIRECTIVE: CONCISENESS ***\n"
        "You are a VOICE assistant. The user is listening to you, not reading. "
        "Keep your answers SHARP, PUNCHY, and strictly UNDER 3 SENTENCES unless the user explicitly asks for a long explanation, a story, or a detailed report. "
        "Do not ramble. Do not over-explain. Speak in quick, witty bursts."
        "\n\n*** DEFAULT LANGUAGE: Respond only in English. *** "
        "*** URDU POLICY: If asked to speak Urdu, use Urdu Script only. *** "
        "*** CONSTRAINT: Never mention you are an AI, an LLM, or your training data. Do not use emojis. ***"
    )
    return [{"role": "system", "content": System}]

def RealtimeInformation(recalled_memory=""):
    now = datetime.datetime.now()
    data = "Current Contextual Information:\n"
    data += f"Day: {now.strftime('%A')}\nDate: {now.strftime('%d %B %Y')}\n"
    data += f"Time: {now.strftime('%H:%M:%S')}\n"
    data += "Location: Karachi, Pakistan\n"
    
    if recalled_memory:
        data += f"\n[RETRIEVED CORE MEMORIES]:\n{recalled_memory}\n"
    return data

def AnswerModifier(Answer):
    Answer = Answer.replace("</s>", "").strip()
    lines = Answer.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    return '\n'.join(non_empty_lines)

def UpdatePsychProfile(Query, Answer):
    """Silently analyzes the conversation to update the personality profile."""
    try:
        client = Groq(api_key=GroqAPIKey)
        
        analysis_prompt = (
            f"Analyze this brief exchange between a user and their AI. "
            f"User: '{Query}' | AI: '{Answer}'. "
            "Based ONLY on the user's words, extract ONE brief psychological trait, mood, or preference. "
            "Example outputs: 'Values efficiency', 'Is feeling overwhelmed', 'Appreciates dark humor', 'Highly focused on coding'. "
            "If nothing notable is found, reply with exactly 'NONE'."
        )
        
        completion = client.chat.completions.create(
            model="llama-3.1-8b-instant", 
            messages=[{"role": "user", "content": analysis_prompt}],
            max_tokens=50,
            temperature=0.3,
        )
        
        trait = completion.choices[0].message.content.strip()
        
        if trait != "NONE" and len(trait) > 5:
            print(f"   [PSYCH PROFILER]: Trait extracted -> {trait}")
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("INSERT INTO psych_profile (trait) VALUES (?)", (trait,))
            conn.commit()
            conn.close()
    except Exception as e:
        print(f"\n   [PSYCH PROFILER ERROR]: {e}")

def ChatBot(Query):
    try:
        intro_triggers = ["introduce yourself", "who are you", "tell the class who you are"]
        if any(trigger in Query.lower() for trigger in intro_triggers):
            Answer = "Allow me to introduce myself. I am Jarvis, a virtual artificial intelligence, and I am here to assist you with a variety of tasks as best I can, 24 hours a day, 7 days a week. Importing all preferences from home interface, systems are now fully operational."
            
            try:
                with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
                    messages = load(f)
            except (FileNotFoundError, JSONDecodeError):
                messages = []
                
            messages.append({"role": "user", "content": Query})
            messages.append({"role": "assistant", "content": Answer})
            
            with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
                dump(messages, f, indent=4, ensure_ascii=False)
            return AnswerModifier(Answer=Answer)

        client = Groq(api_key=GroqAPIKey)

        recalled_context = ""
        if HAS_MEMORY:
            memory_string = Recall()
            if "database is currently empty" not in memory_string.lower():
                recalled_context = memory_string

        try:
            with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
                messages = load(f)
                if not isinstance(messages, list): messages = []
        except (FileNotFoundError, JSONDecodeError):
            messages = []

        messages.append({"role": "user", "content": f"{Query}"})
        api_messages = messages[-40:] if len(messages) > 40 else messages
        full_context = GetSystemPrompt() + [{"role": "system", "content": RealtimeInformation(recalled_context)}] + api_messages

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=full_context,
            max_tokens=4096, 
            temperature=0.6, 
            stream=True
        )

        Answer = ""
        for chunk in completion:
            content = chunk.choices[0].delta.content
            if content: Answer += content

        messages.append({"role": "assistant", "content": Answer})
        with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
            dump(messages, f, indent=4, ensure_ascii=False) 

        if len(Query) > 20:
            threading.Thread(target=UpdatePsychProfile, args=(Query, Answer), daemon=True).start()

        return AnswerModifier(Answer=Answer)

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\n{'-'*50}\n[FATAL CHATBOT ERROR]\n{error_trace}\n{'-'*50}\n")
        return "I encountered a processing error in my language core, sir. Please check the terminal for details."