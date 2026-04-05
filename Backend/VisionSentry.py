import cv2
import pyautogui
import math
import time
import mediapipe as mp

def get_working_camera():
    """Aggressively hunts for a working camera lens across all indices and backends."""
    print(">> [VISION SENTRY]: Hunting for active camera lens...")
    
    for index in [0, 1, 2]:
        # Try default backend first
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f">> [VISION SENTRY]: Success! Camera locked on Index {index} (Default)")
                return cap
            cap.release()
            
        # Try DirectShow backend (Crucial for Windows)
        cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        if cap.isOpened():
            ret, _ = cap.read()
            if ret:
                print(f">> [VISION SENTRY]: Success! Camera locked on Index {index} (DirectShow)")
                return cap
            cap.release()
            
    return None

def StartGestureSentry():
    """Runs a 30FPS spatial tracking loop for holographic gestures."""
    try:
        # Standard, clean MediaPipe initialization
        mp_hands = mp.solutions.hands
        hands = mp_hands.Hands(
            min_detection_confidence=0.7, 
            min_tracking_confidence=0.7,
            max_num_hands=1 # Limit to 1 hand to save CPU resources
        )
        
        # Deploy the camera hunter
        cap = get_working_camera()
        
        if cap is None:
            print("!! [VISION SENTRY]: FAILED. All camera indices are blocked or in use.")
            return

        print(">> [VISION SENTRY]: Holographic spatial tracking online. Waiting for hand...")
        
        last_action_time = 0
        current_cooldown = 0.5 
        anchor_x, anchor_y = None, None

        while True:
            success, img = cap.read()
            if not success:
                time.sleep(0.1)
                continue

            # Flip camera horizontally to act like a mirror
            img = cv2.flip(img, 1)
            imgRGB = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            results = hands.process(imgRGB)
            
            current_time = time.time()

            if results.multi_hand_landmarks:
                for handLms in results.multi_hand_landmarks:
                    thumb = handLms.landmark[4]
                    index = handLms.landmark[8]
                    
                    # 1. PINCH DETECTION (Play/Pause)
                    pinch_dist = math.hypot(index.x - thumb.x, index.y - thumb.y)
                    
                    if pinch_dist < 0.05 and (current_time - last_action_time > 1.0):
                        print(">> [GESTURE]: Pinch Detected -> Play/Pause")
                        pyautogui.press("playpause")
                        last_action_time = current_time
                        current_cooldown = 1.0
                        anchor_x, anchor_y = index.x, index.y 
                        continue 
                    
                    # 2. SPATIAL SWIPE/HOVER DETECTION
                    if anchor_x is None:
                        anchor_x, anchor_y = index.x, index.y
                    
                    delta_x = index.x - anchor_x
                    delta_y = index.y - anchor_y
                    
                    if current_time - last_action_time > current_cooldown:
                        MOVEMENT_THRESHOLD = 0.15 
                        
                        if abs(delta_x) > MOVEMENT_THRESHOLD or abs(delta_y) > MOVEMENT_THRESHOLD:
                            if abs(delta_x) > abs(delta_y):
                                # Horizontal Swipe
                                if delta_x > 0:
                                    print(">> [GESTURE]: Right Hover -> Next Track")
                                    pyautogui.press("nexttrack")
                                else:
                                    print(">> [GESTURE]: Left Hover -> Previous Track")
                                    pyautogui.press("prevtrack")
                                
                                last_action_time = current_time
                                current_cooldown = 1.0
                                anchor_x, anchor_y = index.x, index.y 
                                
                            else:
                                # Vertical Hover (Volume)
                                if delta_y > 0:
                                    print(">> [GESTURE]: Downward Hover -> Decrease Volume")
                                    pyautogui.press("volumedown", presses=8)
                                else:
                                    print(">> [GESTURE]: Upward Hover -> Increase Volume")
                                    pyautogui.press("volumeup", presses=8)
                                    
                                last_action_time = current_time
                                current_cooldown = 0.3
                                anchor_x, anchor_y = index.x, index.y 
            else:
                anchor_x, anchor_y = None, None

            time.sleep(0.05) 

    except Exception as e:
        print(f"!! [VISION SENTRY ERROR]: {e}")
    finally:
        if 'cap' in locals() and cap is not None:
            cap.release()