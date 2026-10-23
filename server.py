"""
Drishti — web server for the driver monitoring backend.

Runs the same pipeline as main.py (MediaPipe face landmarks -> EAR/MAR ->
TemporalEngine, HeadPoseDetector, PhoneDetector) but publishes the annotated
frames as MJPEG and the derived metrics as JSON instead of using cv2.imshow.

main.py is untouched and still runs standalone.
"""

import math
import queue
import numpy as np
import os
import threading
import time
import urllib.request
from collections import deque

import cv2
import mediapipe as mp
from flask import Flask, Response, jsonify, request
from flask_cors import CORS
from mediapipe.tasks import python
from mediapipe.tasks.python import vision

from head_pose import HeadPoseDetector
from phone_detector import PhoneDetector
from temporal_engine import TemporalEngine

FACE_MODEL_PATH = "face_landmarker.task"
FACE_MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/face_landmarker/"
    "face_landmarker/float16/1/face_landmarker.task"
)

PHONE_DETECT_INTERVAL = 8

# Webcam index by default; set DRISHTI_CAMERA to a file path to replay a clip.
_source = os.environ.get("DRISHTI_CAMERA", "0")
CAMERA_SOURCE = int(_source) if _source.isdigit() else _source

LEFT_EYE = {"left": 33, "right": 133, "upper1": 160, "lower1": 144, "upper2": 158, "lower2": 153}
RIGHT_EYE = {"left": 362, "right": 263, "upper1": 385, "lower1": 380, "upper2": 387, "lower2": 373}
MOUTH_LEFT, MOUTH_RIGHT, MOUTH_UPPER, MOUTH_LOWER = 61, 291, 13, 14

# BGR, matched to the frontend palette
INK = (245, 244, 244)
MESH = (130, 125, 120)
BLUE = (255, 107, 47)
BURGUNDY = (80, 58, 176)

# original main.py palette, used only when raw overlay is enabled
GREEN, YELLOW, ORANGE, RED, WHITE, GRAY, MAGENTA = (
    (0, 255, 0), (0, 255, 255), (0, 165, 255), (0, 0, 255),
    (255, 255, 255), (180, 180, 180), (255, 0, 255),
)

SEVERITY = {"ALERT": 0, "FATIGUED": 1, "DROWSY": 2, "DISTRACTED": 2, "CRITICAL": 3}


def _point(landmarks, index, width, height):
    lm = landmarks[index]
    return int(lm.x * width), int(lm.y * height)


def _distance(p1, p2):
    return math.hypot(p1[0] - p2[0], p1[1] - p2[1])


def calculate_ear(landmarks, eye, width, height):
    left = _point(landmarks, eye["left"], width, height)
    right = _point(landmarks, eye["right"], width, height)
    horizontal = _distance(left, right)
    if horizontal <= 0:
        return 0.0
    v1 = _distance(_point(landmarks, eye["upper1"], width, height),
                   _point(landmarks, eye["lower1"], width, height))
    v2 = _distance(_point(landmarks, eye["upper2"], width, height),
                   _point(landmarks, eye["lower2"], width, height))
    return (v1 + v2) / (2.0 * horizontal)


def calculate_mar(landmarks, width, height):
    horizontal = _distance(_point(landmarks, MOUTH_LEFT, width, height),
                           _point(landmarks, MOUTH_RIGHT, width, height))
    if horizontal <= 0:
        return 0.0
    vertical = _distance(_point(landmarks, MOUTH_UPPER, width, height),
                         _point(landmarks, MOUTH_LOWER, width, height))
    return vertical / horizontal


def score_distraction(head_direction, head_duration, phone_detected, phone_using):
    score = 0
    if head_direction in ("LEFT", "RIGHT", "UP"):
        for threshold, points in ((3.0, 75), (1.5, 55), (1.0, 35), (0.5, 15)):
            if head_duration >= threshold:
                score += points
                break
    elif head_direction == "DOWN":
        for threshold, points in ((2.5, 80), (1.2, 60), (0.8, 40), (0.4, 20)):
            if head_duration >= threshold:
                score += points
                break

    if phone_detected:
        score += 15
    if phone_using:
        score += 35

    if phone_using and head_direction == "DOWN":
        score += 40
    elif phone_using and head_direction in ("LEFT", "RIGHT") and head_duration >= 1.0:
        score += 25

    return min(score, 100)


def resolve_attention(phone_using, head_direction, head_distracted):
    if phone_using and (head_direction == "DOWN" or head_distracted):
        return "PHONE DISTRACTION"
    if phone_using:
        return "PHONE USE"
    if head_distracted:
        return "DISTRACTED"
    if head_direction != "FORWARD":
        return "LOOKING AWAY"
    return "ATTENTIVE"


def resolve_status(drowsiness_status, distraction_score, phone_using,
                   head_direction, head_distracted):
    if drowsiness_status == "CRITICAL":
        return "CRITICAL"
    if drowsiness_status == "DROWSY" and distraction_score >= 60:
        return "CRITICAL"
    if drowsiness_status == "DROWSY":
        return "DROWSY"
    if phone_using and head_direction == "DOWN":
        return "DISTRACTED"
    if distraction_score >= 60:
        return "DISTRACTED"
    if drowsiness_status == "FATIGUED":
        return "FATIGUED"
    if head_distracted or phone_using:
        return "DISTRACTED"
    return "ALERT"


class BrowserCapture:
    """A bounded queue of frames supplied by the browser camera."""

    def __init__(self):
        self.frames = queue.Queue(maxsize=1)
        self.closed = False

    def read(self):
        try:
            return True, self.frames.get(timeout=0.5)
        except queue.Empty:
            return False, None

    def submit(self, frame):
        try:
            self.frames.get_nowait()
        except queue.Empty:
            pass
        try:
            self.frames.put_nowait(frame)
        except queue.Full:
            pass

    def release(self):
        self.closed = True


class Monitor:
    """Owns the camera, the detectors, and the published frame/state."""

    def __init__(self):
        self._lock = threading.Lock()
        self._thread = None
        self._stop = threading.Event()

        self.running = False
        self.error = None
        self.raw_overlay = False

        self.frame_jpeg = None
        self.started_at = None
        self.fps = 0.0
        self.events = deque(maxlen=60)
        self.event_seq = 0
        self.metrics = self._blank_metrics()
        self.totals = {"yawns": 0, "long_closures": 0, "blinks": 0, "phone_events": 0}

        self._face_detector = None
        self._ensure_face_model()

    @staticmethod
    def _ensure_face_model():
        if not os.path.exists(FACE_MODEL_PATH):
            print("Downloading MediaPipe Face Landmarker...")
            urllib.request.urlretrieve(FACE_MODEL_URL, FACE_MODEL_PATH)

    @staticmethod
    def _blank_metrics():
        return {
            "face": False,
            "status": "STANDBY",
            "severity": 0,
            "attention": "—",
            "eye_state": "—",
            "ear": 0.0,
            "mar": 0.0,
            "closed_duration": 0.0,
            "blinks": 0,
            "perclos": 0.0,
            "yawn": False,
            "yawn_count": 0,
            "recent_yawns": 0,
            "recent_long_closures": 0,
            "evidence_score": 0,
            "drowsiness_score": 0,
            "drowsiness_status": "—",
            "head_direction": "—",
            "pitch": 0.0,
            "yaw": 0.0,
            "head_duration": 0.0,
            "head_distracted": False,
            "distraction_score": 0,
            "phone_detected": False,
            "phone_using": False,
            "phone_confidence": 0.0,
            "phone_duration": 0.0,
            "phone_source": "NONE",
        }

    def _log(self, level, message):
        self.event_seq += 1
        self.events.appendleft({
            "id": self.event_seq,
            "level": level,
            "message": message,
            "at": time.time(),
        })

    def start(self, browser=False):
        with self._lock:
            if self.running:
                return True, None

            capture = BrowserCapture() if browser else cv2.VideoCapture(CAMERA_SOURCE)
            self._capture = capture
            if not browser:
                capture.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
                capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
            if not browser and not capture.isOpened():
                capture.release()
                self.error = (
                    "Camera unavailable. Grant camera access to your terminal in "
                    "System Settings > Privacy & Security > Camera, then retry."
                )
                return False, self.error

            options = vision.FaceLandmarkerOptions(
                base_options=python.BaseOptions(model_asset_path=FACE_MODEL_PATH),
                running_mode=vision.RunningMode.VIDEO,
                num_faces=1,
                min_face_detection_confidence=0.5,
                min_face_presence_confidence=0.5,
                min_tracking_confidence=0.5,
            )

            self._face_detector = vision.FaceLandmarker.create_from_options(options)
            self._temporal = TemporalEngine()
            self._head = HeadPoseDetector()
            self._phone = PhoneDetector()

            self.error = None
            self.running = True
            self.started_at = time.time()
            self.metrics = self._blank_metrics()
            self.totals = {"yawns": 0, "long_closures": 0, "blinks": 0, "phone_events": 0}
            self.events.clear()
            self.event_seq = 0
            self._log("info", "Monitoring session started")

            self._stop.clear()
            self._thread = threading.Thread(target=self._loop, args=(capture,), daemon=True)
            self._thread.start()
            return True, None

    def stop(self):
        with self._lock:
            if not self.running:
                return
            self._stop.set()
            thread = self._thread

        if thread:
            thread.join(timeout=4)

        with self._lock:
            self.running = False
            self._thread = None
            self.frame_jpeg = None
            self.metrics = self._blank_metrics()
            self._log("info", "Monitoring session stopped")
            if self._face_detector:
                self._face_detector.close()
                self._face_detector = None

    def _loop(self, capture):
        frame_count = 0
        origin = time.time()
        last_tick = origin
        phone_cache = {"detected": False, "using": False, "duration": 0.0,
                       "confidence": 0.0, "box": None, "source": "NONE"}
        previous = {"status": "ALERT", "yawns": 0, "closures": 0, "phone": False}

        try:
            while not self._stop.is_set():
                ok, frame = capture.read()
                if not ok and isinstance(capture, BrowserCapture):
                    # Do not count camera/network gaps as continuous eye closure.
                    if time.time() - last_tick > 2:
                        self._temporal = TemporalEngine()
                        self._head.reset()
                        self.metrics = self._blank_metrics()
                        self.frame_jpeg = None
                    continue
                if not ok:
                    # A replayed clip just loops; a live camera has genuinely failed.
                    if isinstance(CAMERA_SOURCE, str):
                        capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        continue
                    self.error = "Camera frame error."
                    break

                frame_count += 1
                frame = cv2.flip(frame, 1)
                height, width = frame.shape[:2]

                if frame_count % PHONE_DETECT_INTERVAL == 0:
                    phone_cache = self._phone.detect(frame)

                metrics = self._blank_metrics()
                metrics.update({
                    "phone_detected": phone_cache["detected"],
                    "phone_using": phone_cache["using"],
                    "phone_confidence": round(float(phone_cache["confidence"]), 2),
                    "phone_duration": round(float(phone_cache["duration"]), 1),
                    "phone_source": phone_cache.get("source", "NONE"),
                })

                if phone_cache["detected"] and phone_cache["box"] is not None:
                    x1, y1, x2, y2 = phone_cache["box"]
                    cv2.rectangle(frame, (x1, y1), (x2, y2), BURGUNDY, 2)
                    cv2.putText(frame, f"PHONE {phone_cache['confidence']:.2f}",
                                (x1, max(26, y1 - 10)), cv2.FONT_HERSHEY_SIMPLEX,
                                0.6, BURGUNDY, 2)

                mp_image = mp.Image(image_format=mp.ImageFormat.SRGB,
                                    data=cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
                result = self._face_detector.detect_for_video(
                    mp_image, int((time.time() - origin) * 1000))

                if result.face_landmarks:
                    landmarks = result.face_landmarks[0]
                    self._analyse(frame, landmarks, width, height, metrics, phone_cache)
                else:
                    self._head.reset()
                    metrics["status"] = "NO DRIVER"
                    metrics["severity"] = 1

                now = time.time()
                self.fps = round(1.0 / max(now - last_tick, 1e-6), 1)
                last_tick = now

                if self.raw_overlay:
                    self._draw_raw_overlay(frame, metrics, width, height)

                encoded, buffer = cv2.imencode(
                    ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 80])
                if encoded:
                    self.frame_jpeg = buffer.tobytes()

                self._emit_events(metrics, previous)
                self.metrics = metrics
        finally:
            capture.release()
            self.running = False

    def _analyse(self, frame, landmarks, width, height, metrics, phone_cache):
        raw_ear = (calculate_ear(landmarks, LEFT_EYE, width, height)
                   + calculate_ear(landmarks, RIGHT_EYE, width, height)) / 2.0
        raw_mar = calculate_mar(landmarks, width, height)

        state = self._temporal.update(raw_ear, raw_mar)
        head = self._head.calculate(landmarks, width, height)

        distraction_score = score_distraction(
            head["direction"], head["duration"],
            phone_cache["detected"], phone_cache["using"])

        attention = resolve_attention(
            phone_cache["using"], head["direction"], head["distracted"])

        status = resolve_status(
            state["status"], distraction_score, phone_cache["using"],
            head["direction"], head["distracted"])

        metrics.update({
            "face": True,
            "status": status,
            "severity": SEVERITY.get(status, 0),
            "attention": attention,
            "eye_state": state["eye_state"],
            "ear": round(float(state["ear"]), 3),
            "mar": round(float(state["mar"]), 3),
            "closed_duration": round(float(state["closed_duration"]), 1),
            "blinks": int(state["blink_count"]),
            "perclos": round(float(state["perclos"]), 2),
            "yawn": bool(state["yawn"]),
            "yawn_count": int(state["yawn_count"]),
            "recent_yawns": int(state["recent_yawns"]),
            "recent_long_closures": int(state["recent_long_closures"]),
            "evidence_score": int(state["target_score"]),
            "drowsiness_score": int(state["score"]),
            "drowsiness_status": state["status"],
            "head_direction": head["direction"],
            "pitch": round(float(head["pitch"]), 1),
            "yaw": round(float(head["yaw"]), 1),
            "head_duration": round(float(head["duration"]), 1),
            "head_distracted": bool(head["distracted"]),
            "distraction_score": distraction_score,
        })

        for lm in landmarks:
            cv2.circle(frame, (int(lm.x * width), int(lm.y * height)), 1, MESH, -1)

        for index in list(LEFT_EYE.values()) + list(RIGHT_EYE.values()):
            cv2.circle(frame, _point(landmarks, index, width, height), 3, BLUE, -1)

        for index in (MOUTH_LEFT, MOUTH_RIGHT, MOUTH_UPPER, MOUTH_LOWER):
            cv2.circle(frame, _point(landmarks, index, width, height), 3, BURGUNDY, -1)

    def _draw_raw_overlay(self, frame, m, width, height):
        """Reproduces the on-frame text panels from main.py."""
        if not m["face"]:
            cv2.putText(frame, "NO DRIVER DETECTED", (20, 50),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, RED, 3)
            return

        font = cv2.FONT_HERSHEY_SIMPLEX
        eye_color = GREEN if m["eye_state"] == "OPEN" else RED
        yawn_color = RED if m["yawn"] else GREEN
        attention_color = {
            "ATTENTIVE": GREEN, "LOOKING AWAY": YELLOW, "PHONE USE": ORANGE,
        }.get(m["attention"], RED)
        final_color = {
            "ALERT": GREEN, "FATIGUED": YELLOW, "DROWSY": ORANGE, "DISTRACTED": MAGENTA,
        }.get(m["status"], RED)

        left = [
            (f"EYES: {m['eye_state']}", 35, 0.75, eye_color),
            (f"EAR: {m['ear']:.3f}", 67, 0.58, WHITE),
            (f"Closed: {m['closed_duration']:.1f}s", 97, 0.58, WHITE),
            (f"Blinks: {m['blinks']}", 127, 0.58, WHITE),
            (f"PERCLOS: {m['perclos']:.2f}", 157, 0.58, WHITE),
            (f"YAWN: {'YAWN' if m['yawn'] else 'NO YAWN'}", 202, 0.75, yawn_color),
            (f"MAR: {m['mar']:.3f}", 234, 0.58, WHITE),
            (f"Total yawns: {m['yawn_count']}", 264, 0.58, WHITE),
            (f"Recent yawns: {m['recent_yawns']}", 294, 0.58, WHITE),
            (f"Long closures: {m['recent_long_closures']}", 324, 0.58, WHITE),
            (f"Evidence: {m['evidence_score']}/100", 370, 0.60, WHITE),
            (f"Drowsiness: {m['drowsiness_score']}/100", 405, 0.68, final_color),
        ]
        for text, y, scale, color in left:
            cv2.putText(frame, text, (20, y), font, scale, color, 2)

        panel_x = max(650, width - 390)
        head_color = GREEN if m["head_direction"] == "FORWARD" else YELLOW
        if m["phone_using"]:
            phone_text, phone_color = "PHONE USE", RED
        elif m["phone_detected"]:
            phone_text, phone_color = "DETECTED", YELLOW
        else:
            phone_text, phone_color = "NO PHONE", GREEN

        right = [
            (f"HEAD: {m['head_direction']}", 35, 0.75, head_color, 2),
            (f"Pitch: {m['pitch']:.1f}", 67, 0.58, WHITE, 2),
            (f"Yaw: {m['yaw']:.1f}", 97, 0.58, WHITE, 2),
            (f"Away: {m['head_duration']:.1f}s", 127, 0.58, WHITE, 2),
            (f"PHONE: {phone_text}", 180, 0.70, phone_color, 2),
            (f"Phone conf: {m['phone_confidence']:.2f}", 212, 0.55, WHITE, 2),
            (f"Phone time: {m['phone_duration']:.1f}s", 242, 0.55, WHITE, 2),
            (f"Source: {m['phone_source']}", 272, 0.50, GRAY, 1),
            (f"Distraction: {m['distraction_score']}/100", 320, 0.65, attention_color, 2),
            (f"ATTENTION: {m['attention']}", 355, 0.68, attention_color, 2),
        ]
        for text, y, scale, color, thickness in right:
            cv2.putText(frame, text, (panel_x, y), font, scale, color, thickness)

        cv2.putText(frame, f"STATUS: {m['status']}", (20, height - 40),
                    font, 1.15, final_color, 3)

    def _emit_events(self, metrics, previous):
        if metrics["status"] != previous["status"]:
            if metrics["status"] == "CRITICAL":
                self._log("critical", "Critical state — driver unresponsive")
            elif metrics["status"] == "DROWSY":
                self._log("critical", "Drowsiness detected")
            elif metrics["status"] == "DISTRACTED":
                self._log("warning", f"Distraction detected — {metrics['attention'].title()}")
            elif metrics["status"] == "FATIGUED":
                self._log("warning", "Early fatigue signs detected")
            elif metrics["status"] == "NO DRIVER":
                self._log("warning", "Driver not in frame")
            elif metrics["status"] == "ALERT" and previous["status"] != "STANDBY":
                self._log("info", "Driver alert")
            previous["status"] = metrics["status"]

        if metrics["yawn_count"] > previous["yawns"]:
            previous["yawns"] = metrics["yawn_count"]
            self.totals["yawns"] = metrics["yawn_count"]
            self._log("warning", "Yawn recorded")

        if metrics["recent_long_closures"] > previous["closures"]:
            previous["closures"] = metrics["recent_long_closures"]
            self.totals["long_closures"] += 1
            self._log("critical", "Prolonged eye closure")

        if metrics["phone_using"] and not previous["phone"]:
            self.totals["phone_events"] += 1
            self._log("critical", "Phone use detected")
        previous["phone"] = metrics["phone_using"]

        self.totals["blinks"] = metrics["blinks"]

    def snapshot(self):
        return {
            "running": self.running,
            "error": self.error,
            "fps": self.fps,
            "raw_overlay": self.raw_overlay,
            "duration": round(time.time() - self.started_at, 1) if (self.running and self.started_at) else 0.0,
            "metrics": self.metrics,
            "totals": self.totals,
            "events": list(self.events),
        }

    def frames(self):
        boundary = b"--frame\r\nContent-Type: image/jpeg\r\n\r\n"
        while True:
            frame = self.frame_jpeg
            if frame is None:
                if not self.running:
                    return
                time.sleep(0.05)
                continue
            yield boundary + frame + b"\r\n"
            time.sleep(1 / 30)


monitor = Monitor()

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 2_000_000
CORS(app)


@app.get("/api/health")
def health():
    return jsonify({"status": "ok", "running": monitor.running})


@app.post("/api/start")
def start():
    browser = (request.get_json(silent=True) or {}).get("source") == "browser"
    ok, error = monitor.start(browser=browser)
    return (jsonify({"ok": True, **monitor.snapshot()}) if ok
            else (jsonify({"ok": False, "error": error}), 503))


@app.post("/api/frame")
def browser_frame():
    if not monitor.running or not isinstance(getattr(monitor, "_capture", None), BrowserCapture):
        return jsonify({"error": "Start a browser monitoring session first"}), 409
    data = request.get_data()
    if not data or len(data) > 2_000_000:
        return jsonify({"error": "Expected a JPEG smaller than 2 MB"}), 400
    frame = cv2.imdecode(np.frombuffer(data, dtype=np.uint8), cv2.IMREAD_COLOR)
    if frame is None or max(frame.shape[:2]) > 1920:
        return jsonify({"error": "Invalid frame or dimensions larger than 1920 pixels"}), 400
    monitor._capture.submit(frame)
    return jsonify({"ok": True})


@app.post("/api/stop")
def stop():
    monitor.stop()
    return jsonify({"ok": True, **monitor.snapshot()})


@app.post("/api/overlay")
def overlay():
    monitor.raw_overlay = bool((request.get_json(silent=True) or {}).get("enabled"))
    return jsonify({"ok": True, "raw_overlay": monitor.raw_overlay})


@app.get("/api/state")
def state():
    return jsonify(monitor.snapshot())


@app.get("/api/stream")
def stream():
    return Response(monitor.frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")


if __name__ == "__main__":
    port = int(os.environ.get("DRISHTI_PORT", "5001"))
    print(f"\n  Drishti backend  ->  http://localhost:{port}\n")
    app.run(host="127.0.0.1", port=port, threaded=True, debug=False)
