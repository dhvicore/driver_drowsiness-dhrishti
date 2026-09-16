import time
from collections import deque

import cv2
from ultralytics import YOLO


class PhoneDetector:

    def __init__(self):

        print("Loading YOLO11s tiled phone detector...")

        # ====================================================
        # MODEL
        # ====================================================

        self.model = YOLO("yolo11s.pt")

        # COCO cell-phone class
        self.PHONE_CLASS = 67

        # Full-frame confidence
        self.FULL_CONF = 0.20

        # Tile confidence can be slightly lower because
        # temporal logic filters occasional weak detections.
        self.TILE_CONF = 0.16

        # Full-frame inference resolution
        self.FULL_IMGSZ = 960

        # Tile inference resolution
        self.TILE_IMGSZ = 640


        # ====================================================
        # TEMPORAL SETTINGS
        # ====================================================

        self.history = deque(maxlen=10)

        self.MIN_POSITIVE_FRAMES = 3

        self.LOST_GRACE_SECONDS = 0.8

        self.PHONE_USE_SECONDS = 1.0


        # ====================================================
        # STATE
        # ====================================================

        self.phone_start = None

        self.last_seen_time = None

        self.phone_duration = 0.0

        self.phone_detected = False

        self.phone_using = False

        self.last_box = None

        self.last_confidence = 0.0

        self.last_source = "NONE"


    # ========================================================
    # RUN YOLO ON AN IMAGE
    # ========================================================

    def _run_yolo(
        self,
        image,
        confidence,
        imgsz
    ):

        results = self.model.predict(
            source=image,
            conf=confidence,
            imgsz=imgsz,
            verbose=False
        )

        detections = []

        for result in results:

            if result.boxes is None:
                continue

            for box in result.boxes:

                class_id = int(
                    box.cls[0].item()
                )

                if class_id != self.PHONE_CLASS:
                    continue

                conf = float(
                    box.conf[0].item()
                )

                coords = (
                    box.xyxy[0]
                    .cpu()
                    .numpy()
                    .astype(int)
                )

                x1, y1, x2, y2 = coords

                detections.append(
                    {
                        "confidence": conf,

                        "box": (
                            int(x1),
                            int(y1),
                            int(x2),
                            int(y2)
                        )
                    }
                )

        return detections


    # ========================================================
    # FULL-FRAME DETECTION
    # ========================================================

    def _detect_full_frame(self, frame):

        detections = self._run_yolo(
            frame,
            self.FULL_CONF,
            self.FULL_IMGSZ
        )

        if not detections:

            return None

        return max(
            detections,
            key=lambda d: d["confidence"]
        )


    # ========================================================
    # TILED DETECTION
    # ========================================================

    def _detect_tiles(self, frame):

        h, w = frame.shape[:2]

        candidates = []


        # ====================================================
        # OVERLAPPING TILES
        #
        # We deliberately use overlapping regions.
        #
        # This prevents a phone from being cut exactly at
        # a tile boundary.
        # ====================================================

        tiles = [

            # LEFT HALF
            (
                0,
                int(h * 0.20),
                int(w * 0.60),
                h
            ),

            # RIGHT HALF
            (
                int(w * 0.40),
                int(h * 0.20),
                w,
                h
            ),

            # LOWER LEFT
            (
                0,
                int(h * 0.45),
                int(w * 0.60),
                h
            ),

            # LOWER RIGHT
            (
                int(w * 0.40),
                int(h * 0.45),
                w,
                h
            ),

            # CENTER / DRIVER REGION
            (
                int(w * 0.15),
                int(h * 0.20),
                int(w * 0.85),
                h
            )
        ]


        # ====================================================
        # PROCESS EACH TILE
        # ====================================================

        for tile_index, (
            x_start,
            y_start,
            x_end,
            y_end
        ) in enumerate(tiles):

            crop = frame[
                y_start:y_end,
                x_start:x_end
            ]


            if crop.size == 0:
                continue


            crop_h, crop_w = crop.shape[:2]


            # =================================================
            # ENLARGE TILE
            #
            # Small phones now occupy substantially more pixels.
            # =================================================

            scale = 1.5

            enlarged = cv2.resize(
                crop,
                None,
                fx=scale,
                fy=scale,
                interpolation=cv2.INTER_CUBIC
            )


            detections = self._run_yolo(
                enlarged,
                self.TILE_CONF,
                self.TILE_IMGSZ
            )


            # =================================================
            # CONVERT TILE COORDINATES BACK TO FULL FRAME
            # =================================================

            for detection in detections:

                bx1, by1, bx2, by2 = (
                    detection["box"]
                )


                # Undo enlargement
                bx1 = int(bx1 / scale)
                by1 = int(by1 / scale)

                bx2 = int(bx2 / scale)
                by2 = int(by2 / scale)


                # Add tile offset
                full_x1 = bx1 + x_start
                full_y1 = by1 + y_start

                full_x2 = bx2 + x_start
                full_y2 = by2 + y_start


                # Clamp coordinates
                full_x1 = max(
                    0,
                    min(w - 1, full_x1)
                )

                full_y1 = max(
                    0,
                    min(h - 1, full_y1)
                )

                full_x2 = max(
                    0,
                    min(w - 1, full_x2)
                )

                full_y2 = max(
                    0,
                    min(h - 1, full_y2)
                )


                candidates.append(
                    {
                        "confidence":
                            detection["confidence"],

                        "box": (
                            full_x1,
                            full_y1,
                            full_x2,
                            full_y2
                        ),

                        "source":
                            f"TILE {tile_index + 1}"
                    }
                )


        if not candidates:

            return None


        return max(
            candidates,
            key=lambda d: d["confidence"]
        )


    # ========================================================
    # MAIN DETECTION
    # ========================================================

    def detect(self, frame):

        now = time.time()


        # ====================================================
        # 1. FULL FRAME
        # ====================================================

        full_detection = (
            self._detect_full_frame(frame)
        )


        # ====================================================
        # 2. TILED DETECTION
        # ====================================================

        tile_detection = (
            self._detect_tiles(frame)
        )


        # ====================================================
        # CHOOSE BEST DETECTION
        # ====================================================

        candidates = []


        if full_detection is not None:

            candidates.append(
                {
                    "confidence":
                        full_detection["confidence"],

                    "box":
                        full_detection["box"],

                    "source":
                        "FULL"
                }
            )


        if tile_detection is not None:

            candidates.append(
                tile_detection
            )


        # ====================================================
        # RAW RESULT
        # ====================================================

        if candidates:

            best = max(
                candidates,
                key=lambda d: d["confidence"]
            )

            current_found = True

            best_confidence = (
                best["confidence"]
            )

            best_box = (
                best["box"]
            )

            best_source = (
                best["source"]
            )

        else:

            current_found = False

            best_confidence = 0.0

            best_box = None

            best_source = "NONE"


        # ====================================================
        # TEMPORAL HISTORY
        # ====================================================

        self.history.append(
            1 if current_found else 0
        )


        positive_frames = sum(
            self.history
        )


        # ====================================================
        # CURRENT PHONE FOUND
        # ====================================================

        if current_found:

            self.last_seen_time = now

            self.last_box = best_box

            self.last_confidence = (
                best_confidence
            )

            self.last_source = (
                best_source
            )


        # ====================================================
        # LOST-FRAME GRACE PERIOD
        # ====================================================

        recently_seen = False


        if self.last_seen_time is not None:

            recently_seen = (

                now
                -
                self.last_seen_time

                <=

                self.LOST_GRACE_SECONDS
            )


        stable_detection = (

            positive_frames
            >=
            self.MIN_POSITIVE_FRAMES
        )


        self.phone_detected = (

            stable_detection
            or
            recently_seen
        )


        # ====================================================
        # PHONE USE TIMER
        # ====================================================

        if self.phone_detected:

            if self.phone_start is None:

                self.phone_start = now


            self.phone_duration = (

                now
                -
                self.phone_start
            )


            self.phone_using = (

                self.phone_duration
                >=
                self.PHONE_USE_SECONDS
            )


        else:

            self.phone_start = None

            self.phone_duration = 0.0

            self.phone_using = False

            self.last_box = None

            self.last_confidence = 0.0

            self.last_source = "NONE"


        # ====================================================
        # RETURN
        # ====================================================

        return {

            "detected":
                self.phone_detected,

            "using":
                self.phone_using,

            "duration":
                self.phone_duration,

            "confidence":
                self.last_confidence,

            "box":
                self.last_box,

            "current_found":
                current_found,

            "positive_frames":
                positive_frames,

            "source":
                self.last_source
        }