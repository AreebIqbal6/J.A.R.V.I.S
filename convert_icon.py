from PIL import Image
import os

# Define the target path
folder = "Frontend/Graphics"
output_path = os.path.join(folder, "Jarvis.ico")

# Possible names the user might have saved it as
possible_names = ["Jarvis.jpg", "Jarvis.png", "Jarvis_Icon.jpg", "pngegg.jpg", "icon.jpg", "icon.png"]
found_file = None

# Hunt for the file
print(f"Looking for image in {folder}...")
for name in possible_names:
    path = os.path.join(folder, name)
    if os.path.exists(path):
        found_file = path
        print(f">> Found image: {name}")
        break

if not found_file:
    # Check root folder just in case
    print("Not found in Graphics folder. Checking root folder...")
    for name in possible_names:
        if os.path.exists(name):
            found_file = name
            print(f">> Found image in root: {name}")
            break

if found_file:
    try:
        img = Image.open(found_file)
        
        # Resize and Save as .ico
        img.save(output_path, format='ICO', sizes=[(256, 256)])
        print(f"\nSUCCESS! Icon created at: {output_path}")
        print("You can now run the PyInstaller command.")
        
    except Exception as e:
        print(f"Error converting image: {e}")
else:
    print("\n!!! ERROR: Could not find any image file.")
    print("Please make sure you put the image in 'Frontend/Graphics' and name it 'Jarvis.jpg'")