@echo off
cd /d "%~dp0"
title J.A.R.V.I.S. Mark IV Core
echo ========================================
echo       LAUNCHING J.A.R.V.I.S. A.I.
echo ========================================

powershell -NoProfile -ExecutionPolicy Bypass -Command "Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }"

call .venv\Scripts\activate.bat
python Main.py
pause
