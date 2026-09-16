import cv2
import time
import os
import math
import urllib.request
import mediapipe as mp

from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from temporal_engine import TemporalEngine
from head_pose import HeadPoseDetector
from phone_detector import PhoneDetector


# ============================================================
# CONFIGURATION
# ============================================================

FACE_MODEL_PATH = "face_landmarker.task"

FACE_MODEL_URL = (
    "https://storage.googleapis.com/"
    "mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/"
    "face_landmarker.task"
)

# Phone detection is expensive because phone_detector.py
# performs tiled YOLO inference.
#
# Run it periodically rather than every webcam frame.
PHONE_DETECT_INTERVAL = 8


# ============================================================
# DOWNLOAD MEDIAPIPE MODEL IF NEEDED
# ============================================================

if not os.path.exists(FACE_MODEL_PATH):

    print("Downloading MediaPipe Face Landmarker...")

    urllib.request.urlretrieve(
        FACE_MODEL_URL,
        FACE_MODEL_PATH
    )


# ============================================================
# MEDIAPIPE FACE LANDMARKER
# ============================================================

base_options = python.BaseOptions(
    model_asset_path=FACE_MODEL_PATH
)

options = vision.FaceLandmarkerOptions(

    base_options=base_options,

    running_mode=vision.RunningMode.VIDEO,

    num_faces=1,

    min_face_detection_confidence=0.5,

    min_face_presence_confidence=0.5,

    min_tracking_confidence=0.5
)

face_detector = (
    vision.FaceLandmarker.create_from_options(
        options
    )
)


# ============================================================
# LOAD ENGINES
# ============================================================

print("Loading driver monitoring system...")

temporal_engine = TemporalEngine()

head_detector = HeadPoseDetector()

phone_detector = PhoneDetector()


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


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_point(
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


def distance(p1, p2):

    return math.sqrt(

        (p1[0] - p2[0]) ** 2

        +

        (p1[1] - p2[1]) ** 2
    )


# ============================================================
# EAR
# ============================================================

def calculate_ear(
    landmarks,
    eye,
    width,
    height
):

    left = get_point(
        landmarks,
        eye["left"],
        width,
        height
    )

    right = get_point(
        landmarks,
        eye["right"],
        width,
        height
    )

    upper1 = get_point(
        landmarks,
        eye["upper1"],
        width,
        height
    )

    lower1 = get_point(
        landmarks,
        eye["lower1"],
        width,
        height
    )

    upper2 = get_point(
        landmarks,
        eye["upper2"],
        width,
        height
    )

    lower2 = get_point(
        landmarks,
        eye["lower2"],
        width,
        height
    )


    horizontal = distance(
        left,
        right
    )


    if horizontal <= 0:

        return 0.0


    vertical1 = distance(
        upper1,
        lower1
    )

    vertical2 = distance(
        upper2,
        lower2
    )


    return (

        vertical1
        +
        vertical2

    ) / (

        2.0
        *
        horizontal

    )


# ============================================================
# MAR
# ============================================================

def calculate_mar(
    landmarks,
    width,
    height
):

    left = get_point(
        landmarks,
        MOUTH_LEFT,
        width,
        height
    )

    right = get_point(
        landmarks,
        MOUTH_RIGHT,
        width,
        height
    )

    upper = get_point(
        landmarks,
        MOUTH_UPPER,
        width,
        height
    )

    lower = get_point(
        landmarks,
        MOUTH_LOWER,
        width,
        height
    )


    horizontal = distance(
        left,
        right
    )


    if horizontal <= 0:

        return 0.0


    vertical = distance(
        upper,
        lower
    )


    return (
        vertical
        /
        horizontal
    )


# ============================================================
# DRAW ONE LANDMARK
# ============================================================

def draw_landmark(
    frame,
    landmarks,
    index,
    width,
    height,
    color,
    radius=3
):

    p = get_point(
        landmarks,
        index,
        width,
        height
    )

    cv2.circle(
        frame,
        p,
        radius,
        color,
        -1
    )


# ============================================================
# COLORS
# ============================================================

GREEN = (0, 255, 0)

YELLOW = (0, 255, 255)

ORANGE = (0, 165, 255)

RED = (0, 0, 255)

WHITE = (255, 255, 255)

GRAY = (180, 180, 180)

MAGENTA = (255, 0, 255)

CYAN = (255, 255, 0)


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

    face_detector.close()

    exit()


# ============================================================
# PHONE STATE CACHE
# ============================================================

last_phone_result = {

    "detected": False,

    "using": False,

    "duration": 0.0,

    "confidence": 0.0,

    "box": None,

    "current_found": False,

    "positive_frames": 0,

    "source": "NONE"
}


frame_count = 0

start_time = time.time()


print()
print("==============================================")
print(" FINAL DRIVER MONITORING BACKEND")
print("==============================================")
print()
print("Drowsiness:")
print("  EAR + MAR + PERCLOS + temporal analysis")
print()
print("Distraction:")
print("  Head pose + YOLO phone detection")
print()
print("Press Q to quit.")
print()


# ============================================================
# MAIN LOOP
# ============================================================

while True:

    ret, frame = cap.read()


    if not ret:

        print("Camera frame error.")

        break


    frame_count += 1


    # Mirror webcam
    frame = cv2.flip(
        frame,
        1
    )


    h, w = frame.shape[:2]


    # ========================================================
    # PHONE DETECTION
    #
    # Run YOLO only every N frames.
    # ========================================================

    if (
        frame_count
        %
        PHONE_DETECT_INTERVAL
        ==
        0
    ):

        last_phone_result = (
            phone_detector.detect(
                frame
            )
        )


    phone = last_phone_result


    phone_detected = phone[
        "detected"
    ]

    phone_using = phone[
        "using"
    ]

    phone_duration = phone[
        "duration"
    ]

    phone_confidence = phone[
        "confidence"
    ]

    phone_box = phone[
        "box"
    ]

    phone_source = phone.get(
        "source",
        "NONE"
    )


    # ========================================================
    # DRAW PHONE BOX
    # ========================================================

    if (
        phone_detected
        and
        phone_box is not None
    ):

        x1, y1, x2, y2 = (
            phone_box
        )


        cv2.rectangle(
            frame,
            (x1, y1),
            (x2, y2),
            MAGENTA,
            3
        )


        cv2.putText(
            frame,
            f"PHONE {phone_confidence:.2f}",
            (
                x1,
                max(
                    30,
                    y1 - 10
                )
            ),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            MAGENTA,
            2
        )


    # ========================================================
    # MEDIAPIPE
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


    result = (
        face_detector.detect_for_video(
            mp_image,
            timestamp_ms
        )
    )


    # ========================================================
    # FACE FOUND
    # ========================================================

    if result.face_landmarks:

        landmarks = (
            result.face_landmarks[0]
        )


        # ====================================================
        # EAR
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

            left_ear
            +
            right_ear

        ) / 2.0


        # ====================================================
        # MAR
        # ====================================================

        raw_mar = calculate_mar(
            landmarks,
            w,
            h
        )


        # ====================================================
        # TEMPORAL DROWSINESS ENGINE
        # ====================================================

        state = temporal_engine.update(
            raw_ear,
            raw_mar
        )


        eye_state = state[
            "eye_state"
        ]

        smooth_ear = state[
            "ear"
        ]

        smooth_mar = state[
            "mar"
        ]

        closed_duration = state[
            "closed_duration"
        ]

        blink_count = state[
            "blink_count"
        ]

        perclos = state[
            "perclos"
        ]

        yawn_state = state[
            "yawn"
        ]

        yawn_count = state[
            "yawn_count"
        ]

        recent_yawns = state[
            "recent_yawns"
        ]

        recent_long_closures = state[
            "recent_long_closures"
        ]

        evidence_score = state[
            "target_score"
        ]

        drowsiness_score = state[
            "score"
        ]

        drowsiness_status = state[
            "status"
        ]


        # ====================================================
        # HEAD POSE
        # ====================================================

        head = head_detector.calculate(
            landmarks,
            w,
            h
        )


        head_direction = head[
            "direction"
        ]

        head_duration = head[
            "duration"
        ]

        head_distracted = head[
            "distracted"
        ]

        pitch = head[
            "pitch"
        ]

        yaw = head[
            "yaw"
        ]


        # ====================================================
        # DISTRACTION SCORE
        # ====================================================

        distraction_score = 0


        # ----------------------------------------------------
        # HEAD POSE CONTRIBUTION
        # ----------------------------------------------------

        if head_direction in [
            "LEFT",
            "RIGHT",
            "UP"
        ]:

            if head_duration >= 3.0:

                distraction_score += 75

            elif head_duration >= 1.5:

                distraction_score += 55

            elif head_duration >= 1.0:

                distraction_score += 35

            elif head_duration >= 0.5:

                distraction_score += 15


        elif head_direction == "DOWN":

            # Looking down is particularly relevant
            # to phone / dashboard distraction.

            if head_duration >= 2.5:

                distraction_score += 80

            elif head_duration >= 1.2:

                distraction_score += 60

            elif head_duration >= 0.8:

                distraction_score += 40

            elif head_duration >= 0.4:

                distraction_score += 20


        # ----------------------------------------------------
        # PHONE CONTRIBUTION
        # ----------------------------------------------------

        if phone_detected:

            distraction_score += 15


        if phone_using:

            distraction_score += 35


        # ----------------------------------------------------
        # PHONE + HEAD-DOWN FUSION
        # ----------------------------------------------------

        if (
            phone_using
            and
            head_direction == "DOWN"
        ):

            distraction_score += 40


        # Phone + sustained looking away
        elif (
            phone_using
            and
            head_direction
            in [
                "LEFT",
                "RIGHT"
            ]
            and
            head_duration >= 1.0
        ):

            distraction_score += 25


        distraction_score = min(
            distraction_score,
            100
        )


        # ====================================================
        # ATTENTION STATUS
        # ====================================================

        if (
            phone_using
            and
            head_direction == "DOWN"
        ):

            attention_status = (
                "PHONE DISTRACTION"
            )


        elif (
            phone_using
            and
            head_distracted
        ):

            attention_status = (
                "PHONE DISTRACTION"
            )


        elif phone_using:

            attention_status = (
                "PHONE USE"
            )


        elif head_distracted:

            attention_status = (
                "DISTRACTED"
            )


        elif (
            head_direction
            !=
            "FORWARD"
        ):

            attention_status = (
                "LOOKING AWAY"
            )


        else:

            attention_status = (
                "ATTENTIVE"
            )


        # ====================================================
        # FINAL DRIVER STATE
        # ====================================================

        # Severe active drowsiness always wins.
        if drowsiness_status == "CRITICAL":

            final_status = "CRITICAL"


        # Drowsiness + strong distraction simultaneously
        elif (
            drowsiness_status == "DROWSY"
            and
            distraction_score >= 60
        ):

            final_status = "CRITICAL"


        # Strong drowsiness
        elif drowsiness_status == "DROWSY":

            final_status = "DROWSY"


        # Strong phone distraction
        elif (
            phone_using
            and
            head_direction == "DOWN"
        ):

            final_status = (
                "DISTRACTED"
            )


        elif distraction_score >= 60:

            final_status = (
                "DISTRACTED"
            )


        # Fatigue
        elif drowsiness_status == "FATIGUED":

            final_status = (
                "FATIGUED"
            )


        # Mild distraction
        elif (
            head_distracted
            or
            phone_using
        ):

            final_status = (
                "DISTRACTED"
            )


        else:

            final_status = "ALERT"


        # ====================================================
        # COLORS
        # ====================================================

        eye_color = (

            GREEN
            if eye_state == "OPEN"
            else RED

        )


        yawn_color = (

            RED
            if yawn_state
            else GREEN

        )


        if attention_status == "ATTENTIVE":

            attention_color = GREEN


        elif attention_status == "LOOKING AWAY":

            attention_color = YELLOW


        elif attention_status == "PHONE USE":

            attention_color = ORANGE


        else:

            attention_color = RED


        if final_status == "ALERT":

            final_color = GREEN


        elif final_status == "FATIGUED":

            final_color = YELLOW


        elif final_status == "DROWSY":

            final_color = ORANGE


        elif final_status == "DISTRACTED":

            final_color = MAGENTA


        else:

            final_color = RED


        # ====================================================
        # DRAW FACE LANDMARKS
        # ====================================================

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
                (50, 150, 50),
                -1
            )


        # ====================================================
        # HIGHLIGHT EYE LANDMARKS
        # ====================================================

        for idx in LEFT_EYE.values():

            draw_landmark(
                frame,
                landmarks,
                idx,
                w,
                h,
                YELLOW,
                3
            )


        for idx in RIGHT_EYE.values():

            draw_landmark(
                frame,
                landmarks,
                idx,
                w,
                h,
                YELLOW,
                3
            )


        # ====================================================
        # HIGHLIGHT MOUTH LANDMARKS
        # ====================================================

        for idx in [

            MOUTH_LEFT,
            MOUTH_RIGHT,
            MOUTH_UPPER,
            MOUTH_LOWER

        ]:

            draw_landmark(
                frame,
                landmarks,
                idx,
                w,
                h,
                MAGENTA,
                4
            )


        # ====================================================
        # LEFT PANEL — DROWSINESS
        # ====================================================

        x = 20


        cv2.putText(
            frame,
            f"EYES: {eye_state}",
            (x, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            eye_color,
            2
        )


        cv2.putText(
            frame,
            f"EAR: {smooth_ear:.3f}",
            (x, 67),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Closed: {closed_duration:.1f}s",
            (x, 97),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Blinks: {blink_count}",
            (x, 127),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"PERCLOS: {perclos:.2f}",
            (x, 157),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        yawn_text = (
            "YAWN"
            if yawn_state
            else
            "NO YAWN"
        )


        cv2.putText(
            frame,
            f"YAWN: {yawn_text}",
            (x, 202),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            yawn_color,
            2
        )


        cv2.putText(
            frame,
            f"MAR: {smooth_mar:.3f}",
            (x, 234),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Total yawns: {yawn_count}",
            (x, 264),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Recent yawns: {recent_yawns}",
            (x, 294),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Long closures: {recent_long_closures}",
            (x, 324),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Evidence: {evidence_score}/100",
            (x, 370),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.60,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Drowsiness: {drowsiness_score}/100",
            (x, 405),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            final_color,
            2
        )


        # ====================================================
        # RIGHT PANEL — ATTENTION
        # ====================================================

        panel_x = max(
            650,
            w - 390
        )


        head_color = (

            GREEN
            if head_direction == "FORWARD"
            else YELLOW

        )


        cv2.putText(
            frame,
            f"HEAD: {head_direction}",
            (panel_x, 35),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.75,
            head_color,
            2
        )


        cv2.putText(
            frame,
            f"Pitch: {pitch:.1f}",
            (panel_x, 67),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Yaw: {yaw:.1f}",
            (panel_x, 97),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Away: {head_duration:.1f}s",
            (panel_x, 127),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.58,
            WHITE,
            2
        )


        # ====================================================
        # PHONE PANEL
        # ====================================================

        if phone_using:

            phone_text = "PHONE USE"
            phone_color = RED


        elif phone_detected:

            phone_text = "DETECTED"
            phone_color = YELLOW


        else:

            phone_text = "NO PHONE"
            phone_color = GREEN


        cv2.putText(
            frame,
            f"PHONE: {phone_text}",
            (panel_x, 180),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.70,
            phone_color,
            2
        )


        cv2.putText(
            frame,
            f"Phone conf: {phone_confidence:.2f}",
            (panel_x, 212),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Phone time: {phone_duration:.1f}s",
            (panel_x, 242),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.55,
            WHITE,
            2
        )


        cv2.putText(
            frame,
            f"Source: {phone_source}",
            (panel_x, 272),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.50,
            GRAY,
            1
        )


        # ====================================================
        # DISTRACTION
        # ====================================================

        cv2.putText(
            frame,
            f"Distraction: {distraction_score}/100",
            (panel_x, 320),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            attention_color,
            2
        )


        cv2.putText(
            frame,
            f"ATTENTION: {attention_status}",
            (panel_x, 355),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.68,
            attention_color,
            2
        )


        # ====================================================
        # FINAL STATUS
        # ====================================================

        cv2.putText(
            frame,
            f"STATUS: {final_status}",
            (20, h - 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.15,
            final_color,
            3
        )


    # ========================================================
    # NO FACE
    # ========================================================

    else:

        head_detector.reset()


        cv2.putText(
            frame,
            "NO DRIVER DETECTED",
            (20, 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.9,
            RED,
            3
        )


        # Phone can still be shown even if face temporarily lost.
        if phone_using:

            cv2.putText(
                frame,
                "PHONE DETECTED - DRIVER FACE LOST",
                (20, 95),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.65,
                ORANGE,
                2
            )


    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(
        "Driver Monitoring System",
        frame
    )


    key = (
        cv2.waitKey(1)
        &
        0xFF
    )


    if key == ord("q"):

        break


# ============================================================
# CLEANUP
# ============================================================

cap.release()

face_detector.close()

cv2.destroyAllWindows()