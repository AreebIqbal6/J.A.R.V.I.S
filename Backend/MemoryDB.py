import os
import shutil
import numpy as np

# ===========================================
# --- WINERROR 1314 SYMLINK BYPASS ---
# ===========================================
_orig_symlink = os.symlink
def _safe_symlink(src, dst, target_is_directory=False, **kwargs):
    try:
        _orig_symlink(src, dst, target_is_directory=target_is_directory, **kwargs)
    except OSError as e:
        if getattr(e, 'winerror', None) == 1314:
            src_str = str(src)
            dst_str = str(dst)
            if os.path.isdir(src_str):
                shutil.copytree(src_str, dst_str)
            else:
                shutil.copy2(src_str, dst_str)
        else:
            raise
os.symlink = _safe_symlink

import sounddevice as sd
import torch
import torchaudio
import warnings
import huggingface_hub

# ===========================================
# --- NEURAL BYPASS PROTOCOLS ---
# ===========================================
if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: ["soundfile", "ffmpeg"]

_original_download = huggingface_hub.hf_hub_download
def _patched_download(*args, **kwargs):
    kwargs.pop("use_auth_token", None)
    try:
        return _original_download(*args, **kwargs)
    except Exception as e:
        filename = kwargs.get("filename") or (args[1] if len(args) > 1 else "")
        if "custom.py" in str(filename):
            dummy_path = os.path.abspath(os.path.join("tmp_speechbrain", "custom.py"))
            os.makedirs(os.path.dirname(dummy_path), exist_ok=True)
            with open(dummy_path, "w") as f: pass
            return dummy_path
        raise
huggingface_hub.hf_hub_download = _patched_download

# Suppress warnings
warnings.filterwarnings("ignore")
from speechbrain.inference.speaker import EncoderClassifier

# Safely locate the VoicePrints folder
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VOICE_DIR = os.path.join(BASE_DIR, "Data", "VoicePrints")
os.makedirs(VOICE_DIR, exist_ok=True)

print("\n=======================================================")
print("      J.A.R.V.I.S. VOCAL SIGNATURE ENROLLMENT")
print("=======================================================")
print("\n[SYSTEM] Loading Neural Acoustic Model...")

try:
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb", 
        savedir="tmp_speechbrain"
    )
except Exception as e:
    print(f"\n[!] Model Loading Error: {e}")
    exit()

def enroll_user():
    print("\n--- NEW ENROLLMENT ---")
    name = input("Enter the name of the VIP to enroll (e.g., Areeb, Fariya, Saad): ").strip().title()
    
    if not name:
        print("[!] Error: Name cannot be empty.")
        return

    duration = 5  # Seconds to record
    fs = 16000    # 16kHz sample rate
    
    print(f"\n>> PREPARE TO SPEAK: Please have {name} talk clearly into the microphone.")
    input(">> Press ENTER to begin the 5-second recording...")
    
    print("\n[REC] RECORDING IN PROGRESS - SPEAK NOW...")
    try:
        # Record audio as a raw numpy array
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='float32')
        sd.wait()
        print("[REC] RECORDING COMPLETE.")
    except Exception as e:
        print(f"\n[!] Microphone Error: {e}")
        return

    print("\n[SYSTEM] Extracting 192-dimensional vocal signature...")
    
    try:
        # --- DIRECT TENSOR INJECTION (Bypasses TorchCodec Error) ---
        # Convert the raw microphone data directly into a PyTorch shape: (1, frames)
        signal = torch.from_numpy(recording).squeeze(1).unsqueeze(0)
        
        # Pass it through the neural network
        embeddings = classifier.encode_batch(signal)
        
        # Save the tensor securely into the Voice Vault
        save_path = os.path.join(VOICE_DIR, f"{name}.pt")
        torch.save(embeddings, save_path)
        
        print(f"\n>> [SUCCESS]: Vocal signature for {name} has been permanently saved to the vault!")
        print(f">> File: Data/VoicePrints/{name}.pt")
        
    except Exception as e:
        print(f"\n[!] FATAL ERROR during extraction: {e}")

if __name__ == "__main__":
    while True:
        enroll_user()
        
        cont = input("\nWould you like to enroll another VIP? (y/n): ").strip().lower()
        if cont != 'y':
            print("\n[SYSTEM] Shutting down enrollment interface. Vault secured.")
            break