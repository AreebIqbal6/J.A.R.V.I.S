import urllib.request
import json
import socket

def test(url, method='GET', data=None):
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
        with urllib.request.urlopen(req, timeout=3) as res:
            print(f"[{res.status}] {method} {url}", flush=True)
    except urllib.error.HTTPError as e:
        print(f"[{e.code} FAIL] {method} {url} - {e.reason}", flush=True)
    except Exception as e:
        print(f"[ERR] {method} {url} - {e}", flush=True)

endpoints = [
    ('http://127.0.0.1:8000/api/system-stats', 'GET', None),
    ('http://127.0.0.1:8000/api/weather', 'GET', None),
    ('http://127.0.0.1:8000/api/crypto', 'GET', None),
    ('http://127.0.0.1:8000/api/markets', 'GET', None),
    ('http://127.0.0.1:8000/api/news', 'GET', None),
    ('http://127.0.0.1:8000/api/security-log', 'GET', None),
    ('http://127.0.0.1:8000/api/home/devices', 'GET', None),
    ('http://127.0.0.1:8000/api/comms/status', 'GET', None),
    ('http://127.0.0.1:8000/api/f1/telemetry', 'GET', None),
    ('http://127.0.0.1:8000/api/media/now-playing', 'GET', None),
    ('http://127.0.0.1:8000/api/chat/history', 'GET', None),
    ('http://127.0.0.1:8000/api/phone/status', 'GET', None),
    ('http://127.0.0.1:8000/api/iptv/channels', 'GET', None),
    ('http://127.0.0.1:8000/api/godseye/status', 'GET', None),
    ('http://127.0.0.1:8000/api/health', 'GET', None),
    ('http://127.0.0.1:8000/metrics', 'GET', None),
    ('http://127.0.0.1:8000/api/media/play-search', 'POST', {'query': 'test'}),
    ('http://127.0.0.1:8000/api/smart-plug/toggle', 'POST', {'state': True}),
    ('http://127.0.0.1:8000/api/coder/run', 'POST', {'code': 'print(1+1)'}),
]

if __name__ == "__main__":
    for url, m, d in endpoints:
        test(url, m, d)
