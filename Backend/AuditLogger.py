import os
import json
import hashlib
from datetime import datetime

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUDIT_LOG_PATH = os.path.join(ROOT_DIR, "Data", "audit.jsonl")
os.makedirs(os.path.join(ROOT_DIR, "Data"), exist_ok=True)

def record_audit(operator: str, action: str, target: str, status: str = "SUCCESS", details: dict = None, latency_ms: float = 0.0):
    entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "operator": operator,
        "action": action,
        "target": target,
        "status": status,
        "latency_ms": round(latency_ms, 2),
        "details": details or {}
    }
    raw_str = json.dumps(entry, sort_keys=True)
    entry["integrity_sha256"] = hashlib.sha256(raw_str.encode("utf-8")).hexdigest()
    
    try:
        with open(AUDIT_LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")
    except Exception as e:
        print(f"Audit log write failure: {e}")
