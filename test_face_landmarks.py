import cv2
import time
import os
import urllib.request
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ==========================================
# MODEL
# ==========================================

MODEL_PATH = "face_landmarker.task"

MODEL_URL = (
    "https://storage.googleapis.com/"
    "mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/"
    "face_landmarker.task"
)


if not os.path.exists(MODEL_PATH):

    print("Downloading face landmark model...")

    urllib.request.urlretrieve(
        MODEL_URL,
        MODEL_PATH
    )

    print("Model downloaded.")


# ==========================================
# CREATE LANDMARKER
# ==========================================

base_options = python.BaseOptions(
    model_asset_path=MODEL_PATH
)


options = vision.FaceLandmarkerOptions(

    base_options=base_options,

    running_mode=vision.RunningMode.VIDEO,

    num_faces=1,

    min_face_detection_confidence=0.5,

    min_face_presence_confidence=0.5,

    min_tracking_confidence=0.5
)


detector = vision.FaceLandmarker.create_from_options(
    options
)


# ==========================================
# CAMERA
# ==========================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("ERROR: Camera could not open.")

    detector.close()

    exit()


start_time = time.time()

print("Face landmark test started.")
print("Press Q to quit.")


# ==========================================
# LOOP
# ==========================================

while True:

    ret, frame = cap.read()

    if not ret:
        break


    frame = cv2.flip(
        frame,
        1
    )


    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    # MediaPipe Image
    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb
    )


    timestamp_ms = int(
        (time.time() - start_time)
        * 1000
    )


    result = detector.detect_for_video(
        mp_image,
        timestamp_ms
    )


    # ======================================
    # DRAW LANDMARKS
    # ======================================

    if result.face_landmarks:

        landmarks = result.face_landmarks[0]

        h, w = frame.shape[:2]


        # Draw all face landmarks
        for landmark in landmarks:

            px = int(
                landmark.x * w
            )

            py = int(
                landmark.y * h
            )


            cv2.circle(

                frame,

                (px, py),

                1,

                (0, 255, 0),

                -1
            )


        cv2.putText(

            frame,

            f"FACE LANDMARKS: {len(landmarks)}",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 255, 0),

            2
        )


    else:

        cv2.putText(

            frame,

            "NO FACE",

            (20, 40),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.8,

            (0, 0, 255),

            2
        )


    cv2.imshow(
        "MediaPipe Face Landmarks",
        frame
    )


    if (
        cv2.waitKey(1)
        & 0xFF
        ==
        ord("q")
    ):

        break


cap.release()

detector.close()

cv2.destroyAllWindows()