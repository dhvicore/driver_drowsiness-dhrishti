import cv2

from phone_detector import PhoneDetector


# ============================================================
# LOAD PHONE DETECTOR
# ============================================================

detector = PhoneDetector()


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

    exit()


print("")
print("======================================")
print(" SMALL / DISTANT PHONE DETECTION TEST")
print("======================================")
print("")
print("Test:")
print(" - Phone near face")
print(" - Phone near chest")
print(" - Phone lower in frame")
print(" - Phone screen facing camera")
print(" - Phone back facing camera")
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


    # Mirror webcam
    frame = cv2.flip(
        frame,
        1
    )


    # ========================================================
    # PHONE DETECTION
    # ========================================================

    phone = detector.detect(
        frame
    )


    detected = phone[
        "detected"
    ]

    using = phone[
        "using"
    ]

    duration = phone[
        "duration"
    ]

    confidence = phone[
        "confidence"
    ]

    box = phone[
        "box"
    ]

    current_found = phone[
        "current_found"
    ]

    positive_frames = phone[
        "positive_frames"
    ]


    # ========================================================
    # DRAW PHONE BOX
    # ========================================================

    if box is not None:

        x1, y1, x2, y2 = box


        cv2.rectangle(

            frame,

            (x1, y1),

            (x2, y2),

            (255, 0, 255),

            3
        )


        cv2.putText(

            frame,

            f"PHONE {confidence:.2f}",

            (
                x1,
                max(
                    30,
                    y1 - 10
                )
            ),

            cv2.FONT_HERSHEY_SIMPLEX,

            0.7,

            (255, 0, 255),

            2
        )


    # ========================================================
    # DETERMINE DISPLAY STATUS
    # ========================================================

    if using:

        status = "PHONE USE"

        color = (
            0,
            0,
            255
        )


    elif detected:

        status = "PHONE DETECTED"

        color = (
            0,
            255,
            255
        )


    else:

        status = "NO PHONE"

        color = (
            0,
            255,
            0
        )


    # ========================================================
    # MAIN STATUS
    # ========================================================

    cv2.putText(

        frame,

        f"PHONE: {status}",

        (20, 50),

        cv2.FONT_HERSHEY_SIMPLEX,

        1.0,

        color,

        3
    )


    # ========================================================
    # CONFIDENCE
    # ========================================================

    cv2.putText(

        frame,

        f"Confidence: {confidence:.2f}",

        (20, 90),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (255, 255, 255),

        2
    )


    # ========================================================
    # DURATION
    # ========================================================

    cv2.putText(

        frame,

        f"Duration: {duration:.1f}s",

        (20, 125),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (255, 255, 255),

        2
    )


    # ========================================================
    # RAW YOLO RESULT
    # ========================================================

    if current_found:

        raw_text = "YES"

        raw_color = (
            0,
            255,
            0
        )

    else:

        raw_text = "NO"

        raw_color = (
            0,
            0,
            255
        )


    cv2.putText(

        frame,

        f"YOLO this frame: {raw_text}",

        (20, 160),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        raw_color,

        2
    )


    # ========================================================
    # TEMPORAL HISTORY
    # ========================================================

    cv2.putText(

        frame,

        f"Recent detections: {positive_frames}/10",

        (20, 195),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.65,

        (255, 255, 255),

        2
    )


    # ========================================================
    # MODEL INFO
    # ========================================================

    cv2.putText(

        frame,

        "YOLO11s | Input: 960",

        (20, 230),

        cv2.FONT_HERSHEY_SIMPLEX,

        0.55,

        (180, 180, 180),

        1
    )


    # ========================================================
    # SHOW
    # ========================================================

    cv2.imshow(

        "Improved Phone Detection",

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

cv2.destroyAllWindows()