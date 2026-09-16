from ultralytics import YOLO
import time


class DistractionDetector:

    def __init__(self):

        print("Loading YOLO phone detector...")

        self.model = YOLO(
            "yolov8n.pt"
        )

        self.phone_start = None

        self.phone_active = False


    def detect_phone(
        self,
        frame
    ):

        results = self.model(
            frame,
            verbose=False,
            conf=0.35
        )


        phone_detected = False

        boxes_out = []


        for result in results:

            for box in result.boxes:

                cls_id = int(
                    box.cls[0]
                )

                name = self.model.names[
                    cls_id
                ]


                if name == "cell phone":

                    phone_detected = True

                    x1, y1, x2, y2 = map(
                        int,
                        box.xyxy[0]
                    )

                    boxes_out.append(
                        (
                            x1,
                            y1,
                            x2,
                            y2
                        )
                    )


        now = time.time()


        if phone_detected:

            if self.phone_start is None:

                self.phone_start = now


            duration = (
                now -
                self.phone_start
            )


            if duration >= 1.0:

                self.phone_active = True


        else:

            self.phone_start = None

            self.phone_active = False

            duration = 0


        return (
            self.phone_active,
            boxes_out,
            duration
        )