import re

with open('jarvis_ui.html', 'r', encoding='utf-8') as f:
    text = f.read()

to_fixed_calls = re.findall(r'([^;\n\r\{\}]+?\.toFixed\([0-9]*\))', text)
print(f"Total toFixed calls found: {len(to_fixed_calls)}")
for call in to_fixed_calls:
    print("  -", call.strip())
