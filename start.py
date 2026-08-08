import subprocess
import sys
import os
import signal
import threading

def stream_output(process, prefix):
    """Reads stdout from the process and prefixes it."""
    for line in iter(process.stdout.readline, b''):
        print(f"{prefix} | {line.decode('utf-8', errors='replace').rstrip()}")
    process.stdout.close()

def main():
    # Hardcode the path to JARVIS_V2 since you are running this from J.A.R.V.I.S folder
    base_dir = r"D:\AREEB\JARVIS_V2"
    backend_dir = os.path.join(base_dir, "backend")
    frontend_dir = os.path.join(base_dir, "frontend")
    
    print("Starting JARVIS_V2 Agent OS...")
    
    # Start Backend
    print(f"-> Launching Backend in {backend_dir}")
    backend_proc = subprocess.Popen(
        "uvicorn main:app --reload",
        cwd=backend_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Start Frontend
    print(f"-> Launching Frontend in {frontend_dir}")
    frontend_proc = subprocess.Popen(
        "npm run dev",
        cwd=frontend_dir,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT
    )
    
    # Stream outputs in separate threads so they don't block each other
    t_backend = threading.Thread(target=stream_output, args=(backend_proc, "BACKEND "))
    t_frontend = threading.Thread(target=stream_output, args=(frontend_proc, "FRONTEND"))
    
    t_backend.daemon = True
    t_frontend.daemon = True
    
    t_backend.start()
    t_frontend.start()
    
    def signal_handler(sig, frame):
        print("\nShutting down JARVIS_V2...")
        # On Windows, shell=True spawns a cmd process, so we need to kill the process tree.
        if sys.platform == "win32":
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(backend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            subprocess.call(['taskkill', '/F', '/T', '/PID', str(frontend_proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            backend_proc.terminate()
            frontend_proc.terminate()
        sys.exit(0)
        
    signal.signal(signal.SIGINT, signal_handler)
    
    try:
        backend_proc.wait()
        frontend_proc.wait()
    except KeyboardInterrupt:
        signal_handler(None, None)

if __name__ == "__main__":
    main()
