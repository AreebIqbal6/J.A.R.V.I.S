import os
import base64
from time import sleep
import requests

def TakeScreenshot():
    """Captures the current screen and saves it for analysis."""
    import pyautogui
    os.makedirs("Data", exist_ok=True)
    path = os.path.join("Data", "screenshot.jpg")
    screenshot = pyautogui.screenshot()
    # High quality for local Moondream processing
    screenshot.save(path, "JPEG", quality=95) 
    return path

def CaptureWebcam():
    """Captures a frame from the webcam."""
    import cv2
    os.makedirs("Data", exist_ok=True)
    path = os.path.join("Data", "webcam.jpg")
    cam = cv2.VideoCapture(0)
    if not cam.isOpened():
        cam = cv2.VideoCapture(1)
        if not cam.isOpened(): return None
    sleep(0.5) 
    ret, frame = cam.read()
    if ret:
        cv2.imwrite(path, frame)
    cam.release()
    return path if ret else None

def VisionAnalysis(image_path):
    """
    Local Vision Analysis using Ollama and Moondream.
    Hardened against timeouts and GPU VRAM unloading.
    """
    if not os.path.exists(image_path):
        return "Vision Error: Image file not found, sir."

    try:
        # Convert image to Base64
        with open(image_path, "rb") as image_file:
            base64_image = base64.b64encode(image_file.read()).decode('utf-8')

        print(">> J.A.R.V.I.S: Communicating with local GPU... (Processing visual data)")

        url = "http://localhost:11434/api/generate"
        
        # We use 'keep_alive' to prevent the RX 580 from unloading the model every time
        payload = {
            "model": "moondream",
            "prompt": "What is visible on this screen? Briefly describe the open windows, text, or apps you see.",
            "stream": False,
            "images": [base64_image],
            "keep_alive": "10m",
            "options": {
                "num_predict": 50,
                "temperature": 0.2
            }
        }

        # Increased timeout to 90s to handle the initial VRAM loading lag
        response = requests.post(url, json=payload, timeout=90)
        
        if response.status_code == 200:
            description = response.json().get('response', '').strip()
            
            if not description:
                description = "your desktop interface, though the specifics are slightly obscured"
                
            return f"I see {description}, sir."
        else:
            return f"Ollama Error: Status {response.status_code}. Is the model loaded?"

    except requests.exceptions.Timeout:
        return "Vision Error: The local GPU is still processing. Please try again in a moment, sir."
    except Exception as e:
        return f"Local Vision Error: {e}. Please ensure Ollama is active."