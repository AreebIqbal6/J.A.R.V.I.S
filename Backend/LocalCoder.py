import os
import re
import subprocess
from groq import Groq
from dotenv import dotenv_values

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")

def GenerateLocalCode(prompt, filename="jarvis_script.py"):
    """Hooks into Groq Cloud to write and save code instantly, bypassing local hardware limits."""
    save_dir = os.path.join(os.getcwd(), "Workspace", "Code")
    os.makedirs(save_dir, exist_ok=True)
    file_path = os.path.join(save_dir, filename)

    print(">> [CODING ENGINE]: Bypassing local hardware. Routing to Groq Cloud...")

    if not GroqAPIKey:
        return "Sir, the Groq API key is missing. I cannot access the cloud coding engine."

    try:
        client = Groq(api_key=GroqAPIKey)
        system_prompt = (
            "You are an elite, expert Python developer. "
            "The user will give you a task. You must output ONLY raw, valid, executable Python code. "
            "Do NOT output markdown formatting, do NOT write explanations, and do NOT use ```python tags. "
            "Start directly with the import statements."
        )

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile", 
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            temperature=0.2
        )

        raw_code = completion.choices[0].message.content.strip()
        clean_code = re.sub(r"^```[a-zA-Z]*\n|^```\n|```$", "", raw_code, flags=re.MULTILINE).strip()

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(clean_code)

        return f"Code successfully compiled and saved to {file_path}, sir."

    except Exception as e:
        return f"Cloud coding engine offline. Error: {e}"


def EngageOpenClaw(prompt):
    """Bridges Python J.A.R.V.I.S. to the Node.js OpenClaw agent in a separate terminal."""
    print(f">> [OPENCLAW]: Deploying autonomous coding agent for task...")
    
    claw_dir = os.path.join(os.getcwd(), "openclaw")
    
    if not os.path.exists(claw_dir):
        return "Sir, the OpenClaw directory is missing from the root folder. I cannot deploy the agent."

    try:
        # Spawns a visible CMD window so you can interact with OpenClaw's [y/N] prompts
        cmd = f'start cmd.exe /k "cd {claw_dir} && npx @openclaw/cli "{prompt}""'
        subprocess.Popen(cmd, shell=True)
        return "OpenClaw sub-agent has been deployed in a separate window, Sir. It is handling the codebase now."
        
    except Exception as e:
        return f"Failed to initialize the OpenClaw bridge. Error: {e}"