import os
import datetime
import time

def SentryMode():
    # Lazy load heavy modules to prevent J.A.R.V.I.S. from hanging on startup
    try:
        import cv2
        import winsound
    except ImportError:
        return "Camera or audio modules are missing, sir."

    # 1. Initialize Camera (Silent fail if no camera)
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        return "Sentry Mode Failed: No Camera Found."

    # 2. Load Face Detection Data (Robust Path Handling)
    cascade_path = os.path.join(cv2.data.haarcascades, 'haarcascade_frontalface_default.xml')
    
    if not os.path.exists(cascade_path):
        cascade_path = os.path.join("Backend", "haarcascade_frontalface_default.xml") 
        if not os.path.exists(cascade_path):
            cap.release()
            return "Error: Could not find facial recognition data."
    
    face_cascade = cv2.CascadeClassifier(cascade_path)
    
    save_dir = os.path.join("Data", "Intruders")
    os.makedirs(save_dir, exist_ok=True)

    print(">>> SENTRY MODE ACTIVATED. PRESS 'q' TO EXIT.")
    # Startup Beep (High pitch to indicate armed)
    winsound.Beep(2500, 500) 
    
    last_detection_time = 0 # Cooldown tracker
    
    while True:
        ret, frame = cap.read()
        if not ret: break

        # Optimization: Convert to grayscale for faster detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect Faces (Scale Factor 1.1, Min Neighbors 5 for less false positives)
        faces = face_cascade.detectMultiScale(gray, 1.1, 5)
        
        for (x, y, w, h) in faces:
            # Draw Red Box
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 0, 255), 2)
            cv2.putText(frame, "INTRUDER ALERT", (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
            
            # --- INTRUDER ACTIONS WITH COOLDOWN ---
            current_time = time.time()
            
            # 3-Second Cooldown: Prevents saving 30 photos a second and freezing the disk
            if current_time - last_detection_time > 3.0:
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                print(f"!!! INTRUDER DETECTED AT {timestamp} !!!")
                
                # Save Photo
                filename = os.path.join(save_dir, f"Intruder_{timestamp}.jpg")
                cv2.imwrite(filename, frame)
                
                # Alarm Sound
                winsound.Beep(1000, 500) 
                
                last_detection_time = current_time

        # Show Feed
        cv2.imshow('JARVIS SENTRY HUD', frame)

        # Exit on 'q'
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
    return "Sentry Mode Deactivated, sir."