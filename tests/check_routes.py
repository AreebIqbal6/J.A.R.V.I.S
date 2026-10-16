import re

with open('Backend/Server.py', 'r', encoding='utf-8') as f:
    server_py = f.read()

with open('Backend/real_data.py', 'r', encoding='utf-8') as f:
    real_data_py = f.read()

# Routes in server.py and real_data.py
routes_server = set(re.findall(r'@app\.(?:get|post|put|delete)\(["\']([^"\']+)["\']', server_py))
routes_real_data = set(re.findall(r'@router\.(?:get|post|put|delete)\(["\']([^"\']+)["\']', real_data_py))

# In Server.py, app.include_router(real_data.router) with no prefix
all_routes = routes_server | routes_real_data

print("Total registered routes on backend:", len(all_routes))

with open('jarvis_ui.html', 'r', encoding='utf-8') as f:
    ui_html = f.read()

with open('Frontend/app.js', 'r', encoding='utf-8') as f:
    app_js = f.read()

def normalize_endpoint(ep):
    ep = ep.replace('${API}', '').replace('${API_BASE}', '')
    if not ep.startswith('/'):
        ep = '/' + ep
    return ep

ui_endpoints = set(re.findall(r'fetch\([`\'"]([^`\'"]+)[`\'"]', ui_html))
app_endpoints = set(re.findall(r'fetch\([`\'"]([^`\'"]+)[`\'"]', app_js))

print("\n=== CHECKING jarvis_ui.html FETCH CALLS ===")
for raw_ep in sorted(ui_endpoints):
    norm = normalize_endpoint(raw_ep)
    # Check if norm or norm without query string matches any route
    base_norm = norm.split('?')[0]
    exists = base_norm in all_routes or any(r.startswith(base_norm) for r in all_routes)
    status = "[OK]" if exists else "[404 NOT FOUND!]"
    print(f"  {status} {raw_ep} -> {norm}")

print("\n=== CHECKING Frontend/app.js FETCH CALLS ===")
for raw_ep in sorted(app_endpoints):
    norm = normalize_endpoint(raw_ep)
    base_norm = norm.split('?')[0]
    exists = base_norm in all_routes or any(r.startswith(base_norm) for r in all_routes)
    status = "[OK]" if exists else "[404 NOT FOUND!]"
    print(f"  {status} {raw_ep} -> {norm}")
