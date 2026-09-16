import cv2
import time
import urllib.request
import os

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_PATH = "face_landmarker.task"

MODEL_URL = (
    "https://storage.googleapis.com/"
    "mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/"
    "face_landmarker.task"
)


class LandmarkDetector:

    def __init__(self):

        # Download landmark model once
        if not os.path.exists(MODEL_PATH):

            print("Downloading Face Landmarker model...")

            urllib.request.urlretrieve(
                MODEL_URL,
                MODEL_PATH
            )

            print("Download complete.")

        base_options = python.BaseOptions(
            model_asset_path=MODEL_PATH
        )

        options = vision.FaceLandmarkerOptions(
            base_options=base_options,

            running_mode=vision.RunningMode.VIDEO,

            num_faces=1,

            min_face_detection_confidence=0.5,

            min_face_presence_confidence=0.5,

            min_tracking_confidence=0.5,

            output_face_blendshapes=False,

            output_facial_transformation_matrixes=False
        )

        self.detector = vision.FaceLandmarker.create_from_options(
            options
        )

        self.start_time = time.time()


    def detect(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )

        mp_image = vision.MPImage(
            image_format=vision.ImageFormat.SRGB,
            data=rgb
        )

        timestamp_ms = int(
            (time.time() - self.start_time)
            * 1000
        )

        result = self.detector.detect_for_video(
            mp_image,
            timestamp_ms
        )

        if not result.face_landmarks:
            return None

        return result.face_landmarks[0]


    def close(self):

        self.detector.close()