import os

# --- THE JUNK FILTER ---
IGNORE_DIRS = {'.git', '__pycache__', 'venv', 'env', 'node_modules', '.vscode', '.idea', 'Workspace'}
IGNORE_FILES = {'.env', '.DS_Store', 'project_tree.txt', 'ChatLog.json', 'JarvisMemory.db', 'generate_tree.py'}
IGNORE_EXTENSIONS = {'.pyc', '.pyo', '.pyd', '.db', '.sqlite3'}

def generate_tree(startpath, prefix=''):
    tree_str = ""
    try:
        items = sorted(os.listdir(startpath))
    except PermissionError:
        return ""

    # Filter out the noise
    dirs = [d for d in items if os.path.isdir(os.path.join(startpath, d)) and d not in IGNORE_DIRS]
    files = [f for f in items if os.path.isfile(os.path.join(startpath, f)) 
             and f not in IGNORE_FILES 
             and not any(f.endswith(ext) for ext in IGNORE_EXTENSIONS)]
    
    cleaned_items = dirs + files
    
    for i, item in enumerate(cleaned_items):
        path = os.path.join(startpath, item)
        is_last = (i == len(cleaned_items) - 1)
        connector = '└── ' if is_last else '├── '
        
        tree_str += f"{prefix}{connector}{item}\n"
        
        if os.path.isdir(path):
            extension = '    ' if is_last else '│   '
            tree_str += generate_tree(path, prefix + extension)
            
    return tree_str

if __name__ == "__main__":
    print(">> [SENTRY]: Scanning directory structure...")
    root_dir = os.getcwd()
    
    # Generate the tree
    tree_output = f"📁 {os.path.basename(root_dir)}/\n" + generate_tree(root_dir)
    
    # Save it to a safe text file
    output_file = "project_tree.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write(tree_output)
        
    print(f">> [SUCCESS]: Clean architecture mapped and saved to '{output_file}'.")
    print(">> You may now copy the contents of that file and provide them to me, Sir.")