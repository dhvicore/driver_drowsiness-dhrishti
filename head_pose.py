import cv2
import time
import numpy as np
from collections import deque


class HeadPoseDetector:

    def __init__(self):

        # Smoothing
        self.pitch_buffer = deque(maxlen=7)
        self.yaw_buffer = deque(maxlen=7)

        # Your calibrated ranges
        self.LEFT_THRESHOLD = -25
        self.RIGHT_THRESHOLD = 20

        self.DOWN_THRESHOLD = 20
        self.UP_THRESHOLD = -15

        # How long before we consider it distraction
        self.LOOK_AWAY_SECONDS = 1.5
        self.DOWN_SECONDS = 1.2

        # Timer
        self.distraction_start = None

        self.direction = "FORWARD"
        self.distraction_duration = 0.0
        self.distracted = False


    # ========================================================
    # HELPER
    # ========================================================

    def _point(
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


    # ========================================================
    # CALCULATE POSE
    # ========================================================

    def calculate(
        self,
        landmarks,
        width,
        height
    ):

        image_points = np.array(
            [
                self._point(
                    landmarks, 1,
                    width, height
                ),

                self._point(
                    landmarks, 152,
                    width, height
                ),

                self._point(
                    landmarks, 33,
                    width, height
                ),

                self._point(
                    landmarks, 263,
                    width, height
                ),

                self._point(
                    landmarks, 61,
                    width, height
                ),

                self._point(
                    landmarks, 291,
                    width, height
                )
            ],
            dtype=np.float64
        )


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

            return self._empty_result()


        rotation_matrix, _ = cv2.Rodrigues(
            rotation_vector
        )


        angles, _, _, _, _, _ = (
            cv2.RQDecomp3x3(
                rotation_matrix
            )
        )


        pitch = float(angles[0])
        yaw = float(angles[1])


        # ====================================================
        # NORMALIZE PITCH
        # ====================================================

        if pitch < -90:

            pitch += 180

        elif pitch > 90:

            pitch -= 180


        # Webcam is mirrored
        yaw = -yaw


        # ====================================================
        # SMOOTH
        # ====================================================

        self.pitch_buffer.append(
            pitch
        )

        self.yaw_buffer.append(
            yaw
        )


        pitch = float(
            np.median(
                self.pitch_buffer
            )
        )


        yaw = float(
            np.median(
                self.yaw_buffer
            )
        )


        # ====================================================
        # DIRECTION
        # ====================================================

        if yaw < self.LEFT_THRESHOLD:

            direction = "LEFT"


        elif yaw > self.RIGHT_THRESHOLD:

            direction = "RIGHT"


        elif pitch > self.DOWN_THRESHOLD:

            direction = "DOWN"


        elif pitch < self.UP_THRESHOLD:

            direction = "UP"


        else:

            direction = "FORWARD"


        self.direction = direction


        # ====================================================
        # TEMPORAL DISTRACTION
        # ====================================================

        now = time.time()


        if direction == "FORWARD":

            self.distraction_start = None

            self.distraction_duration = 0.0

            self.distracted = False


        else:

            if self.distraction_start is None:

                self.distraction_start = now


            self.distraction_duration = (
                now
                -
                self.distraction_start
            )


            # Looking down is particularly relevant
            if direction == "DOWN":

                required_time = (
                    self.DOWN_SECONDS
                )

            else:

                required_time = (
                    self.LOOK_AWAY_SECONDS
                )


            self.distracted = (
                self.distraction_duration
                >=
                required_time
            )


        return {

            "pitch": pitch,

            "yaw": yaw,

            "direction": direction,

            "duration":
                self.distraction_duration,

            "distracted":
                self.distracted
        }


    # ========================================================
    # NO FACE
    # ========================================================

    def _empty_result(self):

        return {

            "pitch": 0.0,

            "yaw": 0.0,

            "direction": "UNKNOWN",

            "duration": 0.0,

            "distracted": False
        }


    def reset(self):

        self.pitch_buffer.clear()

        self.yaw_buffer.clear()

        self.distraction_start = None

        self.distraction_duration = 0.0

        self.distracted = False

        self.direction = "UNKNOWN"