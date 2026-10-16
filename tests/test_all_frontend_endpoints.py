import re
import urllib.request
import json

with open('jarvis_ui.html', 'r', encoding='utf-8') as f:
    ui_html = f.read()

with open('Frontend/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

# Extract all fetch calls
ui_fetches = set(re.findall(r'fetch\([`\'"]([^`\'"]+)[`\'"]', ui_html))
app_fetches = set(re.findall(r'fetch\([`\'"]([^`\'"]+)[`\'"]', app_js))

print("=== ALL UNIQUE FETCH CALLS ===")
print("jarvis_ui.html fetches:", len(ui_fetches))
print("Frontend/app.js fetches:", len(app_fetches))

def test_endpoint(raw_url, method='GET', data=None):
    # Normalize url to localhost:8000
    url = raw_url.replace('${API}', 'http://127.0.0.1:8000/api')
    url = url.replace('${API_BASE}', 'http://127.0.0.1:8000')
    if url.startswith('/'):
        url = 'http://127.0.0.1:8000' + url
    elif not url.startswith('http'):
        url = 'http://127.0.0.1:8000/' + url

    try:
        req = urllib.request.Request(url, method=method)
        if data is not None:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
        with urllib.request.urlopen(req, timeout=8) as resp:
            return resp.status, "OK"
    except urllib.error.HTTPError as e:
        return e.code, e.reason
    except Exception as e:
        return 0, str(e)

print("\n--- TESTING jarvis_ui.html ENDPOINTS ---")
for raw in sorted(ui_fetches):
    is_get = any(p in raw for p in ['now-playing', 'history', 'weather', 'crypto', 'system-stats', 'markets', 'news', 'security-log', 'earth-tracker', 'f1/telemetry', 'devices', 'health', 'status'])
    method = 'GET' if is_get and 'toggle' not in raw and 'halt' not in raw else 'POST'
    if 'chat' in raw and 'history' not in raw:
        method = 'POST'
    payload = {}
    if 'chat' in raw:
        payload = {"text": "hello"}
    if 'code' in raw or 'run' in raw:
        payload = {"code": "print(1)"}
    elif 'play' in raw:
        payload = {"query": "test"}
    elif 'geosleuth' in raw:
        payload = {"query": "London"}
    elif 'scout' in raw:
        payload = {"target": "google.com"}
    elif 'ocr' in raw:
        payload = {"image_b64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}
    elif 'analyze' in raw:
        payload = {"image_b64": ""}

    status, reason = test_endpoint(raw, method=method, data=payload if method == 'POST' else None)
    mark = "[200 OK]" if status in (200, 201) else f"[{status} FAIL: {reason}]"
    print(f"  {mark} {method} {raw}")

print("\n--- TESTING Frontend/app.js ENDPOINTS ---")
for raw in sorted(app_fetches):
    is_post = any(p in raw for p in ['run', 'toggle', 'play', 'control', 'beam', 'analyze', 'ocr', 'geosleuth', 'scout', 'halt', 'thermostat', 'chat', 'think', 'qr']) and 'now-playing' not in raw
    method = 'POST' if is_post else 'GET'
    payload = {}
    if 'chat' in raw or 'think' in raw:
        payload = {"text": "hello"}
    elif 'run' in raw:
        payload = {"code": "print(1)"}
    elif 'play' in raw:
        payload = {"query": "test"}
    elif 'geosleuth' in raw:
        payload = {"query": "London"}
    elif 'scout' in raw:
        payload = {"target": "google.com"}
    elif 'ocr' in raw:
        payload = {"image_b64": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNk+A8AAQUBAScY42YAAAAASUVORK5CYII="}
    elif 'analyze' in raw:
        payload = {"image_b64": ""}
    elif 'control' in raw:
        payload = {"action": "ping"}

    status, reason = test_endpoint(raw, method=method, data=payload if method == 'POST' else None)
    mark = "[200 OK]" if status in (200, 201) else f"[{status} FAIL: {reason}]"
    print(f"  {mark} {method} {raw}")
