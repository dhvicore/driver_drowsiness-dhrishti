import cv2
import numpy as np
import tensorflow as tf


# =========================================================
# LOAD BOTH EYE MODELS
# =========================================================

print("Loading eye_model.keras...")
model_a = tf.keras.models.load_model(
    "eye_model.keras"
)

print("Loading eye_state_mobilenetv2.keras...")
model_b = tf.keras.models.load_model(
    "eye_state_mobilenetv2.keras"
)

print("Both models loaded.")


# =========================================================
# FACE DETECTOR
# =========================================================

face_cascade = cv2.CascadeClassifier(
    cv2.data.haarcascades
    + "haarcascade_frontalface_default.xml"
)


# =========================================================
# PREPROCESSING METHODS
# =========================================================

def prepare_raw(img):

    img = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )

    img = cv2.resize(
        img,
        (224, 224)
    )

    img = img.astype(
        np.float32
    )

    return np.expand_dims(
        img,
        axis=0
    )


def prepare_mobilenet(img):

    img = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2RGB
    )

    img = cv2.resize(
        img,
        (224, 224)
    )

    img = img.astype(
        np.float32
    )

    img = tf.keras.applications.mobilenet_v2.preprocess_input(
        img
    )

    return np.expand_dims(
        img,
        axis=0
    )


# =========================================================
# CAMERA
# =========================================================

cap = cv2.VideoCapture(0)

if not cap.isOpened():

    print("Camera could not open.")
    exit()


print("Eye comparison running.")
print("Press Q to quit.")


# =========================================================
# LOOP
# =========================================================

while True:

    ret, frame = cap.read()

    if not ret:
        break


    frame = cv2.flip(
        frame,
        1
    )


    gray = cv2.cvtColor(
        frame,
        cv2.COLOR_BGR2GRAY
    )


    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.08,
        minNeighbors=6,
        minSize=(140, 140)
    )


    if len(faces) > 0:

        x, y, w, h = max(
            faces,
            key=lambda box:
            box[2] * box[3]
        )


        face = frame[
            y:y+h,
            x:x+w
        ]


        # ================================================
        # TIGHT EYE REGION
        # ================================================

        eye_y1 = int(
            h * 0.29
        )

        eye_y2 = int(
            h * 0.43
        )


        # left side
        lx1 = int(
            w * 0.12
        )

        lx2 = int(
            w * 0.47
        )


        # right side
        rx1 = int(
            w * 0.53
        )

        rx2 = int(
            w * 0.88
        )


        left_eye = face[
            eye_y1:eye_y2,
            lx1:lx2
        ]


        right_eye = face[
            eye_y1:eye_y2,
            rx1:rx2
        ]


        if (
            left_eye.size > 0
            and
            right_eye.size > 0
        ):

            # ==========================================
            # RAW 0-255
            # ==========================================

            l_raw = prepare_raw(
                left_eye
            )

            r_raw = prepare_raw(
                right_eye
            )


            a_raw_left = float(
                model_a.predict(
                    l_raw,
                    verbose=0
                )[0][0]
            )

            a_raw_right = float(
                model_a.predict(
                    r_raw,
                    verbose=0
                )[0][0]
            )


            b_raw_left = float(
                model_b.predict(
                    l_raw,
                    verbose=0
                )[0][0]
            )

            b_raw_right = float(
                model_b.predict(
                    r_raw,
                    verbose=0
                )[0][0]
            )


            a_raw = (
                a_raw_left
                +
                a_raw_right
            ) / 2


            b_raw = (
                b_raw_left
                +
                b_raw_right
            ) / 2


            # ==========================================
            # MOBILENET PREPROCESSING
            # ==========================================

            l_mob = prepare_mobilenet(
                left_eye
            )

            r_mob = prepare_mobilenet(
                right_eye
            )


            a_mob = (

                float(
                    model_a.predict(
                        l_mob,
                        verbose=0
                    )[0][0]
                )

                +

                float(
                    model_a.predict(
                        r_mob,
                        verbose=0
                    )[0][0]
                )

            ) / 2


            b_mob = (

                float(
                    model_b.predict(
                        l_mob,
                        verbose=0
                    )[0][0]
                )

                +

                float(
                    model_b.predict(
                        r_mob,
                        verbose=0
                    )[0][0]
                )

            ) / 2


            # ==========================================
            # DRAW EYE BOXES
            # ==========================================

            cv2.rectangle(
                frame,
                (
                    x + lx1,
                    y + eye_y1
                ),
                (
                    x + lx2,
                    y + eye_y2
                ),
                (255, 255, 0),
                2
            )


            cv2.rectangle(
                frame,
                (
                    x + rx1,
                    y + eye_y1
                ),
                (
                    x + rx2,
                    y + eye_y2
                ),
                (255, 255, 0),
                2
            )


            # ==========================================
            # DISPLAY RESULTS
            # ==========================================

            cv2.putText(
                frame,
                f"eye_model RAW: {a_raw:.3f}",
                (20, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"eye_model MOB: {a_mob:.3f}",
                (20, 75),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (255, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"state_model RAW: {b_raw:.3f}",
                (20, 110),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 255),
                2
            )


            cv2.putText(
                frame,
                f"state_model MOB: {b_mob:.3f}",
                (20, 145),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.75,
                (0, 255, 255),
                2
            )


            cv2.imshow(
                "LEFT EYE CROP",
                left_eye
            )

            cv2.imshow(
                "RIGHT EYE CROP",
                right_eye
            )


    cv2.imshow(
        "Eye Model Comparison",
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

cv2.destroyAllWindows()