import re

def audit_ids(html_file, js_file):
    print(f"\n=== AUDITING {html_file} vs {js_file} ===")
    with open(html_file, 'r', encoding='utf-8') as f:
        html = f.read()

    with open(js_file, 'r', encoding='utf-8') as f:
        js = f.read()

    html_ids = set(re.findall(r'id=["\']([a-zA-Z0-9_\-]+)["\']', html))
    js_ids = set(re.findall(r'getElementById\(["\']([a-zA-Z0-9_\-]+)["\']\)', js))
    js_query_ids = set(re.findall(r'querySelector\(["\']#([a-zA-Z0-9_\-]+)["\']\)', js))
    all_js_ids = js_ids | js_query_ids

    missing = all_js_ids - html_ids
    print(f"Total HTML IDs found: {len(html_ids)}")
    print(f"Total JS IDs queried: {len(all_js_ids)}")
    print(f"Missing in HTML: {len(missing)}")
    for m in sorted(missing):
        print(f"  [MISSING] {m}")

audit_ids('Frontend/index.html', 'Frontend/app.js')

with open('jarvis_ui.html', 'r', encoding='utf-8') as f:
    jarvis_content = f.read()

html_ids_jarvis = set(re.findall(r'id=["\']([a-zA-Z0-9_\-]+)["\']', jarvis_content))
js_ids_jarvis = set(re.findall(r'getElementById\(["\']([a-zA-Z0-9_\-]+)["\']\)', jarvis_content))
js_query_ids_jarvis = set(re.findall(r'querySelector\(["\']#([a-zA-Z0-9_\-]+)["\']\)', jarvis_content))
all_js_jarvis = js_ids_jarvis | js_query_ids_jarvis

missing_jarvis = all_js_jarvis - html_ids_jarvis
print(f"\n=== AUDITING jarvis_ui.html (inline scripts vs markup) ===")
print(f"Total HTML IDs found: {len(html_ids_jarvis)}")
print(f"Total JS IDs queried: {len(all_js_jarvis)}")
print(f"Missing in HTML: {len(missing_jarvis)}")
for m in sorted(missing_jarvis):
    print(f"  [MISSING] {m}")

