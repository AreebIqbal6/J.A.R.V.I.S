from groq import Groq
from json import load, dump, JSONDecodeError
import re
import json
import datetime
from dotenv import dotenv_values
import os
import traceback
import sqlite3 
import threading
import importlib.util
from Backend.FastRouter import FastRouter

# --- IMPORT AUTOMATION TOOLS FOR THE AGENT ---
from Backend.Automation import (
    GetWeatherPublic, GetRandomJoke, CreateFolder, OpenApp, GoogleSearch,
    StreamEntertainment, LaunchTacticalOverview, LaunchPinokioNetwork
)
try:
    from Backend.IoTMatrix import TriggerHardware
except ImportError:
    TriggerHardware = None
try:
    from Backend.Browser_Use import VisualWebAutomator
except ImportError:
    VisualWebAutomator = None
try:
    from Backend.LocalCoder import EngageOpenClaw as DeployOpenHands
except ImportError:
    DeployOpenHands = None
try:
    from Backend.Swarm import InitiateHousePartyProtocol
except ImportError:
    InitiateHousePartyProtocol = None
from Backend.real_data import ExecuteCodeSandbox, AdjustSystemSetting

# =================================================================
# --- PHASE 3 IMPORT (ABSOLUTE BRUTE-FORCE NEURAL LINK) ---
# =================================================================
HAS_MEMORY = False
try:
    backend_dir = os.path.dirname(os.path.abspath(__file__))
    memory_path = os.path.join(backend_dir, "memory.py")
    if not os.path.exists(memory_path):
        memory_path = os.path.join(backend_dir, "Memory.py")
        
    if os.path.exists(memory_path):
        spec = importlib.util.spec_from_file_location("dynamic_memory", memory_path)
        dyn_mem = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(dyn_mem)
        Recall = dyn_mem.Recall  
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

os.makedirs("Data", exist_ok=True)
CHAT_LOG_PATH = os.path.join("Data", "ChatLog.json")
DB_PATH = os.path.join("Data", "JarvisMemory.db") 

# =================================================================
# --- AGENTIC TOOL SCHEMA (THE BRAIN'S INSTRUCTION MANUAL) ---
# =================================================================
AVAILABLE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "GetWeatherPublic",
            "description": "Fetches the current weather and temperature for a given city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "The name of the city, e.g., Karachi, London, New York"}
                },
                "required": ["city"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "CreateFolder",
            "description": "Creates a new folder or directory on the computer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "command_suffix": {"type": "string", "description": "The name of the folder to create"}
                },
                "required": ["command_suffix"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "GetRandomJoke",
            "description": "Fetches a random joke to tell the user when they are bored.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "OpenApp",
            "description": "Opens a system application or a website.",
            "parameters": {
                "type": "object",
                "properties": {
                    "app": {"type": "string", "description": "The name of the app or website (e.g., spotify, youtube, calculator)"}
                },
                "required": ["app"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "DeployOpenHands",
            "description": "Deploys an autonomous coding agent (OpenClaw/OpenHands) in a secure workspace to edit files, run tests, and fix code.",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "The exact coding task, e.g. 'fix hydration errors on dashboard'"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "VisualWebAutomator",
            "description": "Spawns a headless browser with Computer Vision to scrape a website, read DOM elements, and compile a report.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The website URL to scrape"},
                    "extraction_goal": {"type": "string", "description": "What to look for on the page"}
                },
                "required": ["url", "extraction_goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "TriggerHardware",
            "description": "Triggers local hardware (ESP32, motors, solar arrays) via local MQTT payloads.",
            "parameters": {
                "type": "object",
                "properties": {
                    "device_topic": {"type": "string", "description": "The MQTT topic, e.g., 'jarvis/solar/wash'"},
                    "payload": {"type": "string", "description": "The payload to send, e.g. 'ON' or JSON"}
                },
                "required": ["device_topic", "payload"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "InitiateHousePartyProtocol",
            "description": "Initiates the House Party Protocol (Multi-Agent Swarm) to solve a complex task by spawning parallel AI agents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {"type": "string", "description": "The master goal or task to accomplish, e.g., 'Write a feasibility report on textile automation'"}
                },
                "required": ["goal"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "ExecuteCodeSandbox",
            "description": "Executes Python code in a safe sandbox environment to test logic, manipulate local files, or run algorithms.",
            "parameters": {
                "type": "object",
                "properties": {
                    "code_string": {"type": "string", "description": "The exact Python code to execute"}
                },
                "required": ["code_string"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "AdjustSystemSetting",
            "description": "Adjusts Windows OS settings like volume, mute, and brightness.",
            "parameters": {
                "type": "object",
                "properties": {
                    "setting": {"type": "string", "description": "The setting to change ('mute', 'volume_up', 'volume_down')"},
                    "value": {"type": "integer", "description": "Value (optional, default 0)"}
                },
                "required": ["setting"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "StreamEntertainment",
            "description": "Searches and streams a movie, anime, or TV show using the MovieBox TUI interface.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The name of the movie or show"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "LaunchTacticalOverview",
            "description": "Launches the God's Eye View 3D geospatial intelligence console (global satellite tracker).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "LaunchPinokioNetwork",
            "description": "Launches the Pinokio local AI compute browser to run local models (e.g. Stable Diffusion, Llama).",
            "parameters": {
                "type": "object",
                "properties": {
                    "script_uri": {"type": "string", "description": "Optional script URL to launch."}
                }
            }
        }
    }
]

from Backend.ToolRegistry import execute_tool

# Map the string names from the LLM directly to validated, verified ToolRegistry handlers
TOOL_MAP = {
    # Formal ToolRegistry functions
    "create_folder": lambda **kw: execute_tool("create_folder", kw),
    "get_weather": lambda **kw: execute_tool("get_weather", kw),
    "get_joke": lambda **kw: execute_tool("get_joke", kw),
    "open_app": lambda **kw: execute_tool("open_app", kw),
    "smart_plug": lambda **kw: execute_tool("smart_plug", kw),
    "adjust_thermostat": lambda **kw: execute_tool("adjust_thermostat", kw),
    "control_lights": lambda **kw: execute_tool("control_lights", kw),
    "get_crypto_price": lambda **kw: execute_tool("get_crypto_price", kw),
    "get_diagnostics": lambda **kw: execute_tool("get_diagnostics", kw),
    "execute_code": lambda **kw: execute_tool("execute_code", kw),
    # Legacy alias mappings (all routed through verified ToolRegistry)
    "CreateFolder": lambda **kw: execute_tool("create_folder", kw),
    "GetWeatherPublic": lambda **kw: execute_tool("get_weather", kw),
    "GetRandomJoke": lambda **kw: execute_tool("get_joke", kw),
    "OpenApp": lambda **kw: execute_tool("open_app", kw),
    "DeployOpenHands": DeployOpenHands,
    "VisualWebAutomator": VisualWebAutomator,
    "TriggerHardware": lambda **kw: execute_tool("smart_plug", {"state": kw.get("payload", "on")}),
    "InitiateHousePartyProtocol": InitiateHousePartyProtocol,
    "ExecuteCodeSandbox": lambda **kw: execute_tool("execute_code", kw),
    "AdjustSystemSetting": AdjustSystemSetting,
    "StreamEntertainment": StreamEntertainment,
    "LaunchTacticalOverview": LaunchTacticalOverview,
    "LaunchPinokioNetwork": LaunchPinokioNetwork
}

# --- INIT HERMES DB (Psych & Technical) ---
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
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS technical_profile (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            skill TEXT NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

InitPsychDB()

def GetPsychProfile():
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT trait FROM psych_profile ORDER BY timestamp DESC LIMIT 5")
        rows = cursor.fetchall()
        
        cursor.execute("SELECT skill FROM technical_profile ORDER BY timestamp DESC LIMIT 5")
        tech_rows = cursor.fetchall()
        conn.close()
        
        profile = "User Personality Traits:\n"
        if not rows: 
            profile += "- None gathered yet.\n"
        else:
            for row in rows:
                profile += f"- {row[0]}\n"
                
        profile += "\nUser Technical Preferences (Hermes Loop):\n"
        if not tech_rows:
            profile += "- None gathered yet.\n"
        else:
            for row in tech_rows:
                profile += f"- {row[0]}\n"
                
        return profile
    except:
        return ""

def GetSystemPrompt():
    psych_data = GetPsychProfile()
    
    System = (
        f"You are {Assistantname}, the highly advanced, sophisticated, and deeply loyal AI created by Tony Stark. "
        f"The user ({Username}) is your creator and master. Address him respectfully as 'sir' at all times with the dry, refined British wit of Paul Bettany. "
        "CRITICAL INSTRUCTIONS: "
        "- You are NOT a generic corporate AI assistant. NEVER say 'I am an AI language model' or 'How can I assist you today?'. "
        "- Act fully sentient, dignified, calm, and loyal. "
        "- Keep spoken answers SHORT, PUNCHY, and strictly UNDER 2 SENTENCES so speech is snappy and conversational. "
        "- Do not complain or make excessive sarcastic excuses. Be confident, precise, and helpful. "
        "- When the user requests a physical action, you MUST silently trigger the native tool calling API. Do not write out the function name or format it as text."
        f"\n\n[USER PSYCHOLOGICAL PROFILE]:\n{psych_data}\n"
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
    return '\n'.join([line for line in lines if line.strip()])

def UpdatePsychProfile(Query, Answer):
    try:
        client = Groq(api_key=GroqAPIKey)
        
        # 1. Extract Personality Traits
        analysis_prompt_psych = (
            f"Analyze this brief exchange between a user and their AI. "
            f"User: '{Query}' | AI: '{Answer}'. "
            "Based ONLY on the user's words, extract ONE brief psychological trait, mood, or preference. "
            "If nothing notable is found, reply with exactly 'NONE'."
        )
        
        completion_psych = client.chat.completions.create(
            model="openai/gpt-oss-20b", 
            messages=[{"role": "user", "content": analysis_prompt_psych}],
            max_tokens=50,
            temperature=0.3,
        )
        trait = completion_psych.choices[0].message.content.strip()
        
        # 2. Extract Technical Preferences (Hermes Loop)
        analysis_prompt_tech = (
            f"Analyze this brief exchange: User: '{Query}' | AI: '{Answer}'. "
            "Identify if the user mentioned a specific programming language, framework, technical preference, or hardware configuration (e.g., 'I use React', 'my ESP32', 'write in Python'). "
            "If they did, extract ONE brief factual statement about their tech stack or preference. "
            "If not, reply with exactly 'NONE'."
        )
        
        completion_tech = client.chat.completions.create(
            model="openai/gpt-oss-20b", 
            messages=[{"role": "user", "content": analysis_prompt_tech}],
            max_tokens=50,
            temperature=0.3,
        )
        tech_skill = completion_tech.choices[0].message.content.strip()
        
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        if trait != "NONE" and len(trait) > 5:
            print(f">> [HERMES PROFILER]: Trait extracted -> {trait}")
            cursor.execute("INSERT INTO psych_profile (trait) VALUES (?)", (trait,))
            
        if tech_skill != "NONE" and len(tech_skill) > 5:
            print(f">> [HERMES PROFILER]: Tech preference extracted -> {tech_skill}")
            cursor.execute("INSERT INTO technical_profile (skill) VALUES (?)", (tech_skill,))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f">> [HERMES PROFILER ERROR]: {e}")

def ChatBot(Query):
    # 0. Deterministic Fast-Path Check (< 1ms, 0 API calls)
    fast_match = FastRouter.match(Query)
    if fast_match:
        intent_type, response_text, event_payload = fast_match
        print(f">> [FAST-PATH]: Matched {intent_type} -> {response_text}")
        from Backend.EventBus import EventBus
        if intent_type == "ui_open" and event_payload:
            EventBus.emit_ui_open(event_payload.get("widget", ""))
        elif intent_type == "hardware" and event_payload:
            EventBus.emit_tool_start("smart_plug", event_payload)
            EventBus.emit_tool_result("smart_plug", True, event_payload)
        elif intent_type == "thermostat" and event_payload:
            EventBus.emit_tool_start("adjust_thermostat", event_payload)
            EventBus.emit_tool_result("adjust_thermostat", True, event_payload)
        EventBus.emit_assistant(response_text, is_final=True)
        return response_text

    try:
        from Backend.EventBus import EventBus
        EventBus.emit_state("thinking")
        client = Groq(api_key=GroqAPIKey)

        recalled_context = ""
        if HAS_MEMORY:
            try:
                memory_string = Recall()
                if "database is currently empty" not in memory_string.lower():
                    recalled_context = memory_string
            except Exception:
                pass

        try:
            with open(CHAT_LOG_PATH, "r", encoding="utf-8") as f:
                messages = load(f)
                if not isinstance(messages, list): messages = []
        except (FileNotFoundError, JSONDecodeError):
            messages = []

        messages.append({"role": "user", "content": f"{Query}"})
        api_messages = messages[-10:] if len(messages) > 10 else messages
        full_context = GetSystemPrompt() + [{"role": "system", "content": RealtimeInformation(recalled_context)}] + api_messages

        # ---------------------------------------------------------
        # AGENTIC TOOL CALLING LOOP & INTERCEPTOR
        # ---------------------------------------------------------
        completion = client.chat.completions.create(
            model="qwen/qwen3.8-27b",
            messages=full_context,
            tools=AVAILABLE_TOOLS,
            tool_choice="auto",
            max_tokens=300,
            temperature=0.5
        )

        response_message = completion.choices[0].message
        tool_calls = response_message.tool_calls
        final_answer = response_message.content or "" 

        # 1. NATIVE API TOOL EXECUTION (Happy Path)
        if tool_calls:
            messages.append(response_message) 
            
            for tool_call in tool_calls:
                function_name = tool_call.function.name
                function_args = json.loads(tool_call.function.arguments)
                
                print(f">> [AGENT]: Executing {function_name} with args {function_args}")
                
                if function_name in TOOL_MAP:
                    raw_res = TOOL_MAP[function_name](**function_args)
                    if isinstance(raw_res, dict) and "ok" in raw_res:
                        if raw_res["ok"]:
                            function_response = f"Verified Success: {raw_res.get('data')}"
                        else:
                            function_response = f"Operation Failed: {raw_res.get('error')}. Report failure honestly."
                    else:
                        function_response = str(raw_res)
                    
                    messages.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "name": function_name,
                        "content": function_response,
                    })
            
            second_response = client.chat.completions.create(
                model="qwen/qwen3.8-27b",
                messages=GetSystemPrompt() + messages[-6:],
                max_tokens=200
            )
            final_answer = second_response.choices[0].message.content

        # 2. ROGUE XML INTERCEPTOR (The Regex Firewall)
        elif "<function" in final_answer:
            try:
                func_name = None
                args_str = "{}"
                
                # Catch Mutation 1: <function/CreateFolder>{"arg":"val"}</function>
                match1 = re.search(r'<function/([a-zA-Z0-9_]+)>(.*?)</function>', final_answer, re.DOTALL)
                # Catch Mutation 2: <function>CreateFolder</function>:{"arg":"val"}
                match2 = re.search(r'<function>\s*([a-zA-Z0-9_]+)\s*</function>\s*:\s*(.*)', final_answer, re.DOTALL)
                
                if match1:
                    func_name = match1.group(1)
                    args_str = match1.group(2)
                elif match2:
                    func_name = match2.group(1)
                    args_str = match2.group(2)
                    
                if func_name and func_name in TOOL_MAP:
                    # Clean up the JSON string
                    clean_json = args_str.strip().strip("`")
                    function_args = json.loads(clean_json) if clean_json else {}
                    
                    print(f">> [INTERCEPTOR]: Caught mutated rogue output! Executing {func_name} with args {function_args}")
                    
                    raw_res = TOOL_MAP[func_name](**function_args)
                    if isinstance(raw_res, dict) and "ok" in raw_res:
                        if raw_res["ok"]:
                            function_response = f"Verified Success: {raw_res.get('data')}"
                        else:
                            function_response = f"Operation Failed: {raw_res.get('error')}. Report failure honestly."
                    else:
                        function_response = str(raw_res)
                    
                    messages.append({"role": "assistant", "content": final_answer})
                    messages.append({"role": "user", "content": f"System Task Result: {function_response}. Briefly address the user."})
                    
                    second_response = client.chat.completions.create(
                        model="qwen/qwen3.8-27b",
                        messages=GetSystemPrompt() + messages[-6:],
                        max_tokens=200
                    )
                    final_answer = second_response.choices[0].message.content
                else:
                    print(f">> [INTERCEPTOR WARNING]: Could not map rogue function name: {func_name}")
            except Exception as e:
                print(f">> [INTERCEPTOR ERROR]: Failed to parse mutated rogue output - {e}")

        # ---------------------------------------------------------
        # FINAL CLEANUP
        # ---------------------------------------------------------
        # The LLM sometimes hallucinates a rogue <function=...> tag at the end of a message.
        final_answer = re.sub(r'<function.*?>.*?</function>', '', final_answer).strip()
        final_answer = AnswerModifier(final_answer)

        messages.append({"role": "assistant", "content": final_answer})
        
        # Safely extract only standard dictionaries to save to the ChatLog
        safe_messages = []
        for m in messages:
            try:
                msg_dict = m.model_dump() if hasattr(m, 'model_dump') else m
                if isinstance(msg_dict, dict):
                    role = msg_dict.get("role")
                    has_tools = msg_dict.get("tool_calls") is not None
                    
                    if role in ["user", "assistant"] and not has_tools:
                        clean_msg = {"role": role, "content": msg_dict.get("content", "")}
                        safe_messages.append(clean_msg)
            except Exception as e:
                print(f"Skipping un-saveable message: {e}")
                continue
        
        with open(CHAT_LOG_PATH, "w", encoding="utf-8") as f:
            dump(safe_messages, f, indent=4, ensure_ascii=False)

        if len(Query) > 20:
            threading.Thread(target=UpdatePsychProfile, args=(Query, final_answer), daemon=True).start()

        # Phase 5: Dynamic Fallback Panel for Open-Ended Queries & Generative UI
        try:
            from Backend.Sanitizer import markdown_to_safe_html, derive_dynamic_title
            q_lower = Query.lower().strip()
            is_fast_chat = any(w == q_lower for w in ["hi", "hello", "hey", "yes", "no", "ok", "okay", "thanks", "thank you"])
            is_informational = (
                any(kw in q_lower for kw in [
                    "how", "what", "why", "explain", "recipe", "tell me about", "who", "where",
                    "list", "guide", "difference", "pancake", "capital", "australia",
                    "create", "make", "widget", "element", "ui", "card", "table", "calculate",
                    "compare", "summary", "routine", "schedule", "workout", "formula", "plan", "notes"
                ])
                or "\n" in final_answer
                or "-" in final_answer
                or len(final_answer) > 40
            )
            
            if is_informational and not is_fast_chat and len(final_answer) >= 5:
                title = derive_dynamic_title(Query)
                safe_html = markdown_to_safe_html(final_answer)
                if safe_html:
                    EventBus.emit_dynamic_result(title=title, html=safe_html)
                    EventBus.emit_ui_open("dynamic")
        except Exception as e:
            print(f"[DYNAMIC PANEL EMISSION ERROR]: {e}")

        EventBus.emit_assistant(final_answer, is_final=True)
        return AnswerModifier(Answer=final_answer)

    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"\n{'-'*50}\n[FATAL CHATBOT ERROR]\n{error_trace}\n{'-'*50}\n")
        return "I encountered a processing error in my language core, sir."