import os
import shutil
import warnings
import huggingface_hub

# ===========================================
# 1. THE WINERROR SHIELD 
# ===========================================
_orig_symlink = os.symlink
def _safe_symlink(src, dst, target_is_directory=False, **kwargs):
    try:
        _orig_symlink(src, dst, target_is_directory=target_is_directory, **kwargs)
    except OSError as e:
        win_err = getattr(e, 'winerror', None)
        if win_err in (1314, 87, 183):  
            src_str = str(src)
            dst_str = str(dst)
            if src_str in (".", "..") or os.path.abspath(src_str) == os.path.abspath(dst_str):
                return
            try:
                if os.path.isdir(src_str): shutil.copytree(src_str, dst_str, dirs_exist_ok=True)
                else: shutil.copy2(src_str, dst_str)
            except: pass 
        else: raise
os.symlink = _safe_symlink

# ===========================================
# 2. HUGGINGFACE BYPASS
# ===========================================
_original_download = huggingface_hub.hf_hub_download
def _patched_download(*args, **kwargs):
    kwargs.pop("use_auth_token", None)
    try: return _original_download(*args, **kwargs)
    except Exception as e:
        filename = kwargs.get("filename") or (args[1] if len(args) > 1 else "")
        if "custom.py" in str(filename):
            dummy_path = os.path.abspath(os.path.join("tmp_speechbrain", "custom.py"))
            os.makedirs(os.path.dirname(dummy_path), exist_ok=True)
            with open(dummy_path, "w") as f: pass
            return dummy_path
        raise
huggingface_hub.hf_hub_download = _patched_download

# ===========================================
# 3. HEAVY MATH LIBRARIES & BIOMETRICS
# ===========================================
import torch
import torchaudio

# --- CRITICAL FIX: THE MONKEY PATCH MUST HAPPEN BEFORE SPEECHBRAIN IMPORTS ---
if not hasattr(torchaudio, "list_audio_backends"):
    torchaudio.list_audio_backends = lambda: ["soundfile", "ffmpeg"]

import torchaudio.functional as F
import numpy as np
import soundfile as sf  
from speechbrain.inference.speaker import EncoderClassifier

warnings.filterwarnings("ignore")

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOICE_DIR = os.path.join(BASE_DIR, "Data", "VoicePrints")

class VoiceAuthenticator:
    def __init__(self):
        print("\n[SYSTEM] Booting Biometric Security...")
        self.classifier = EncoderClassifier.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb", 
            savedir="tmp_speechbrain"
        )
        self.known_profiles = {}
        self.load_vault()

    def load_vault(self):
        if not os.path.exists(VOICE_DIR): return
        for file in os.listdir(VOICE_DIR):
            if file.endswith(".pt"):
                name = file.replace(".pt", "")
                path = os.path.join(VOICE_DIR, file)
                self.known_profiles[name] = torch.load(path)
        print(f">> [VOICE AUTH]: Loaded {len(self.known_profiles)} VIP signatures.")

    def identify_speaker_from_temp_file(self):
        if not self.known_profiles: return "Unknown", 0.0

        temp_wav = os.path.join(BASE_DIR, "temp_voice.wav")
        if not os.path.exists(temp_wav):
            print("!! [VOICE AUTH]: temp_voice.wav was missing! Check STT deletion.")
            return "Unknown", 0.0 

        try:
            # Read audio data using soundfile (Bypasses TorchCodec errors!)
            audio_data, fs_audio = sf.read(temp_wav)
            signal = torch.from_numpy(audio_data).float()
            if signal.ndim > 1: signal = signal.mean(dim=1) 
            signal = signal.unsqueeze(0)
            
            # --- CRITICAL FIX: RESAMPLE TO 16000Hz ---
            if fs_audio != 16000:
                signal = F.resample(signal, fs_audio, 16000)
            
            # Extract embedding
            current_emb = self.classifier.encode_batch(signal)
            
            best_match = "Unknown"
            highest_score = -1.0 # Allow negative scores to show up in debug
            threshold = 0.25 # Standard SpeechBrain Match Threshold

            for name, saved_emb in self.known_profiles.items():
                emb1 = current_emb.squeeze()
                emb2 = saved_emb.squeeze()
                score = torch.nn.functional.cosine_similarity(emb1, emb2, dim=0).item()
                
                # Print the exact math to the terminal so we can see it working
                print(f"   [DEBUG] Biometric Match Score for {name}: {score:.4f}")
                
                if score > highest_score:
                    highest_score = score
                    best_match = name

            # Clean up the temp file now that we have the identity
            if os.path.exists(temp_wav): os.remove(temp_wav)

            if highest_score > threshold:
                return best_match, highest_score
            else:
                return "Unknown", highest_score

        except Exception as e:
            print(f"!! [VOICE AUTH ERROR]: {e}")
            if os.path.exists(temp_wav):
                try: os.remove(temp_wav)
                except: pass
            return "Error", 0.0