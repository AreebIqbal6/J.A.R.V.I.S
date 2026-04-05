import os
import subprocess

# --- SECURE WORKSPACE SETUP ---
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.join(BASE_DIR, "Data", "Workspace")
os.makedirs(WORKSPACE_DIR, exist_ok=True)

class PythonSandbox:
    def __init__(self):
        self.workspace = WORKSPACE_DIR

    def execute(self, code: str, timeout: int = 15) -> str:
        """Executes Python code in the isolated workspace and returns the output/errors."""
        
        # 1. Clean the code
        code = code.strip()
        if code.startswith("```python"): code = code[9:]
        if code.startswith("```"): code = code[3:]
        if code.endswith("```"): code = code[:-3]
        code = code.strip()

        # 2. Write the AI's code to a temporary script file
        script_path = os.path.join(self.workspace, "jarvis_script.py")
        with open(script_path, "w", encoding="utf-8") as f:
            f.write(code)

        # 3. Execute the script safely capturing all terminal output
        try:
            print("--- [SANDBOX]: Executing J.A.R.V.I.S. Code... ---")
            result = subprocess.run(
                ["python", script_path],
                capture_output=True,
                text=True,
                timeout=timeout,
                cwd=self.workspace # Forces execution inside the secure folder
            )
            
            # 4. Return the results back to his brain
            if result.returncode == 0:
                output = result.stdout.strip()
                return f"[SUCCESS]\nOutput:\n{output}" if output else "[SUCCESS] (Code ran with no print output)"
            else:
                error = result.stderr.strip()
                return f"[FAILED]\nError Traceback:\n{error}"
                
        except subprocess.TimeoutExpired:
            return f"[FAILED] Script timed out after {timeout} seconds (Infinite loop detected)."
        except Exception as e:
            return f"[CRITICAL ERROR] System Failure: {e}"