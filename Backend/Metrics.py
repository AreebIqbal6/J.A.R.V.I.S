import time
import psutil

START_TIME = time.time()
REQUEST_COUNTS = {}

def track_request(endpoint: str, status_code: int):
    key = f"{endpoint}:{status_code}"
    REQUEST_COUNTS[key] = REQUEST_COUNTS.get(key, 0) + 1

def generate_prometheus_metrics(ws_client_count: int = 0) -> str:
    uptime = time.time() - START_TIME
    cpu = psutil.cpu_percent(interval=None)
    ram = psutil.virtual_memory().percent
    
    lines = [
        "# HELP jarvis_uptime_seconds Total seconds J.A.R.V.I.S. core has been running",
        "# TYPE jarvis_uptime_seconds counter",
        f"jarvis_uptime_seconds {uptime:.1f}",
        "# HELP jarvis_cpu_percent Host CPU utilization percent",
        "# TYPE jarvis_cpu_percent gauge",
        f"jarvis_cpu_percent {cpu:.1f}",
        "# HELP jarvis_memory_percent Host RAM utilization percent",
        "# TYPE jarvis_memory_percent gauge",
        f"jarvis_memory_percent {ram:.1f}",
        "# HELP jarvis_websocket_clients_active Active real-time WebSocket clients",
        "# TYPE jarvis_websocket_clients_active gauge",
        f"jarvis_websocket_clients_active {ws_client_count}"
    ]
    
    for key, count in REQUEST_COUNTS.items():
        ep, code = key.split(":")
        lines.append(f'jarvis_http_requests_total{{endpoint="{ep}",status="{code}"}} {count}')
        
    return "\n".join(lines) + "\n"
