import cv2
import time
import os
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

# Smoothing prevents LEFT/RIGHT/FORWARD flickering
SMOOTHING_FRAMES = 7


# ============================================================
# DOWNLOAD MODEL IF NEEDED
# ============================================================

if not os.path.exists(MODEL_PATH):

    print("Downloading Face Landmarker...")

    urllib.request.urlretrieve(
        MODEL_URL,
        MODEL_PATH
    )


# ============================================================
# CREATE MEDIAPIPE DETECTOR
# ============================================================

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
# SMOOTHING BUFFERS
# ============================================================

pitch_buffer = deque(
    maxlen=SMOOTHING_FRAMES
)

yaw_buffer = deque(
    maxlen=SMOOTHING_FRAMES
)

roll_buffer = deque(
    maxlen=SMOOTHING_FRAMES
)


# ============================================================
# HELPER
# ============================================================

def point(
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


# ============================================================
# NORMALIZE ANGLE
# ============================================================

def normalize_pitch(angle):

    # OpenCV may return pitch around +/-180
    # instead of the smaller equivalent angle.

    if angle < -90:

        angle += 180

    elif angle > 90:

        angle -= 180

    return angle


# ============================================================
# HEAD POSE
# ============================================================

def calculate_head_pose(
    landmarks,
    width,
    height
):

    # --------------------------------------------------------
    # 2D IMAGE POINTS
    # --------------------------------------------------------

    image_points = np.array(
        [
            point(
                landmarks,
                1,
                width,
                height
            ),  # Nose

            point(
                landmarks,
                152,
                width,
                height
            ),  # Chin

            point(
                landmarks,
                33,
                width,
                height
            ),  # Left eye outer

            point(
                landmarks,
                263,
                width,
                height
            ),  # Right eye outer

            point(
                landmarks,
                61,
                width,
                height
            ),  # Left mouth

            point(
                landmarks,
                291,
                width,
                height
            )   # Right mouth
        ],
        dtype=np.float64
    )


    # --------------------------------------------------------
    # GENERIC 3D FACE MODEL
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # CAMERA MATRIX
    # --------------------------------------------------------

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


    # --------------------------------------------------------
    # SOLVE HEAD POSE
    # --------------------------------------------------------

    success, rotation_vector, translation_vector = (
        cv2.solvePnP(
            model_points,
            image_points,
            camera_matrix,
            distortion,
            flags=cv2.SOLVEPNP_ITERATIVE
        )
    )


    if not success:

        return None


    # --------------------------------------------------------
    # ROTATION MATRIX
    # --------------------------------------------------------

    rotation_matrix, _ = cv2.Rodrigues(
        rotation_vector
    )


    # --------------------------------------------------------
    # EULER ANGLES
    # --------------------------------------------------------

    angles, _, _, _, _, _ = (
        cv2.RQDecomp3x3(
            rotation_matrix
        )
    )


    pitch = float(
        angles[0]
    )

    yaw = float(
        angles[1]
    )

    roll = float(
        angles[2]
    )


    # ========================================================
    # FIX WEIRD +/-180 PITCH
    # ========================================================

    pitch = normalize_pitch(
        pitch
    )


    # ========================================================
    # MIRROR CORRECTION
    #
    # Camera image is flipped horizontally below.
    # ========================================================

    yaw = -yaw

    roll = -roll


    return (
        pitch,
        yaw,
        roll,
        image_points
    )


# ============================================================
# CAMERA
# ============================================================

cap = cv2.VideoCapture(0)


cap.set(
    cv2.CAP_PROP_FRAME_WIDTH,
    1280
)

cap.set(
    cv2.CAP_PROP_FRAME_HEIGHT,
    720
)


if not cap.isOpened():

    print("ERROR: Camera could not open.")

    detector.close()

    exit()


start_time = time.time()


print("")
print("====================================")
print(" HEAD POSE CALIBRATION")
print("====================================")
print("")
print("Test these positions:")
print("1. FORWARD")
print("2. LEFT")
print("3. RIGHT")
print("4. DOWN")
print("5. UP")
print("")
print("Send me Pitch + Yaw for each.")
print("")
print("Press Q to quit.")
print("")


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ret, frame = cap.read()


    if not ret:

        break


    # ========================================================
    # MIRROR WEBCAM
    # ========================================================

    frame = cv2.flip(
        frame,
        1
    )


    # ========================================================
    # CONVERT TO RGB
    # ========================================================

    rgb = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2RGB
    )


    mp_image = mp.Image(

        image_format=mp.ImageFormat.SRGB,

        data=rgb
    )


    timestamp_ms = int(
        (
            time.time()
            -
            start_time
        )
        * 1000
    )


    # ========================================================
    # FACE DETECTION
    # ========================================================

    result = detector.detect_for_video(
        mp_image,
        timestamp_ms
    )


    # ========================================================
    # FACE FOUND
    # ========================================================

    if result.face_landmarks:

        landmarks = (
            result.face_landmarks[0]
        )


        h, w = frame.shape[:2]


        pose = calculate_head_pose(
            landmarks,
            w,
            h
        )


        if pose is not None:

            (
                raw_pitch,
                raw_yaw,
                raw_roll,
                image_points
            ) = pose


            # =================================================
            # SMOOTH VALUES
            # =================================================

            pitch_buffer.append(
                raw_pitch
            )

            yaw_buffer.append(
                raw_yaw
            )

            roll_buffer.append(
                raw_roll
            )


            pitch = float(
                np.median(
                    pitch_buffer
                )
            )

            yaw = float(
                np.median(
                    yaw_buffer
                )
            )

            roll = float(
                np.median(
                    roll_buffer
                )
            )


            # =================================================
            # TEMPORARY DIRECTION CLASSIFICATION
            #
            # We will calibrate these after seeing YOUR values.
            # =================================================

            if yaw < -20:

                direction = "LEFT"


            elif yaw > 20:

                direction = "RIGHT"

            elif pitch < -15:

                  direction = "UP"

            elif pitch > 15:

              direction = "DOWN"

            else:

                direction = "FORWARD"


            # =================================================
            # DRAW ALL FACE LANDMARKS
            # =================================================

            for lm in landmarks:

                px = int(
                    lm.x * w
                )

                py = int(
                    lm.y * h
                )


                cv2.circle(
                    frame,
                    (px, py),
                    1,
                    (50, 180, 50),
                    -1
                )


            # =================================================
            # DRAW IMPORTANT POSE POINTS
            # =================================================

            for p in image_points:

                cv2.circle(
                    frame,
                    (
                        int(p[0]),
                        int(p[1])
                    ),
                    5,
                    (0, 255, 255),
                    -1
                )


            # =================================================
            # COLOR
            # =================================================

            if direction == "FORWARD":

                color = (
                    0,
                    255,
                    0
                )

            else:

                color = (
                    0,
                    255,
                    255
                )


            # =================================================
            # DISPLAY
            # =================================================

            cv2.putText(
                frame,
                f"HEAD: {direction}",
                (20, 50),
                cv2.FONT_HERSHEY_SIMPLEX,
                1.0,
                color,
                3
            )


            cv2.putText(
                frame,
                f"Pitch: {pitch:.1f}",
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Yaw: {yaw:.1f}",
                (20, 135),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"Roll: {roll:.1f}",
                (20, 175),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.8,
                (255, 255, 255),
                2
            )


            # =================================================
            # RAW VALUES FOR DEBUGGING
            # =================================================

            cv2.putText(
                frame,
                f"Raw Pitch: {raw_pitch:.1f}",
                (20, 220),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (180, 180, 180),
                1
            )


            cv2.putText(
                frame,
                f"Raw Yaw: {raw_yaw:.1f}",
                (20, 245),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (180, 180, 180),
                1
            )


    # ========================================================
    # NO FACE
    # ========================================================

    else:

        pitch_buffer.clear()
        yaw_buffer.clear()
        roll_buffer.clear()


        cv2.putText(
            frame,
            "NO FACE DETECTED",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.0,
            (0, 0, 255),
            3
        )


    # ========================================================
    # DISPLAY
    # ========================================================

    cv2.imshow(
        "Head Pose Calibration",
        frame
    )


    if (
        cv2.waitKey(1)
        & 0xFF
        ==
        ord("q")
    ):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

detector.close()

cv2.destroyAllWindows()