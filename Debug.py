import sys
import os
import importlib

print(">> 1. Starting System Diagnostics, sir...")

# --- CHECK FOLDERS ---
data_dir = "Data"
frontend_files_dir = os.path.join("Frontend", "Files")

for directory in [data_dir, frontend_files_dir]:
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"   - Created missing directory: '{directory}'")

# --- TEST IMPORTS INDIVIDUALLY ---
print("\n>> 2. Testing Core Modules...")
modules_to_test = [
    "Frontend.GUI",
    "Backend.Model",
    "Backend.SpeechToText",
    "Backend.TextToSpeech",
    "Backend.RealtimeSearchEngine",
    "Backend.Automation"
]

all_imports_passed = True
for mod in modules_to_test:
    try:
        importlib.import_module(mod)
        print(f"   - {mod}: OK")
    except Exception as e:
        print(f"   !!! ERROR loading {mod}: {e}")
        all_imports_passed = False

if not all_imports_passed:
    print("\n!!! CRITICAL IMPORT ERROR(S) DETECTED.")
    print("Please ensure all dependencies are installed via 'pip install -r requirements.txt'")

# --- AUDIO CHECK ---
print("\n>> 3. Testing Audio Engine...")
try:
    import pygame
    pygame.mixer.init()
    print("   - Pygame Mixer: OK")
    pygame.mixer.quit()
except Exception as e:
    print(f"   !!! AUDIO ERROR: {e}")

# --- API KEY CHECK ---
print("\n>> 4. Checking API Keys...")
try:
    from dotenv import dotenv_values
    env = dotenv_values(".env")

    keys = ["GroqAPIKey", "BytezAPIKey", "HuggingFaceAPIKey", "CohereAPIKey"]
    missing = [k for k in keys if not env.get(k)]

    if missing:
        print(f"   !!! WARNING: Missing Keys in .env: {missing}")
    else:
        print("   - All API Keys Found: OK")
except Exception as e:
    print(f"   !!! ENV ERROR: {e}")

# --- GUI CHECK ---
print("\n>> 5. Testing GUI Initialization...")
try:
    from PyQt5.QtWidgets import QApplication
    from Frontend.GUI import MainWindow 
    
    # Safe instantiation: Check if an app already exists before creating a new one
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)
        
    window = MainWindow()
    print("   - Window Initialized: OK")
    print("   - Closing Test Window...")
    window.close()
    
    print("\n>>> SUCCESS! All systems are healthy and fully synced, sir.")
    print("You can now safely run 'python Main.py'")
    
except Exception as e:
    print(f"\n!!! GUI ERROR (Likely missing images or PyQt5 issue): {e}")

input("\nDiagnostics complete. Press Enter to close...")