import webview
import subprocess
import time
import sys
import os

def start():
    if getattr(sys, 'frozen', False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(os.path.abspath(__file__))

    # The Server.py is run using the virtual environment python
    python_exe = os.path.join(base_dir, "env", "Scripts", "python.exe")
    server_script = os.path.join(base_dir, "Backend", "Server.py")
    
    # Start FastApi backend hidden
    # CREATE_NO_WINDOW = 0x08000000 ensures the python server terminal doesn't pop up
    server_process = subprocess.Popen(
        [python_exe, server_script], 
        cwd=base_dir, 
        creationflags=0x08000000
    )
    
    # Wait for Uvicorn to boot up
    time.sleep(3)
    
    # Launch Desktop GUI (Fullscreen, Frameless)
    window = webview.create_window(
        "J.A.R.V.I.S. Mark IV", 
        "http://127.0.0.1:8000",
        fullscreen=True,
        frameless=True,
        background_color='#000000'
    )
    
    webview.start()
    
    # When the user hits alt-f4 or closes the GUI, kill the backend server
    server_process.terminate()

if __name__ == '__main__':
    start()
