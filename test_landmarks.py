import cv2
import mediapipe as mp

print("MediaPipe version:", mp.__version__)
print("Has solutions:", hasattr(mp, "solutions"))

if hasattr(mp, "solutions"):
    print("MediaPipe Solutions API available")
else:
    print("MediaPipe Solutions API NOT available")