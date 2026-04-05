import os
from adb_shell.adb_device import AdbDeviceTcp
from adb_shell.auth.sign_pythonrsa import PythonRSASigner
from adb_shell.auth.keygen import keygen
from dotenv import load_dotenv

load_dotenv()
TV_IP = os.getenv("TV_IP")
ADB_KEY_PATH = os.path.join("Data", "adbkey")

def load_adb_keys():
    """Generates and loads RSA keys so the TV trusts Jarvis."""
    os.makedirs("Data", exist_ok=True)
    
    # Generate keys if they don't exist
    if not os.path.exists(ADB_KEY_PATH) or not os.path.exists(ADB_KEY_PATH + '.pub'):
        keygen(ADB_KEY_PATH)
        
    with open(ADB_KEY_PATH, 'r') as f:
        priv = f.read()
    with open(ADB_KEY_PATH + '.pub', 'r') as f:
        pub = f.read()
        
    # The correct class to sign the keys
    return PythonRSASigner(pub=pub, priv=priv)

def ControlTV(command):
    if not TV_IP:
        return "Sir, I don't have the TV's IP address in my environment variables."

    try:
        # Connect to the TV
        device = AdbDeviceTcp(TV_IP, 5555, default_transport_timeout_s=9.)
        keys = load_adb_keys()
        
        # Connect using the RSA keys
        device.connect(rsa_keys=[keys], auth_timeout_s=0.1)

        cmd = command.lower()
        
        # Route the physical commands
        if any(word in cmd for word in ["power", "turn on", "turn off", "turn the tv off", "turn tv off", "shut down", "turn the tv off", "turn tv on"]):
            device.shell("input keyevent 26") # KEYCODE_POWER
            res = "Toggling television power, sir."
        elif "mute" in cmd:
            device.shell("input keyevent 164") # KEYCODE_VOLUME_MUTE
            res = "Muting television."
        elif "volume up" in cmd:
            device.shell("input keyevent 24") # KEYCODE_VOLUME_UP
            res = "Turning the volume up."
        elif "volume down" in cmd:
            device.shell("input keyevent 25") # KEYCODE_VOLUME_DOWN
            res = "Turning the volume down."
        elif "netflix" in cmd:
            device.shell("monkey -p com.netflix.ninja -c android.intent.category.LAUNCHER 1")
            res = "Launching Netflix."
        elif "youtube" in cmd:
            device.shell("monkey -p com.google.android.youtube.tv -c android.intent.category.LAUNCHER 1")
            res = "Launching YouTube."
        elif any(word in cmd for word in ["home", "leave", "exit", "close", "back", "stop"]):
            device.shell("input keyevent 3") # KEYCODE_HOME
            res = "Returning TV to the home screen."
        else:
            res = "I am connected, but I don't recognize that specific remote command."

        device.close()
        return res

    except Exception as e:
        return f"Connection failed. Please ensure the TV is on, connected to Wi-Fi, and ADB Debugging is enabled."