@echo off
title J.A.R.V.I.S. Deployment Protocol
color 0B

echo ======================================================
echo           INITIALIZING J.A.R.V.I.S. DEPLOYMENT
echo ======================================================
echo.

:: PRE-FLIGHT CHECK: Python
echo [SYSTEM] Verifying Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0C
    echo [!] FATAL ERROR: Python is not installed or not in your system PATH.
    echo Please install Python 3.10+ and ensure "Add Python to PATH" is checked during installation.
    pause
    exit
)

:: PRE-FLIGHT CHECK: Ollama (For Vision)
set OLLAMA_INSTALLED=1
echo [SYSTEM] Verifying local AI models (Ollama)...
ollama --version >nul 2>&1
if %errorlevel% neq 0 (
    color 0E
    echo [!] WARNING: Ollama is not installed on this machine. 
    echo The Vision protocols (screen analysis) will be disabled, but core functions will work.
    set OLLAMA_INSTALLED=0
)

:: 1. Create Virtual Environment
echo.
echo [1/5] Securing Neural Environment...
if exist env (
    echo       - Environment already exists. Skipping creation.
) else (
    python -m venv env
    echo       - Virtual environment created successfully.
)

:: 2. Activate Environment and Upgrade Pip
echo [2/5] Activating Environment...
call .\env\Scripts\activate
python -m pip install --upgrade pip >nul 2>&1

:: 3. Install Dependencies
echo [3/5] Installing Neural Pathways (This may take a few minutes)...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    color 0C
    echo [!] ERROR: Failed to install dependencies. Check your internet connection.
    pause
    exit
)

:: 4. Pull Vision Model via Ollama
echo [4/5] Syncing Local Visual Cortex...
if %OLLAMA_INSTALLED%==1 (
    echo       - Downloading Moondream vision model...
    ollama pull moondream
) else (
    echo       - Skipping vision sync (Ollama not found).
)

:: 5. Finalizing Folders (Including Phase 3 Architecture)
echo [5/5] Finalizing Secure Directories...
if not exist "Data" mkdir "Data"
if not exist "Frontend\Files" mkdir "Frontend\Files"
if not exist "Workspace\Code" mkdir "Workspace\Code"
if not exist "Workspace\Presentations" mkdir "Workspace\Presentations"
if not exist "Workspace\Databases" mkdir "Workspace\Databases"
if not exist "Workspace\Excel" mkdir "Workspace\Excel"

color 0A
echo.
echo ======================================================
echo           DEPLOYMENT COMPLETE, SIR.
echo ======================================================
echo.

if exist test.py (
    echo Launching System Diagnostic...
    python test.py
    echo.
)

color 0B
echo Initialization finished. Press any key to boot the Main Interface...
pause >nul

:: Clear screen and launch GUI
cls
echo Booting J.A.R.V.I.S...
python main.py
pause