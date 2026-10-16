import os
import sys
import asyncio
from dotenv import dotenv_values, load_dotenv

print("\n" + "="*50)
print("   J.A.R.V.I.S PRE-FLIGHT DEMO CHECKLIST")
print("="*50 + "\n")

# 1. Environment Variables
print("[1] Checking Environment API Keys...")
env_path = ".env"
env_vars = dotenv_values(env_path)
if not env_vars:
    load_dotenv(env_path)
    env_vars = os.environ

keys_to_check = {
    "Deepgram STT (Native Bilingualism)": "DEEPGRAM_API_KEY",
    "Groq LPU (Main Brain)": "GroqAPIKey",
    "Cohere (Intent Router)": "CohereAPIKey",
    "Smart Plug IP": "SMART_PLUG_IP"
}

all_keys_passed = True
for name, var in keys_to_check.items():
    if env_vars.get(var):
        print(f"  [+] {name}: Configured")
    else:
        print(f"  [-] {name}: MISSING ({var})")
        all_keys_passed = False

if not all_keys_passed:
    print("\n[!] WARNING: You have missing API keys in your .env file.")
    print("    JARVIS might fail during the demo. Please add them.")
else:
    print("  => All API keys are loaded successfully!\n")


# 2. Smart Plug Network Check
print("[2] Verifying TP-Link Kasa Smart Plug Connection...")
plug_ip = env_vars.get("SMART_PLUG_IP", "192.168.1.100")
if not env_vars.get("SMART_PLUG_IP"):
    print(f"  [!] SMART_PLUG_IP is not in .env. Defaulting to {plug_ip}")
    print("      Please add SMART_PLUG_IP=192.168.x.x to your .env once you buy the plug.")
else:
    try:
        from kasa import SmartPlug
        async def check_plug():
            plug = SmartPlug(plug_ip)
            await plug.update()
            print(f"  [+] Smart Plug Found! State: {'ON' if plug.is_on else 'OFF'}")
        asyncio.run(check_plug())
    except ImportError:
        print("  [-] python-kasa is not installed. Run: pip install python-kasa")
    except Exception as e:
        print(f"  [-] Could not reach Smart Plug at {plug_ip}. Is it connected to the same Wi-Fi?")


# 3. Audio & Dependencies
print("\n[3] Checking System Audio & Libraries...")
try:
    import speech_recognition as sr
    print("  [+] Speech Recognition Module: Installed")
except ImportError:
    print("  [-] Speech Recognition Module: MISSING")

try:
    import docx
    print("  [+] MS Word Automation (python-docx): Installed")
except ImportError:
    print("  [-] MS Word Automation: MISSING. Run: pip install python-docx")

print("\n" + "="*50)
print(" PRE-FLIGHT COMPLETE. IF ALL [+] ARE GREEN, JARVIS IS READY FOR CLASS.")
print("="*50 + "\n")
