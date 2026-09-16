import cv2
import math
import time
import os
import urllib.request
import numpy as np
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision


MODEL_PATH = "face_landmarker.task"

MODEL_URL = (
    "https://storage.googleapis.com/"
    "mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/"
    "face_landmarker.task"
)


# ============================================================
# LANDMARK INDICES
# ============================================================

LEFT_EYE = {
    "left": 33,
    "right": 133,
    "upper1": 160,
    "lower1": 144,
    "upper2": 158,
    "lower2": 153
}

RIGHT_EYE = {
    "left": 362,
    "right": 263,
    "upper1": 385,
    "lower1": 380,
    "upper2": 387,
    "lower2": 373
}


MOUTH_LEFT = 61
MOUTH_RIGHT = 291
MOUTH_UPPER = 13
MOUTH_LOWER = 14


class FaceAnalyzer:

    def __init__(self):

        if not os.path.exists(MODEL_PATH):

            print("Downloading Face Landmarker...")

            urllib.request.urlretrieve(
                MODEL_URL,
                MODEL_PATH
            )


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


        self.detector = (
            vision.FaceLandmarker.create_from_options(
                options
            )
        )

        self.start_time = time.time()


    # ========================================================
    # BASIC HELPERS
    # ========================================================

    def point(
        self,
        landmarks,
        index,
        width,
        height
    ):

        lm = landmarks[index]

        return (
            int(lm.x * width),
            int(lm.y * height)
        )


    def distance(self, p1, p2):

        return math.sqrt(
            (p1[0] - p2[0]) ** 2
            +
            (p1[1] - p2[1]) ** 2
        )


    # ========================================================
    # EAR
    # ========================================================

    def eye_ear(
        self,
        landmarks,
        eye,
        width,
        height
    ):

        left = self.point(
            landmarks,
            eye["left"],
            width,
            height
        )

        right = self.point(
            landmarks,
            eye["right"],
            width,
            height
        )

        upper1 = self.point(
            landmarks,
            eye["upper1"],
            width,
            height
        )

        lower1 = self.point(
            landmarks,
            eye["lower1"],
            width,
            height
        )

        upper2 = self.point(
            landmarks,
            eye["upper2"],
            width,
            height
        )

        lower2 = self.point(
            landmarks,
            eye["lower2"],
            width,
            height
        )


        horizontal = self.distance(
            left,
            right
        )


        if horizontal == 0:
            return 0


        return (
            self.distance(
                upper1,
                lower1
            )
            +
            self.distance(
                upper2,
                lower2
            )
        ) / (
            2.0 * horizontal
        )


    # ========================================================
    # MAR
    # ========================================================

    def mar(
        self,
        landmarks,
        width,
        height
    ):

        left = self.point(
            landmarks,
            MOUTH_LEFT,
            width,
            height
        )

        right = self.point(
            landmarks,
            MOUTH_RIGHT,
            width,
            height
        )

        upper = self.point(
            landmarks,
            MOUTH_UPPER,
            width,
            height
        )

        lower = self.point(
            landmarks,
            MOUTH_LOWER,
            width,
            height
        )


        horizontal = self.distance(
            left,
            right
        )


        if horizontal == 0:
            return 0


        return (
            self.distance(
                upper,
                lower
            )
            /
            horizontal
        )


    # ========================================================
    # HEAD POSE
    # ========================================================

    def head_pose(
        self,
        landmarks,
        width,
        height
    ):

        # Important facial reference points
        indices = [
            1,      # nose
            152,    # chin
            33,     # left eye corner
            263,    # right eye corner
            61,     # left mouth
            291     # right mouth
        ]


        image_points = np.array(
            [
                self.point(
                    landmarks,
                    idx,
                    width,
                    height
                )
                for idx in indices
            ],
            dtype=np.float64
        )


        # Approximate generic 3D face model
        model_points = np.array(
            [
                (0.0, 0.0, 0.0),
                (0.0, -63.6, -12.5),
                (-43.3, 32.7, -26.0),
                (43.3, 32.7, -26.0),
                (-28.9, -28.9, -24.1),
                (28.9, -28.9, -24.1)
            ],
            dtype=np.float64
        )


        focal_length = width


        camera_matrix = np.array(
            [
                [
                    focal_length,
                    0,
                    width / 2
                ],
                [
                    0,
                    focal_length,
                    height / 2
                ],
                [
                    0,
                    0,
                    1
                ]
            ],
            dtype=np.float64
        )


        distortion = np.zeros(
            (4, 1)
        )


        success, rotation_vector, _ = (
            cv2.solvePnP(
                model_points,
                image_points,
                camera_matrix,
                distortion,
                flags=cv2.SOLVEPNP_ITERATIVE
            )
        )


        if not success:

            return 0, 0, 0


        rotation_matrix, _ = (
            cv2.Rodrigues(
                rotation_vector
            )
        )


        projection = np.hstack(
            (
                rotation_matrix,
                np.zeros(
                    (3, 1)
                )
            )
        )


        _, _, _, _, _, _, euler = (
            cv2.decomposeProjectionMatrix(
                projection
            )
        )


        pitch = float(
            euler[0][0]
        )

        yaw = float(
            euler[1][0]
        )

        roll = float(
            euler[2][0]
        )


        return (
            pitch,
            yaw,
            roll
        )


    # ========================================================
    # MAIN DETECTION
    # ========================================================

    def analyze(self, frame):

        rgb = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2RGB
        )


        mp_image = mp.Image(

            image_format=mp.ImageFormat.SRGB,

            data=rgb
        )


        timestamp = int(
            (
                time.time()
                -
                self.start_time
            )
            * 1000
        )


        result = (
            self.detector.detect_for_video(
                mp_image,
                timestamp
            )
        )


        if not result.face_landmarks:

            return None


        landmarks = (
            result.face_landmarks[0]
        )


        h, w = frame.shape[:2]


        left_ear = self.eye_ear(
            landmarks,
            LEFT_EYE,
            w,
            h
        )


        right_ear = self.eye_ear(
            landmarks,
            RIGHT_EYE,
            w,
            h
        )


        ear = (
            left_ear
            +
            right_ear
        ) / 2


        mouth_ratio = self.mar(
            landmarks,
            w,
            h
        )


        pitch, yaw, roll = (
            self.head_pose(
                landmarks,
                w,
                h
            )
        )


        return {

            "landmarks":
                landmarks,

            "left_ear":
                left_ear,

            "right_ear":
                right_ear,

            "ear":
                ear,

            "mar":
                mouth_ratio,

            "pitch":
                pitch,

            "yaw":
                yaw,

            "roll":
                roll
        }


    def close(self):

        self.detector.close()