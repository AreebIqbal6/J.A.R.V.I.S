import re

with open('jarvis_ui.html', 'r', encoding='utf-8') as f:
    text = f.read()

screens = re.findall(r'id=["\'](screen-[a-zA-Z0-9_\-]+)["\']', text)
print("Screens in jarvis_ui.html:", screens)

dock_buttons = re.findall(r'<button[^>]*class=["\'][^"\']*dock-btn[^"\']*["\'][^>]*>(.*?)</button>', text, re.DOTALL)
print("\nDock buttons in jarvis_ui.html:")
for b in dock_buttons:
    clean = re.sub(r'<[^>]+>', '', b).strip()
    print("  -", clean)

nav_tabs = re.findall(r'<[^>]*class=["\'][^"\']*nav-item[^"\']*["\'][^>]*>(.*?)</[^>]+>', text, re.DOTALL)
print("\nNav tabs in jarvis_ui.html:")
for t in nav_tabs:
    clean = re.sub(r'<[^>]+>', '', t).strip()
    print("  -", clean)
