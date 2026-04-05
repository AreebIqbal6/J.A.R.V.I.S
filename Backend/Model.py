import requests
import cohere
from dotenv import dotenv_values
from Backend.DSA_Manager import JARVIS_DSA 

# Initialize the DSA Manager
dsa_logistics = JARVIS_DSA()
env_vars = dotenv_values(".env")
CohereAPIKey = env_vars.get("CohereAPIKey")

# Added "presentation", "excel", "database", and "code" to the functions list
funcs = [
    "exit", "general", "realtime", "open", "close", "play",
    "generate image", "system", "content", "google search",
    "youtube search", "reminder", "weather", "calculate",
    "clipboard", "cleanup", "memory", "sentry", 
    "urban", "book", "news", "iss", "coordinates", 
    "currency", "show", "anime", "github", "agent", "vision", "f1", "quant",
    "presentation", "excel", "database", "code"
]

def Backup_HuggingFace_Router(prompt):
    HuggingFaceAPIKey = env_vars.get("HuggingFaceAPIKey")
    API_URL = "https://api-inference.huggingface.co/models/microsoft/Phi-3-mini-4k-instruct"
    headers = {"Authorization": f"Bearer {HuggingFaceAPIKey}"}
    
    definition = f"""<|system|>
    Classify the query into ONE category: {funcs}. 
    Output format: category prompt<|end|><|user|>{prompt}<|end|><|assistant|>"""
    
    try:
        response = requests.post(API_URL, headers=headers, json={"inputs": definition}, timeout=25)
        if response.status_code == 200:
            text = response.json()[0]['generated_text'].split("<|assistant|>")[-1].strip().lower()
            intent = text.split(" ")[0]
            if intent in funcs:
                return [text]
        return [f"general {prompt}"]
    except Exception as e:
        print(f"!! Backup Router Failed. Error: {e}")
        return [f"general {prompt}"]

def FirstLayerDMM(prompt: str = "test"):
    prompt_lower = prompt.lower().strip()
    
    corrupted_names = ["harvest", "starves", "travis", "jairus", "ravish", "west", "century", "सेंट्री"]
    for name in corrupted_names:
        if name in prompt_lower:
            prompt_lower = prompt_lower.replace(name, "jarvis")

    prompt_clean = prompt_lower.replace("jarvis", "").strip(", ").strip()
    dsa_logistics.push_history(prompt_clean)
    
    decisions = []

    # 1. Executive Suite & Local Coder
    if any(word in prompt_clean for word in ["presentation", "powerpoint", "slides"]):
        decisions.append(f"presentation {prompt_clean}")
    elif any(word in prompt_clean for word in ["excel", "spreadsheet", "data sheet", "csv"]):
        decisions.append(f"excel {prompt_clean}")
    elif any(word in prompt_clean for word in ["database", "sql", "sqlite", "db"]):
        decisions.append(f"database {prompt_clean}")
    elif any(word in prompt_clean for word in ["code", "script", "python", "program", "write an app"]):
        decisions.append(f"code {prompt_clean}")

    # 2. Phase 3 Agent Triggers (Complex logic, workflows, math)
    agent_triggers = ["solve", "design", "logic trap", "puzzle", "architect", "workflow"]
    if any(word in prompt_clean for word in agent_triggers):
        decisions.append(f"agent {prompt_clean}")

    # 3. Vision Triggers (The Safety Net)
    vision_triggers = ["look", "screen", "vision", "camera", "screenshot", "see", "what is in front of you"]
    if any(word in prompt_clean for word in vision_triggers):
        decisions.append(f"vision {prompt_clean}")

    # 4. Sentry Mode
    if "sentry" in prompt_clean or "security" in prompt_clean:
        decisions.append("sentry")

    # 5. Jokes/Small Talk
    chat_triggers = ["joke", "hello", "hi", "who are you", "how are you"]
    if any(word in prompt_clean for word in chat_triggers):
        decisions.append(f"general {prompt_clean}")

    # 6. Automation & Media
    if "open " in prompt_clean: 
        decisions.append(f"open {prompt_clean.split('open ')[1].strip()}")
    if "close " in prompt_clean:
        decisions.append(f"close {prompt_clean.split('close ')[1].strip()}")
    if "play " in prompt_clean:
        decisions.append(f"play {prompt_clean.split('play ')[1].strip()}")

    # 7. Memory
    memory_triggers = ["you remember", "i mention", "i say", "i said", "i told you", "just mentioned"]
    if any(word in prompt_clean for word in memory_triggers):
        decisions.append(f"general {prompt_clean}")

    # 8. Formula 1 Triggers
    f1_triggers = ["f1", "formula 1", "race", "grand prix", "verstappen", "hamilton", "mercedes", "ferrari", "mclaren", "who won"]
    if any(word in prompt_clean for word in f1_triggers) and "open " not in prompt_clean:
        decisions.append(f"f1 {prompt_clean}")

    # 9. Quantitative Broker Triggers (Stocks & Crypto)
    quant_triggers = ["stock", "price", "buy", "sell", "market", "trading", "nvidia", "apple", "tesla", "bitcoin", "crypto"]
    if any(word in prompt_clean for word in quant_triggers) and "open " not in prompt_clean:
        decisions.append(f"quant {prompt_clean}")

    # 10. Realtime
    realtime_triggers = ["weather", "temperature", "who is", "what is", "wonder", "match", "vs", "versus", "score", "t20", "cricket"]
    if any(word in prompt_clean for word in realtime_triggers) and not any(f.startswith("f1") or f.startswith("quant") for f in decisions):
        decisions.append(f"realtime {prompt_clean}")

    if decisions:
        return list(set(decisions))

    # --- PRIMARY LLM ROUTER (UNIVERSAL FALLBACK ENFORCED) ---
    try:
        if CohereAPIKey:
            co = cohere.Client(api_key=CohereAPIKey)
            preamble = (
                f"You are the intent router for JARVIS. Categories: {funcs}. "
                "Classify the input precisely. Output EXACTLY the category followed by the query. NO BRACKETS. "
                "Example 1: general count from 1 to 10. "
                "Example 2: google search is the pixel 8 pro a good phone. "
                "CRITICAL DIRECTIVES: "
                "If asking to make a presentation or powerpoint, use 'presentation'. "
                "If asking to make an excel or spreadsheet, use 'excel'. "
                "If asking to make a database, use 'database'. "
                "If asking to write code or a script, use 'code'. "
                "If asking to construct a logic workflow, use 'agent'. "
                "UNIVERSAL DIRECTIVE: If you do not explicitly recognize the command, or if it is a casual conversation, ALWAYS default to 'general'. Never invent a category."
            )
            response = co.chat(
                model='command-r-08-2024',
                message=prompt_clean, 
                temperature=0.0,
                preamble=preamble
            )
            
            clean_response = response.text.replace("[", "").replace("]", "").replace('"', '').replace("'", "").strip().lower()
            results = [res.strip() for res in clean_response.split(",")]
            
            # THE VALIDATOR: Ensure the LLM didn't hallucinate a fake command
            valid_results = []
            for res in results:
                intent = res.split(" ")[0]
                if intent in funcs:
                    valid_results.append(res)
            
            if valid_results:
                return valid_results
            else:
                # If Cohere fails the validation check, force General Chatbot.
                return [f"general {prompt_clean}"]
                
    except Exception as e:
        print(f"!! Primary Router Offline. Error: {e}")
        return Backup_HuggingFace_Router(prompt_clean)

    return [f"general {prompt_clean}"]