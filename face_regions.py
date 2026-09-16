import cv2


class FaceRegionDetector:

    def __init__(self):

        self.face_cascade = cv2.CascadeClassifier(
            cv2.data.haarcascades
            + "haarcascade_frontalface_default.xml"
        )


    def detect(self, frame):

        gray = cv2.cvtColor(
            frame,
            cv2.COLOR_BGR2GRAY
        )

        faces = self.face_cascade.detectMultiScale(
            gray,
            scaleFactor=1.08,
            minNeighbors=6,
            minSize=(140, 140)
        )

        if len(faces) == 0:
            return None


        x, y, w, h = max(
            faces,
            key=lambda b: b[2] * b[3]
        )


        face = frame[
            y:y+h,
            x:x+w
        ]


        # ==================================================
        # TIGHT EYE CROPS
        # ==================================================

        # much tighter than previous version

        eye_y1 = int(h * 0.28)
        eye_y2 = int(h * 0.44)


        # left side of displayed image
        left_x1 = int(w * 0.10)
        left_x2 = int(w * 0.48)


        # right side
        right_x1 = int(w * 0.52)
        right_x2 = int(w * 0.90)


        left_eye = face[
            eye_y1:eye_y2,
            left_x1:left_x2
        ]


        right_eye = face[
            eye_y1:eye_y2,
            right_x1:right_x2
        ]


        # ==================================================
        # LOWER FACE / MOUTH
        # ==================================================

        mouth_y1 = int(h * 0.53)
        mouth_y2 = int(h * 0.90)

        mouth_x1 = int(w * 0.20)
        mouth_x2 = int(w * 0.80)


        mouth = face[
            mouth_y1:mouth_y2,
            mouth_x1:mouth_x2
        ]


        return {

            "bbox": (x, y, w, h),

            "face": face,

            "left_eye": left_eye,

            "right_eye": right_eye,

            "mouth": mouth,

            "eye_coordinates": (
                eye_y1,
                eye_y2,
                left_x1,
                left_x2,
                right_x1,
                right_x2
            ),

            "mouth_coordinates": (
                mouth_y1,
                mouth_y2,
                mouth_x1,
                mouth_x2
            )
        }