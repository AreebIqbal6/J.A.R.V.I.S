import asyncio
import os
from dotenv import dotenv_values
from rich.console import Console
from rich.panel import Panel

# --- CORRECTED IMPORTS ---
from Backend.Model import FirstLayerDMM
from Backend.RealtimeSearchEngine import RealtimeSearchEngine
from Backend.Automation import Automation
from Backend.SpeechToText import SpeechRecognition  
from Backend.TextToSpeech import TextToSpeech      
from Backend.Chatbot import ChatBot

# Setup Console
console = Console()
env_vars = dotenv_values(".env")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Jarvis")

# --- ASYNC WRAPPER FOR AUTOMATION ---
async def RunAutomation(tasks):
    async for result in Automation(tasks):
        if result and isinstance(result, str):
            # Added TTS so he actually speaks his automation feedback
            console.print(f"[green]{Assistantname}:[/green] {result}")
            TextToSpeech(result)

def MainExecution():
    console.print(Panel(f"[bold green]SYSTEM ONLINE[/bold green]\nWelcome back, sir.", title=f"{Assistantname} AI"))
    TextToSpeech(f"System online. Welcome back, sir.")

    while True:
        # 1. LISTEN
        try:
            Query = SpeechRecognition()
            if not Query: continue # Skip if silence
        except Exception as e:
            console.print(f"[red]Mic Error: {e}[/red]")
            continue
            
        console.print(f"[cyan]{Username}:[/cyan] {Query}")

        # 2. THINK (Decision Making)
        try:
            Decision = FirstLayerDMM(Query)
        except Exception as e:
            console.print(f"[red]Decision Error: {e}[/red]")
            Decision = [f"general {Query}"]

        # 3. ACT
        GeneralResponse = ""
        AutomationTasks = []

        for task in Decision:
            task = str(task).strip()
            
            # CASE A: General Chat
            # Fixed the .replace() bug so it doesn't delete words from the middle of sentences
            if task.startswith("general "):
                clean_query = task.removeprefix("general ").strip()
                GeneralResponse = ChatBot(clean_query)
            
            # CASE B: Realtime Search
            elif task.startswith("realtime "):
                clean_query = task.removeprefix("realtime ").strip()
                GeneralResponse = RealtimeSearchEngine(clean_query)
                
            # CASE C: Exit
            elif "exit" in task:
                GeneralResponse = "Shutting down systems. Goodbye, sir."
                console.print(f"[green]{Assistantname}:[/green] {GeneralResponse}")
                TextToSpeech(GeneralResponse)
                os._exit(0)
                
            # CASE D: Automation
            else:
                AutomationTasks.append(task)

        # 4. EXECUTE RESPONSES
        # Speak response first
        if GeneralResponse:
            console.print(f"[green]{Assistantname}:[/green] {GeneralResponse}")
            TextToSpeech(GeneralResponse)

        # Run Automation asynchronously
        if AutomationTasks:
            console.print(f"[yellow]Executing Tasks:[/yellow] {AutomationTasks}")
            try:
                asyncio.run(RunAutomation(AutomationTasks))
            except Exception as e:
                console.print(f"[red]Automation Error: {e}[/red]")

if __name__ == "__main__":
    MainExecution()