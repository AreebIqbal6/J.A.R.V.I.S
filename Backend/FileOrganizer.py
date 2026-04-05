import os
import shutil

def CleanUp():
    try:
        # 1. Automatically find the current user's Downloads folder
        folder_path = os.path.join(os.path.expanduser("~"), "Downloads")

        if not os.path.exists(folder_path):
            return "I couldn't find your Downloads folder."

        # 2. Extension Map
        extensions = {
            "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp", ".svg"],
            "Videos": [".mp4", ".mkv", ".mov", ".avi", ".flv", ".wmv"],
            "Documents": [".pdf", ".docx", ".doc", ".txt", ".xlsx", ".pptx", ".csv", ".epub"],
            "Software": [".exe", ".msi", ".zip", ".rar", ".iso", ".7z", ".tar", ".gz"],
            "Audio": [".mp3", ".wav", ".aac", ".flac", ".ogg"]
        }

        moved_count = 0

        # 3. Iterate over files
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)

            # Skip folders, shortcuts, and hidden files
            if os.path.isdir(file_path) or filename.endswith(".lnk") or filename.endswith(".ini") or filename.startswith("."):
                continue

            # Get extension
            _, ext = os.path.splitext(filename)
            ext = ext.lower()

            for category, exts in extensions.items():
                if ext in exts:
                    # Define Target Folder
                    target_folder = os.path.join(folder_path, category)
                    os.makedirs(target_folder, exist_ok=True)
                    
                    target_path = os.path.join(target_folder, filename)

                    # --- DUPLICATE HANDLING ---
                    # If file exists, rename it (e.g., file_1.jpg)
                    if os.path.exists(target_path):
                        base, extension = os.path.splitext(filename)
                        counter = 1
                        while os.path.exists(os.path.join(target_folder, f"{base}_{counter}{extension}")):
                            counter += 1
                        target_path = os.path.join(target_folder, f"{base}_{counter}{extension}")

                    # Move File
                    try:
                        shutil.move(file_path, target_path)
                        moved_count += 1
                    except Exception as e:
                        print(f"Error moving {filename}: {e}")
                    
                    break # Stop checking other categories for this file

        if moved_count == 0:
            return "Your downloads folder is already clean."
            
        return f"I have successfully organized {moved_count} files."

    except Exception as e:
        return f"Error organizing files: {e}"