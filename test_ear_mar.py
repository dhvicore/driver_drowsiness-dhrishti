import cv2
import time
import os
import math
import urllib.request
import numpy as np
import mediapipe as mp

from collections import deque
from mediapipe.tasks import python
from mediapipe.tasks.python import vision


# ============================================================
# SETTINGS
# ============================================================

MODEL_PATH = "face_landmarker.task"

MODEL_URL = (
    "https://storage.googleapis.com/"
    "mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/"
    "face_landmarker.task"
)


# ---------------- EYE SETTINGS ----------------

# Your normal open EAR is around 0.27 - 0.38.
#
# We intentionally use TWO thresholds.
# This prevents OPEN/CLOSED flickering.

EYE_CLOSE_THRESHOLD = 0.20
EYE_OPEN_THRESHOLD = 0.24

# State must persist for several frames
EYE_CONFIRM_FRAMES = 4

# Median smoothing
EAR_SMOOTHING_FRAMES = 7


# ---------------- MOUTH / YAWN SETTINGS ----------------

# Your measurements:
# closed ≈ 0.02
# wide open ≈ 0.73

MAR_YAWN_START = 0.38
MAR_YAWN_STOP = 0.20

MAR_SMOOTHING_FRAMES = 7

# Mouth must stay open this long
YAWN_CONFIRM_SECONDS = 0.7

# Mouth must stay closed before yawn ends
YAWN_STOP_SECONDS = 0.4


# ============================================================
# MEDIAPIPE
# ============================================================

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


detector = vision.FaceLandmarker.create_from_options(
    options
)


# ============================================================
# LANDMARKS
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


# ============================================================
# FUNCTIONS
# ============================================================

def point(landmarks, index, width, height):

    lm = landmarks[index]

    return (
        int(lm.x * width),
        int(lm.y * height)
    )


def distance(p1, p2):

    return math.sqrt(
        (p1[0] - p2[0]) ** 2
        +
        (p1[1] - p2[1]) ** 2
    )


def calculate_ear(
    landmarks,
    eye,
    width,
    height
):

    left = point(
        landmarks,
        eye["left"],
        width,
        height
    )

    right = point(
        landmarks,
        eye["right"],
        width,
        height
    )

    upper1 = point(
        landmarks,
        eye["upper1"],
        width,
        height
    )

    lower1 = point(
        landmarks,
        eye["lower1"],
        width,
        height
    )

    upper2 = point(
        landmarks,
        eye["upper2"],
        width,
        height
    )

    lower2 = point(
        landmarks,
        eye["lower2"],
        width,
        height
    )


    vertical1 = distance(
        upper1,
        lower1
    )

    vertical2 = distance(
        upper2,
        lower2
    )

    horizontal = distance(
        left,
        right
    )


    if horizontal <= 0:
        return 0.0


    return (
        vertical1 + vertical2
    ) / (
        2.0 * horizontal
    )


def calculate_mar(
    landmarks,
    width,
    height
):

    left = point(
        landmarks,
        MOUTH_LEFT,
        width,
        height
    )

    right = point(
        landmarks,
        MOUTH_RIGHT,
        width,
        height
    )

    upper = point(
        landmarks,
        MOUTH_UPPER,
        width,
        height
    )

    lower = point(
        landmarks,
        MOUTH_LOWER,
        width,
        height
    )


    vertical = distance(
        upper,
        lower
    )

    horizontal = distance(
        left,
        right
    )


    if horizontal <= 0:
        return 0.0


    return vertical / horizontal


def draw_point(
    frame,
    landmarks,
    index,
    width,
    height,
    color
):

    p = point(
        landmarks,
        index,
        width,
        height
    )

    cv2.circle(
        frame,
        p,
        3,
        color,
        -1
    )


# ============================================================
# TEMPORAL STATE
# ============================================================

ear_buffer = deque(
    maxlen=EAR_SMOOTHING_FRAMES
)

mar_buffer = deque(
    maxlen=MAR_SMOOTHING_FRAMES
)


eye_state = "OPEN"

close_counter = 0
open_counter = 0

blink_count = 0

eye_closed_start = None
closed_duration = 0.0


yawn_state = False

yawn_candidate_start = None
yawn_stop_start = None

yawn_count = 0


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("Camera error")

    detector.close()

    exit()


start_time = time.time()


print("Stable EAR/MAR detector started")
print("Press Q to quit")


# ============================================================
# MAIN LOOP
# ============================================================

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


    if result.face_landmarks:

        landmarks = result.face_landmarks[0]

        h, w = frame.shape[:2]


        # ====================================================
        # RAW EAR
        # ====================================================

        left_ear = calculate_ear(
            landmarks,
            LEFT_EYE,
            w,
            h
        )


        right_ear = calculate_ear(
            landmarks,
            RIGHT_EYE,
            w,
            h
        )


        raw_ear = (
            left_ear +
            right_ear
        ) / 2.0


        # ====================================================
        # RAW MAR
        # ====================================================

        raw_mar = calculate_mar(
            landmarks,
            w,
            h
        )


        # ====================================================
        # SMOOTHING
        # ====================================================

        ear_buffer.append(
            raw_ear
        )

        mar_buffer.append(
            raw_mar
        )


        # Median is more resistant to one bad frame
        smooth_ear = float(
            np.median(
                ear_buffer
            )
        )


        smooth_mar = float(
            np.median(
                mar_buffer
            )
        )


        # ====================================================
        # STABLE EYE STATE
        # ====================================================

        if eye_state == "OPEN":

            # Only consider closing when EAR goes
            # substantially below normal open EAR.

            if (
                smooth_ear <
                EYE_CLOSE_THRESHOLD
            ):

                close_counter += 1

            else:

                close_counter = 0


            if (
                close_counter >=
                EYE_CONFIRM_FRAMES
            ):

                eye_state = "CLOSED"

                eye_closed_start = time.time()

                close_counter = 0

                open_counter = 0


        else:

            # CLOSED -> OPEN requires a HIGHER threshold.
            # This hysteresis prevents flicker.

            if (
                smooth_ear >
                EYE_OPEN_THRESHOLD
            ):

                open_counter += 1

            else:

                open_counter = 0


            if (
                open_counter >=
                EYE_CONFIRM_FRAMES
            ):

                eye_state = "OPEN"

                blink_count += 1

                eye_closed_start = None

                closed_duration = 0.0

                open_counter = 0

                close_counter = 0


        # ====================================================
        # CLOSED DURATION
        # ====================================================

        if (
            eye_state == "CLOSED"
            and
            eye_closed_start is not None
        ):

            closed_duration = (
                time.time()
                -
                eye_closed_start
            )

        else:

            closed_duration = 0.0


        # ====================================================
        # STABLE YAWN STATE
        # ====================================================

        if not yawn_state:

            # Potential yawn
            if (
                smooth_mar >
                MAR_YAWN_START
            ):

                if yawn_candidate_start is None:

                    yawn_candidate_start = (
                        time.time()
                    )


                candidate_duration = (
                    time.time()
                    -
                    yawn_candidate_start
                )


                # Must remain open long enough
                if (
                    candidate_duration >=
                    YAWN_CONFIRM_SECONDS
                ):

                    yawn_state = True

                    yawn_count += 1

                    yawn_candidate_start = None

                    yawn_stop_start = None


            else:

                yawn_candidate_start = None


        else:

            # Once yawning, don't immediately stop it.
            # MAR must fall significantly.

            if (
                smooth_mar <
                MAR_YAWN_STOP
            ):

                if yawn_stop_start is None:

                    yawn_stop_start = (
                        time.time()
                    )


                stop_duration = (
                    time.time()
                    -
                    yawn_stop_start
                )


                if (
                    stop_duration >=
                    YAWN_STOP_SECONDS
                ):

                    yawn_state = False

                    yawn_stop_start = None


            else:

                yawn_stop_start = None


        # ====================================================
        # DRAW IMPORTANT LANDMARKS
        # ====================================================

        for idx in LEFT_EYE.values():

            draw_point(
                frame,
                landmarks,
                idx,
                w,
                h,
                (0, 255, 0)
            )


        for idx in RIGHT_EYE.values():

            draw_point(
                frame,
                landmarks,
                idx,
                w,
                h,
                (0, 255, 0)
            )


        for idx in [
            MOUTH_LEFT,
            MOUTH_RIGHT,
            MOUTH_UPPER,
            MOUTH_LOWER
        ]:

            draw_point(
                frame,
                landmarks,
                idx,
                w,
                h,
                (255, 0, 255)
            )


        # ====================================================
        # COLORS
        # ====================================================

        if eye_state == "OPEN":

            eye_color = (
                0,
                255,
                0
            )

        else:

            eye_color = (
                0,
                0,
                255
            )


        if yawn_state:

            mouth_color = (
                0,
                0,
                255
            )

        else:

            mouth_color = (
                0,
                255,
                0
            )


        # ====================================================
        # DISPLAY
        # ====================================================

        cv2.putText(
            frame,
            f"EAR raw: {raw_ear:.3f}",
            (20, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            f"EAR smooth: {smooth_ear:.3f}",
            (20, 65),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            f"EYES: {eye_state}",
            (20, 105),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            eye_color,
            3
        )


        cv2.putText(
            frame,
            f"Closed: {closed_duration:.1f}s",
            (20, 140),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            f"Blinks: {blink_count}",
            (20, 170),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            f"MAR raw: {raw_mar:.3f}",
            (20, 215),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        cv2.putText(
            frame,
            f"MAR smooth: {smooth_mar:.3f}",
            (20, 245),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2
        )


        yawn_text = (
            "YAWN"
            if yawn_state
            else "NO YAWN"
        )


        cv2.putText(
            frame,
            f"YAWN: {yawn_text}",
            (20, 285),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            mouth_color,
            3
        )


        cv2.putText(
            frame,
            f"Yawns: {yawn_count}",
            (20, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
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
        "Stable Eye + Yawn Detection",
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