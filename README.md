# Drishti — Driver Drowsiness Monitoring

Python driver-monitoring prototype using eye and mouth measurements, temporal warning rules, head pose and phone detection.

## Code guide

- [`main.py`](main.py): webcam application; connects MediaPipe landmarks, temporal monitoring, head pose and phone detection.
- [`temporal_engine.py`](temporal_engine.py): median filtering, hysteresis, closure/yawn timers, event histories, evidence score and warning-state rules.
- [`head_pose.py`](head_pose.py): estimates head pose and sustained distraction.
- [`phone_detector.py`](phone_detector.py): YOLO-based phone detection with temporal confirmation.
- [`model_manager.py`](model_manager.py): loads the saved eye/yawn Keras classifiers and applies MobileNetV2 preprocessing.
- [`face_analyzer.py`](face_analyzer.py), [`face_regions.py`](face_regions.py), [`landmark_detector.py`](landmark_detector.py): supporting face-analysis utilities.
- [`yawn.ipynb`](yawn.ipynb): yawning-model notebook.
- `test_*.py`, `model_test.py`, `eye_compare_live.py`: inspection and demonstration scripts; some require a camera or model dependencies.

## Model files

The repository includes the saved Keras models (`eye_model.keras`, `best_yawn_model.keras`, `eye_state_mobilenetv2.keras`, `yawn_state_mobilenetv2.keras`), MediaPipe `face_landmarker.task`, and YOLO weight files. These files serve different modules; `main.py` uses landmark-based temporal rules and does not load the Keras eye/yawn models through `ModelManager`.

## Run the webcam prototype

Use Python 3.11 in a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Run from the repository root so the model paths resolve, and allow camera access when prompted. For the separate Keras model utilities, also install TensorFlow in a compatible environment:

```bash
python -m pip install tensorflow
```

## Frontend source

The dashboard frontend source is not present in this checkout. The current repository provides the Python webcam prototype and saved models; dashboard screenshots do not substitute for frontend source code.

Research papers, presentations, study notes, generated documents and local environments are excluded from this code repository.
