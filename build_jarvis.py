import os
import shutil
import PyInstaller.__main__
import site
import sys
import ast

print("--- [1/4] SCANNING PROJECT DNA ---")

project_dir = os.getcwd()
found_imports = set()

# 1. AUTO-SCANNER: Parses every .py file to find used libraries
for root, dirs, files in os.walk(project_dir):
    if any(skip in root for skip in ['env', '.venv', 'dist', 'build', '__pycache__']):
        continue
    for file in files:
        if file.endswith('.py'):
            filepath = os.path.join(root, file)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    tree = ast.parse(f.read(), filename=filepath)
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            found_imports.add(alias.name.split('.')[0])
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            found_imports.add(node.module.split('.')[0])
            except Exception as e:
                print(f"Skipped {file}: {e}")

# 2. FILTERING: Remove built-ins and local folders
stdlib = sys.stdlib_module_names if hasattr(sys, 'stdlib_module_names') else set()
local_folders = {d for d in os.listdir(project_dir) if os.path.isdir(os.path.join(project_dir, d))}
external_libs = found_imports - set(stdlib) - local_folders - {'Main'}

# 3. MANUAL OVERRIDE: Forcing libraries that use dynamic loading
guaranteed_libs = {
    'groq', 'cohere', 'google.generativeai', 'requests', 'dotenv', 'keyboard', 
    'pyautogui', 'pyperclip', 'pyaudio', 'speech_recognition', 'bytez', 'cv2', 
    'screen_brightness_control', 'psutil', 'AppOpener', 'pywhatkit', 'yfinance', 
    'wikipedia', 'googlesearch', 'duckduckgo_search', 'bs4', 'qrcode', 'PIL', 
    'PyQt5', 'pygame', 'edge_tts', 'mtranslate'
}

all_libs_to_pack = external_libs.union(guaranteed_libs)
print(f"--> Strategy: Forcing {len(all_libs_to_pack)} libraries into the binary.")

# 4. PREPARE BUILD ARGUMENTS
build_args = [
    'Main.py',
    '--noconsole',
    '--onedir',
    '--name=JARVIS',
    '--icon=Frontend/Graphics/Jarvis.ico',
    '--add-data=Frontend;Frontend',
    '--add-data=Data;Data',
    '--add-data=.env;.',
    '--clean',
    '-y'
]

for lib in all_libs_to_pack:
    if lib: build_args.append(f'--hidden-import={lib}')

print("\n--- [2/4] EXECUTING PYINSTALLER ---")
PyInstaller.__main__.run(build_args)

print("\n--- [3/4] PATCHING QT5 BINARIES ---")

# Fix for the dreaded 'Qt Platform Plugin' error
site_packages_dirs = site.getsitepackages()
qt_bin_source = None

for sp in site_packages_dirs:
    candidate = os.path.join(sp, "PyQt5", "Qt5", "bin")
    if os.path.exists(candidate):
        qt_bin_source = candidate
        break

if qt_bin_source:
    dist_internal = os.path.join(os.getcwd(), "dist", "JARVIS", "_internal")
    target_bin = os.path.join(dist_internal, "PyQt5", "Qt5", "bin")
    os.makedirs(target_bin, exist_ok=True)
    shutil.copytree(qt_bin_source, target_bin, dirs_exist_ok=True)
    
    # Copy essential DLLs to root for extra stability
    exe_folder = os.path.join(os.getcwd(), "dist", "JARVIS")
    for dll in ["Qt5Core.dll", "Qt5Gui.dll", "Qt5Widgets.dll"]:
        src = os.path.join(qt_bin_source, dll)
        if os.path.exists(src): shutil.copy2(src, exe_folder)
            
    print("\n--- [4/4] SUCCESS: J.A.R.V.I.S STANDALONE READY ---")
else:
    print("\n[!] WARNING: PyQt5 binaries not found. GUI might require manual DLL placement.")