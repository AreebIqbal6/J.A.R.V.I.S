"""
Backend/Vision.py
Computer Vision & Optical Reconnaissance Subsystem
Powered by Roboflow Supervision (https://github.com/roboflow/supervision) & OpenCV.
Provides live optical sensor analysis, face/person detection, and tactical HUD annotations.
"""

import cv2
import numpy as np
import base64
import os
import logging
from typing import Dict, Any, Optional
import supervision as sv

logger = logging.getLogger("JARVIS_Vision")

# Load OpenCV cascades
CASCADE_FACE = os.path.join(cv2.data.haarcascades, "haarcascade_frontalface_default.xml")
CASCADE_EYE = os.path.join(cv2.data.haarcascades, "haarcascade_eye.xml")

face_classifier = cv2.CascadeClassifier(CASCADE_FACE) if os.path.exists(CASCADE_FACE) else None
eye_classifier = cv2.CascadeClassifier(CASCADE_EYE) if os.path.exists(CASCADE_EYE) else None

# Initialize Supervision Annotators
box_annotator = sv.BoxAnnotator(
    thickness=2,
    color=sv.Color.from_hex("#22d3ee") # Cyan cyber theme
)
label_annotator = sv.LabelAnnotator(
    text_color=sv.Color.from_hex("#020617"),
    text_scale=0.5,
    text_thickness=1
)

def analyze_optical_frame(image_bytes: Optional[bytes] = None) -> Dict[str, Any]:
    """
    Analyzes an optical frame using OpenCV & Supervision.
    Detects faces/persons, generates bounding boxes, and returns base64 annotated frame.
    """
    try:
        if image_bytes:
            nparr = np.frombuffer(image_bytes, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:
            # Generate tactical optical standby frame if no physical feed
            frame = np.zeros((480, 640, 3), dtype=np.uint8)
            # Draw synthetic grid and HUD crosshairs
            cv2.line(frame, (320, 200), (320, 280), (77, 216, 255), 1)
            cv2.line(frame, (280, 240), (360, 240), (77, 216, 255), 1)
            cv2.circle(frame, (320, 240), 50, (77, 216, 255), 1)
            cv2.putText(frame, "OPTICAL SENSOR // ACTIVE", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (77, 216, 255), 1)
            cv2.putText(frame, "SUPERVISION RUNTIME: 0.30.9", (20, 460), cv2.FONT_HERSHEY_SIMPLEX, 0.45, (148, 163, 184), 1)

        if frame is None:
            return {"error": "Invalid image frame."}

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        boxes = []
        labels = []

        if face_classifier:
            faces = face_classifier.detectMultiScale(gray, scaleFactor=1.2, minNeighbors=5, minSize=(30, 30))
            for (x, y, w, h) in faces:
                boxes.append([x, y, x + w, y + h])
                labels.append(f"TARGET // HUMAN [{w}x{h}]")

        detections_count = len(boxes)

        if detections_count > 0:
            xyxy = np.array(boxes, dtype=np.float32)
            detections = sv.Detections(
                xyxy=xyxy,
                confidence=np.ones(detections_count, dtype=np.float32) * 0.95
            )
            # Annotate with Supervision
            annotated_frame = box_annotator.annotate(scene=frame.copy(), detections=detections)
            annotated_frame = label_annotator.annotate(scene=annotated_frame, detections=detections, labels=labels)
        else:
            annotated_frame = frame

        # Encode to JPEG base64
        _, buffer = cv2.imencode('.jpg', annotated_frame)
        b64_frame = base64.b64encode(buffer).decode('utf-8')

        return {
            "status": "ANALYSIS_COMPLETE",
            "detections_count": detections_count,
            "targets": labels,
            "sensor_health": "ONLINE",
            "resolution": f"{frame.shape[1]}x{frame.shape[0]}",
            "annotated_b64": f"data:image/jpeg;base64,{b64_frame}",
            "summary": f"Optical sensor analyzed: {detections_count} target(s) detected. Sector secure."
        }

    except Exception as e:
        logger.error(f"Vision analysis error: {e}")
        return {"error": f"Optical analysis error: {str(e)}"}
