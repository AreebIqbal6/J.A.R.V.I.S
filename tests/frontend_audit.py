import re
import os

def analyze_file(filepath):
    print(f"\n==========================================")
    print(f"ANALYZING: {filepath}")
    print(f"==========================================")
    if not os.path.exists(filepath):
        print("FILE NOT FOUND!")
        return
        
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Find IDs declared
    declared_ids = set(re.findall(r'id=["\']([a-zA-Z0-9_\-]+)["\']', content))
    
    # Find IDs referenced via getElementById or querySelector('#...')
    get_elem_ids = set(re.findall(r'getElementById\(["\']([a-zA-Z0-9_\-]+)["\']\)', content))
    query_ids = set(re.findall(r'querySelector\(["\']#([a-zA-Z0-9_\-]+)["\']\)', content))
    referenced_ids = get_elem_ids | query_ids

    # For HTML files, compare referenced vs declared
    if filepath.endswith('.html'):
        missing = referenced_ids - declared_ids
        print(f"Total IDs declared in HTML: {len(declared_ids)}")
        print(f"Total IDs referenced in inline JS: {len(referenced_ids)}")
        if missing:
            print(f"[!] MISSING IDs referenced in script but NOT in HTML ({len(missing)}):")
            for m in sorted(missing):
                print(f"    - {m}")
        else:
            print("[OK] All referenced IDs exist in HTML.")

    # Find all fetch calls
    fetch_matches = re.findall(r'fetch\([`\'"]([^`\'"]+)[`\'"]', content)
    print(f"\nFetch calls found ({len(fetch_matches)}):")
    for fm in sorted(set(fetch_matches)):
        print(f"    - {fm}")

    # Check for placeholder/mock text patterns
    suspect_patterns = [
        r'lorem ipsum',
        r'dummy',
        r'placeholder',
        r'mock',
        r'sample\s+text',
        r'todo',
        r'not implemented',
        r'fake',
        r'undefined',
        r'NaN'
    ]
    print("\nSuspicious placeholder strings check:")
    found_suspect = False
    for pat in suspect_patterns:
        matches = re.findall(pat, content, re.IGNORECASE)
        if matches:
            found_suspect = True
            print(f"    [!] Pattern '{pat}' found {len(matches)} times!")
    if not found_suspect:
        print("    [OK] No suspicious mock/placeholder text patterns found.")

analyze_file('jarvis_ui.html')
analyze_file('Frontend/index.html')
analyze_file('Frontend/app.js')
