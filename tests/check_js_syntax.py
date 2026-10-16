import re
import subprocess
import tempfile
import os

with open('jarvis_ui.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script(?:\s+[^>]*)?>(.*?)</script>', html, re.DOTALL)
print(f"Total script blocks found: {len(scripts)}")

for i, s in enumerate(scripts):
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False, encoding='utf-8') as tmp:
        tmp.write(s)
        tmp_name = tmp.name

    try:
        res = subprocess.run(['node', '--check', tmp_name], capture_output=True, text=True)
        if res.returncode == 0:
            print(f"Script block {i+1}: SYNTAX OK")
        else:
            print(f"Script block {i+1}: SYNTAX ERROR!\n{res.stderr}")
    finally:
        try: os.unlink(tmp_name)
        except Exception: pass
