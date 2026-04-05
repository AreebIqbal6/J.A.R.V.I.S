import requests
import asyncio
from random import randint
import os
import re
import time
from dotenv import dotenv_values

def GenerateImages(prompt: str):
    """
    Generates an image using a Dual-Engine strategy: 
    Pollinations (Primary) -> Hugging Face Stable Diffusion (Backup).
    """
    safe_prompt = re.sub(r'[^a-zA-Z0-9_\- ]', '', prompt).replace(' ', '')[:30]
    filename = os.path.join("Data", f"{safe_prompt}_{randint(1, 999)}.jpg")
    os.makedirs("Data", exist_ok=True)

    # --- ENGINE 1: POLLINATIONS (Fast & Unrestricted) ---
    seed = randint(1, 1000000)
    # Using 'flux' model often has better uptime than default
    URL = f"https://image.pollinations.ai/prompt/{prompt}?seed={seed}&nologo=true&model=flux" 

    for attempt in range(2):
        try:
            response = requests.get(URL, timeout=(10, 30))
            if response.status_code == 200:
                with open(filename, "wb") as f:
                    f.write(response.content)
                print(f">> [Primary Engine] Success: {filename}")
                return filename
            print(f"!! Primary Engine Status {response.status_code}. Retrying...")
            time.sleep(2)
        except Exception:
            continue

    # --- ENGINE 2: HUGGING FACE (Reliable Backup) ---
    print(">> Switching to Backup Neural Engine (Hugging Face)...")
    env_vars = dotenv_values(".env")
    HF_TOKEN = env_vars.get("HuggingFaceAPIKey")
    
    if not HF_TOKEN:
        print("!! Backup Failed: No Hugging Face API Key found in .env")
        return None

    HF_URL = "https://api-inference.huggingface.co/models/stabilityai/stable-diffusion-2-1"
    headers = {"Authorization": f"Bearer {HF_TOKEN}"}
    
    try:
        # Hugging Face requires a JSON payload
        response = requests.post(HF_URL, headers=headers, json={"inputs": prompt}, timeout=60)
        
        if response.status_code == 200:
            with open(filename, "wb") as f:
                f.write(response.content)
            print(f">> [Backup Engine] Success: {filename}")
            return filename
        elif response.status_code == 503:
            print("!! Backup Engine is loading. Please wait 20s and try again, sir.")
    except Exception as e:
        print(f"!! All Engines Offline: {e}")

    return None

def ListenForPrompts():
    asyncio.run(MainLoop())

async def MainLoop():
    file_path = os.path.join("Frontend", "Files", "ImageGeneration.data")
    while True:
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            if not os.path.exists(file_path):
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write("False,False")

            with open(file_path, "r", encoding="utf-8") as f:
                data = f.read().strip()
            
            if data and "," in data:
                parts = data.rsplit(",", 1)
                prompt_text, status = parts[0], parts[1]
                
                if status == "True":
                    print(f">> J.A.R.V.I.S: Creating visual for '{prompt_text}'...")
                    await asyncio.to_thread(GenerateImages, prompt_text)
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(f"{prompt_text},False")
            
            await asyncio.sleep(1)
        except Exception:
            await asyncio.sleep(2)

if __name__ == "__main__":
    ListenForPrompts()