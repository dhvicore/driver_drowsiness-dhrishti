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

## Run the website and live dashboard

The full website uses two processes: a Flask backend on port **5001** and a Next.js frontend on port **3000**. Run them in separate VS Code terminals.

**Current source location:** the complete website is in the local archive folder below. This GitHub checkout does not yet include `server.py` or the Next.js source and `web/package.json`. A fresh clone can run the desktop prototype, but the website commands require the complete archive copy. Changing this README does not add those missing source files.

### Terminal 1 — backend

```bash
cd "/Users/dhvani/iCloud Drive (Archive)/Desktop/driver_drowsiness-dhrishti-main"
source venv/bin/activate
python server.py
```

Wait until the backend reports `http://127.0.0.1:5001`, then leave this terminal running.

### Terminal 2 — website

```bash
cd "/Users/dhvani/iCloud Drive (Archive)/Desktop/driver_drowsiness-dhrishti-main"
npm --prefix web run dev
```

If frontend packages have not been installed, run `npm --prefix web install` in that folder first.

### Open the website

| Page | Address |
|---|---|
| Landing page | <http://localhost:3000> |
| Live dashboard | <http://localhost:3000/dashboard> |

Press **Start monitoring** on the dashboard to open the camera, and **Stop monitoring** to close it. Stop both processes with **Ctrl+C** in their terminals. Port 5001 serves the backend; open port 3000 to use the website.

If `python server.py` reports “No such file or directory,” check your folder: the fresh `drishti-check` clone currently lacks this file. Use the complete archive folder for the website.

See [HOW_TO_RUN.md](HOW_TO_RUN.md) for the local website instructions and [PROJECT_NOTES.md](PROJECT_NOTES.md) for project details.

## Run the desktop webcam prototype

Use Python 3.11 in a virtual environment:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python main.py
```

Run from the repository root so the model paths resolve, and allow camera access when prompted. Press **q** while the camera window is focused to quit; do not type `Q` into the terminal. Stop the website backend before running this app so only one process uses the camera. For the separate Keras model utilities, also install TensorFlow in a compatible environment:

```bash
python -m pip install tensorflow
```

Research papers, presentations, study notes, generated documents and local environments are excluded from this code repository.
