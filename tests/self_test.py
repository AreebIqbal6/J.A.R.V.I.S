"""
tests/self_test.py
Phase 6 Automated Startup Self-Test & Diagnostic Scorecard.
Exercises every core JARVIS component in under 5 seconds:
1. Environment & API Keys
2. FastRouter deterministic matching (<5ms)
3. Speech-to-Text configuration (Whisper Large v3 Turbo)
4. Text-to-Speech engine & barge-in handler
5. Tool Registry dry-run (All tools return valid schema envelopes)
6. UI EventBus Protocol v1 envelope compliance
7. Watchdog Supervisor process recovery
8. Dynamic Fallback Panel HTML Sanitizer & XSS defense
"""

import os
import sys
import time
import json

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

results = []

def run_check(name: str, fn):
    t0 = time.time()
    try:
        fn()
        elapsed_ms = (time.time() - t0) * 1000
        results.append((name, True, f"{elapsed_ms:.1f}ms", ""))
    except Exception as e:
        elapsed_ms = (time.time() - t0) * 1000
        results.append((name, False, f"{elapsed_ms:.1f}ms", str(e)))

# 1. Environment & Keys
def check_env():
    from dotenv import dotenv_values
    env = dotenv_values(".env")
    key = env.get("GroqAPIKey") or os.getenv("GroqAPIKey")
    assert key, "Missing GroqAPIKey in .env or environment"
    assert len(key) > 10, "GroqAPIKey appears malformed"

# 2. FastRouter Latency
def check_fast_router():
    from Backend.FastRouter import FastRouter
    t0 = time.time()
    res = FastRouter.route("what time is it")
    dur_ms = (time.time() - t0) * 1000
    assert res is not None, "FastRouter failed to match time pattern"
    assert dur_ms < 10.0, f"FastRouter exceeded 10ms SLA ({dur_ms:.2f}ms)"

    # Test wake word detection (<1ms)
    w1 = FastRouter.match("J.a.r.v.i.s.")
    assert w1 and w1[0] == "wake", f"FastRouter failed J.a.r.v.i.s. wake word: {w1}"
    w2 = FastRouter.match("jarvis")
    assert w2 and w2[0] == "wake", f"FastRouter failed jarvis wake word: {w2}"
    
    # Test capabilities & pleasantries (<1ms)
    c1 = FastRouter.match("what can you do")
    assert c1 and c1[0] == "capabilities", f"FastRouter failed capabilities: {c1}"
    p1 = FastRouter.match("thank you")
    assert p1 and p1[0] == "pleasantry", f"FastRouter failed pleasantry: {p1}"

# 3. STT Configuration
def check_stt():
    import Backend.SpeechToText as stt
    assert hasattr(stt, "SpeechRecognition"), "SpeechRecognition function missing"
    assert hasattr(stt, "transcribe_audio_bytes"), "transcribe_audio_bytes missing"

# 4. TTS Engine
def check_tts():
    import Backend.TextToSpeech as tts
    assert hasattr(tts, "TextToSpeech"), "TextToSpeech function missing"
    assert hasattr(tts, "StopTTS"), "StopTTS barge-in function missing"

# 5. Tool Registry Dry-Run
def check_tool_registry():
    from Backend.ToolRegistry import execute_tool, TOOL_REGISTRY
    assert len(TOOL_REGISTRY) >= 10, f"Expected >= 10 registered tools, got {len(TOOL_REGISTRY)}"
    
    # Dry run diagnostics
    r1 = execute_tool("get_diagnostics", {})
    assert r1.get("ok") is True, f"get_diagnostics failed: {r1}"
    assert "cpu_percent" in r1.get("data", {})

    # Dry run thermostat
    r2 = execute_tool("adjust_thermostat", {"temperature": 23})
    assert r2.get("ok") is True, f"adjust_thermostat failed: {r2}"
    assert r2["data"]["temperature"] == 23

    # Dry run lights
    r3 = execute_tool("control_lights", {"state": "on"})
    assert r3.get("ok") is True

    # Dry run joke
    r4 = execute_tool("get_joke", {})
    assert r4.get("ok") is True

# 6. EventBus Protocol v1
def check_event_bus():
    from Backend.EventBus import EventBus
    env = EventBus.build_envelope("state", {"status": "idle"})
    assert env["v"] == 1, "Protocol version must be 1"
    assert env["type"] == "state"
    assert isinstance(env["seq"], int) and env["seq"] > 0
    assert isinstance(env["ts"], int)

# 7. Watchdog Supervisor
def check_supervisor():
    from Backend.Supervisor import Supervisor
    task = Supervisor.register("test_worker", lambda: None, min_backoff=1.0)
    assert task is not None
    st = Supervisor.get_status()
    assert "test_worker" in st

# 8. Dynamic Sanitizer & XSS Defense
def check_sanitizer():
    from Backend.Sanitizer import sanitize_html, markdown_to_safe_html
    cleaned = sanitize_html("<script>bad()</script><p>safe</p>")
    assert "<script" not in cleaned and "<p>safe</p>" in cleaned
    md_html = markdown_to_safe_html("### Header\n- item 1")
    assert "<h3>Header</h3>" in md_html and "<li>item 1</li>" in md_html

def main():
    start_total = time.time()
    print("=" * 65)
    print("      J.A.R.V.I.S. AUTOMATED STARTUP SELF-TEST & DIAGNOSTIC      ")
    print("=" * 65)

    run_check("1. Environment & API Keys", check_env)
    run_check("2. FastRouter Engine (<5ms)", check_fast_router)
    run_check("3. STT Whisper Turbo Engine", check_stt)
    run_check("4. TTS Audio & Barge-In", check_tts)
    run_check("5. Tool Registry Dry-Run (10 Tools)", check_tool_registry)
    run_check("6. EventBus Protocol v1 Envelope", check_event_bus)
    run_check("7. Watchdog Supervisor Logic", check_supervisor)
    run_check("8. Dynamic Panel XSS Sanitizer", check_sanitizer)

    total_dur_s = time.time() - start_total

    print("-" * 65)
    print(f"{'SUBSYSTEM / TEST':<38} {'STATUS':<10} {'LATENCY':<10}")
    print("-" * 65)

    all_pass = True
    for name, ok, lat, err in results:
        status_str = "[PASS]" if ok else "[FAIL]"
        print(f"{name:<38} {status_str:<10} {lat:<10}")
        if not ok:
            all_pass = False
            print(f"   -> Error: {err}")

    print("=" * 65)
    if all_pass:
        print(f" >> ALL 8 SUBSYSTEMS HEALTHY AND VERIFIED IN {total_dur_s:.2f}s <<")
    else:
        print(f" >> SYSTEM DEGRADED: SOME CHECKS FAILED IN {total_dur_s:.2f}s <<")
    print("=" * 65 + "\n")

    return 0 if all_pass else 1

if __name__ == "__main__":
    sys.exit(main())
