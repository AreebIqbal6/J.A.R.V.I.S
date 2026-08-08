import os
import re
import traceback
from groq import Groq
from dotenv import dotenv_values
from Backend.Sandbox import PythonSandbox

# Load Environment
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
env_vars = dotenv_values(os.path.join(BASE_DIR, ".env"))

GroqAPIKey = env_vars.get("GroqAPIKey")
Username = env_vars.get("Username", "User")
Assistantname = env_vars.get("Assistantname", "Jarvis")

class JarvisAgent:
    def __init__(self):
        self.client = Groq(api_key=GroqAPIKey)
        self.sandbox = PythonSandbox()
        self.max_loops = 5 # Prevents infinite thinking loops

        self.system_prompt = (
            f"You are {Assistantname}, the highly advanced Phase 3 Autonomous Agent for {Username}.\n"
            "You have access to a secure Python execution sandbox and a Long-Term Memory database.\n"
            f"The user ({Username}) is Pakistani. Address him respectfully as 'sir' at all times.\n\n"
            "[YOUR CAPABILITIES & DIRECTIVES]:\n"
            "1. To write and execute code to solve a problem, format it EXACTLY like this:\n"
            "```python\n"
            "# your code here\n"
            "print(result)\n"
            "```\n"
            "2. If you output Python code, the system will pause, run it, and feed the terminal output back to you.\n"
            "3. Analyze the output. If there is an error, rewrite the code to fix it.\n"
            "4. Once you have the final answer, output your response normally WITHOUT the python markdown block. Speak concisely and professionally.\n"
            "5. Think step-by-step. If asked a complex math or logic problem, write a Python script to verify your logic before answering."
        )

    def extract_code(self, text: str):
        """Finds Python code blocks in the LLM's response."""
        match = re.search(r'```python\s*(.*?)\s*```', text, re.DOTALL)
        if match:
            return match.group(1)
        return None

    def run(self, user_prompt: str) -> str:
        try:
            # --- PHASE 3 MEMORY INTEGRATION (FIXED) ---
            try:
                from Backend.memory import Recall, Remember
                has_memory = True
            except ImportError:
                has_memory = False
                print("!! memory module not found. Running Sandbox without memory.")

            print("--- [JARVIS AGENT]: Analyzing Logic & Searching Memory... ---")
            
            recalled_context = ""
            if has_memory:
                memory_string = Recall(user_prompt)
                if "database is currently empty" not in memory_string.lower():
                    recalled_context = memory_string

            # Initial context with injected memories
            messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "system", "content": f"Memory Context:\n{recalled_context if recalled_context else 'No relevant memories found.'}"},
                {"role": "user", "content": user_prompt}
            ]

            print("--- [JARVIS AGENT]: Thinking... ---")
            
            # The ReAct Loop
            for iteration in range(self.max_loops):
                response = self.client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages,
                    temperature=0.2, 
                    max_tokens=4096  
                )
                
                ai_message = response.choices[0].message.content
                messages.append({"role": "assistant", "content": ai_message})

                # Check if he wrote code
                code_to_run = self.extract_code(ai_message)
                
                if code_to_run:
                    print(f"--- [JARVIS AGENT]: Executing Code (Attempt {iteration + 1})... ---")
                    
                    execution_result = self.sandbox.execute(code_to_run)
                    print(f"--- [SANDBOX OUTPUT]:\n{execution_result}\n---")
                    
                    messages.append({
                        "role": "user", 
                        "content": f"SYSTEM OBSERVATION - Terminal Output:\n{execution_result}\nAnalyze this output. If it failed, fix the code and try again. If it succeeded, provide the final answer to {Username}."
                    })
                else:
                    print("--- [JARVIS AGENT]: Task Complete. ---")
                    
                    # Save the final Agent conclusion to Long-Term Memory
                    if has_memory:
                        Remember(f"Agent Task: {user_prompt} | Agent Concluded: {ai_message}")
                        
                    return ai_message

            return "I apologize, sir, but I exceeded my maximum reasoning loops while trying to solve that."

        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"\n{'-'*50}\n[FATAL THREAD ERROR]\n{error_trace}\n{'-'*50}\n")
            return f"Sir, my Agent Loop encountered an internal error. Check the terminal for details."