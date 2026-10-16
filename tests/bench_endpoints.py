import urllib.request
import json
import time

def test(url, method='GET', data=None):
    t0 = time.time()
    try:
        req = urllib.request.Request(url, method=method)
        if data:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
        with urllib.request.urlopen(req, timeout=5) as r:
            dt = (time.time() - t0) * 1000
            print(f"[{r.status}] {method} {url} in {dt:.1f}ms")
    except Exception as e:
        dt = (time.time() - t0) * 1000
        print(f"[FAIL {dt:.1f}ms] {method} {url}: {e}")

if __name__ == '__main__':
    test('http://127.0.0.1:8000/api/system-stats')
    test('http://127.0.0.1:8000/api/earth-tracker')
    test('http://127.0.0.1:8000/api/media/play', method='POST', data={'query': 'test'})
    test('http://127.0.0.1:8000/api/weather')
    test('http://127.0.0.1:8000/api/markets')
    test('http://127.0.0.1:8000/api/chat/history')
    test('http://127.0.0.1:8000/api/home/devices')
