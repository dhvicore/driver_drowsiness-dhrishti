"""Browser camera adapter for the existing Drishti Python monitoring engines."""
import copy
from datetime import datetime
from functools import lru_cache
import os
from pathlib import Path
import sys
import threading
import time

os.environ.setdefault('GRADIO_ANALYTICS_ENABLED', 'False')
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
import cv2
import gradio as gr
import mediapipe as mp
import numpy as np
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from temporal_engine import TemporalEngine
from head_pose import HeadPoseDetector
from features import LEFT_EYE, RIGHT_EYE, calculate_ear, calculate_mar

MODEL_LOCK = threading.RLock()

@lru_cache(maxsize=1)
def face_model():
    return vision.FaceLandmarker.create_from_options(vision.FaceLandmarkerOptions(
        base_options=python.BaseOptions(model_asset_path=str(ROOT/'face_landmarker.task')),
        running_mode=vision.RunningMode.IMAGE, num_faces=1,
        min_face_detection_confidence=0.5, min_face_presence_confidence=0.5))

@lru_cache(maxsize=1)
def phone_template():
    from phone_detector import PhoneDetector
    # The desktop detector resolves its weight file from the project root.
    return PhoneDetector()

class Session:
    """Only histories belong to a browser session; model inference is serialized."""
    def __init__(self):
        self.engine = TemporalEngine()
        self.head = HeadPoseDetector()
        self.phone = None
        self.phone_result = None
        self.last_phone = 0.0
        self.last_frame = 0.0
        self.last_label = None
        self.last_yawns = 0
        self.events = []

    def add_event(self, message):
        self.events.insert(0, [datetime.now().strftime('%H:%M:%S'), message])
        self.events = self.events[:40]

    def reset_tracking(self):
        self.engine = TemporalEngine()
        self.head = HeadPoseDetector()
        self.phone = None
        self.phone_result = None
        self.last_label = None
        self.last_yawns = 0

    def __deepcopy__(self, memo):
        # Gradio copies only a fresh initial session. Models are created later.
        if self.phone is not None:
            raise TypeError('Do not copy an active monitoring session')
        other = Session()
        memo[id(self)] = other
        return other


def monitor(frame, enable_phone, state):
    state = state or Session()
    if frame is None:
        return None, '### Ready\nAllow camera access and start the webcam stream.', {}, state.events, state
    frame = np.asarray(frame, dtype=np.uint8)
    if frame.ndim != 3 or frame.shape[2] < 3:
        raise gr.Error('The camera must provide a colour image.')
    frame = frame[:, :, :3]
    height, width = frame.shape[:2]
    if width > 720:
        frame = cv2.resize(frame, (720, round(height*720/width)))
        height, width = frame.shape[:2]
    now = time.monotonic()
    if state.last_frame and now-state.last_frame > 2:
        state.reset_tracking()
        state.add_event('Monitoring resumed; timing history reset after a gap')
    state.last_frame = now
    frame = np.ascontiguousarray(frame)
    with MODEL_LOCK:
        detection = face_model().detect(mp.Image(image_format=mp.ImageFormat.SRGB, data=frame))
    if not detection.face_landmarks:
        if state.last_label != 'NO FACE':
            state.add_event('No face visible; monitoring history reset')
        state.reset_tracking()
        state.last_label = 'NO FACE'
        return frame, '### No face detected\nFace the camera in good lighting.', {}, state.events, state
    landmarks = detection.face_landmarks[0]
    ear = (calculate_ear(landmarks, LEFT_EYE, width, height)
           + calculate_ear(landmarks, RIGHT_EYE, width, height))/2
    mar = calculate_mar(landmarks, width, height)
    result = state.engine.update(ear, mar)
    pose = state.head.calculate(landmarks, width, height)
    label = result['status']
    if label != state.last_label:
        state.add_event('Driver state: '+label)
        state.last_label = label
    if result['yawn_count'] > state.last_yawns:
        state.add_event('Yawn recorded')
    state.last_yawns = result['yawn_count']
    annotated = frame.copy()
    for idx in [33,133,160,144,158,153,362,263,385,380,387,373,61,291,13,14]:
        point = landmarks[idx]
        cv2.circle(annotated, (int(point.x*width), int(point.y*height)), 2, (99,220,184), -1)
    phone = None
    if enable_phone:
        if state.phone is None:
            with MODEL_LOCK:
                template = phone_template()
                state.phone = object.__new__(type(template))
                for key, value in template.__dict__.items():
                    setattr(state.phone, key, value if key == 'model' else copy.deepcopy(value))
        if now-state.last_phone >= 1:
            with MODEL_LOCK:
                state.phone_result = state.phone.detect(cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
            state.last_phone = now
        phone = state.phone_result
        if phone and phone['box'] is not None:
            x1,y1,x2,y2 = [int(v) for v in phone['box']]
            cv2.rectangle(annotated,(x1,y1),(x2,y2),(255,180,70),2)
    else:
        state.phone = None
        state.phone_result = None
    score = result['score']
    status = f"### {label.title()}\nEvidence score **{score}/100** · Eyes **{result['eye_state'].lower()}**"
    if pose['distracted']:
        status += '\n\n**Distraction: sustained head movement detected.**'
    if phone and phone['using']:
        status += '\n\n**Phone use detected.**'
    metrics = {
        'Evidence score (not accuracy)': score,
        'EAR': round(result['ear'],3), 'MAR': round(result['mar'],3),
        'Eye closure (seconds)': round(result['closed_duration'],2),
        'Closed-eye sample ratio': round(result['perclos'],3),
        'Blinks': result['blink_count'], 'Yawns': result['yawn_count'],
        'Head direction': pose['direction'],
        'Phone': ('detected' if phone and phone['detected'] else 'not detected') if enable_phone else 'off',
    }
    return annotated, status, metrics, state.events, state


def reset():
    return None, '### Ready\nStart the webcam stream to monitor.', {}, [], Session()


def build_app():
    with gr.Blocks(title='Drishti | Driver monitoring') as demo:
        gr.Markdown('# Drishti\n### Driver monitoring, from your browser\nAllow camera access, face the camera, then start streaming. Stop the webcam when you finish.')
        gr.Markdown('Your camera frames are sent to this demo server for processing. This app does not save recordings or session logs to disk. A research prototype; use while stationary.')
        state = gr.State(Session, time_to_live=600)
        with gr.Row():
            with gr.Column(scale=3):
                camera = gr.Image(sources=['webcam'], type='numpy', streaming=True, label='Your camera')
                output = gr.Image(type='numpy', label='Landmarks and detections', interactive=False)
            with gr.Column(scale=2):
                status = gr.Markdown('### Ready\nAllow camera access and start streaming.')
                phone = gr.Checkbox(False, label='Enable phone detection (slower)')
                metrics = gr.JSON(label='Live measurements')
                clear = gr.Button('Reset monitoring session')
                activity = gr.Dataframe(headers=['Server time','Event'], datatype=['str','str'], interactive=False, label='Session activity')
        gr.Markdown('The score combines measured cues; it is not an accuracy percentage. Browser frame rate and network delay affect the timing of warnings. Reset starts a new history.')
        camera.stream(monitor, [camera,phone,state], [output,status,metrics,activity,state],
                      stream_every=0.12, concurrency_limit=2, time_limit=600)
        clear.click(reset, [], [output,status,metrics,activity,state])
    return demo

if __name__ == '__main__':
    os.chdir(ROOT)
    build_app().queue(max_size=16).launch(
        server_name=os.environ.get('HOST','0.0.0.0'),
        server_port=int(os.environ.get('PORT','7860')),
        share=False, show_error=False,
        blocked_paths=[str(ROOT/'research_paper'),str(ROOT/'.git'),str(ROOT/'.venv')],
        max_file_size='5mb')
