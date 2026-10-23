# How to Run Drishti

Use Python 3.11 and a working webcam. Run all commands from the project root so model paths resolve.

## 1. Get the project

```bash
git clone https://github.com/dhvicore/driver_drowsiness-dhrishti.git
cd driver_drowsiness-dhrishti
```

If you already have the project, open a terminal in its folder instead.

## 2. Create a virtual environment

### macOS / Linux

```bash
python3.11 -m venv .venv
source .venv/bin/activate
```

### Windows PowerShell

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
```

## 3. Install dependencies

For the browser prototype and a pinned dependency set compatible with the project's MediaPipe code:

```bash
python -m pip install --upgrade pip
python -m pip install -r web/requirements.txt
```

These dependencies also include the packages used by the desktop webcam application. The root `requirements.txt` provides an alternative unpinned dependency list.

## 4. Run the desktop webcam app

```bash
python main.py
```

Allow camera access when prompted. The application opens a window named **Driver Monitoring System** and uses the default camera (index `0`). Keep your face visible to view eye, mouth, head-pose and phone-detection information.

Press **q** while the camera window is focused to exit.

The desktop app uses `face_landmarker.task` and `yolo11s.pt`, both included in the repository. Keep these files in the project root. The separate Keras eye/yawn classifiers are not used by the active `main.py` pipeline.

## 5. Run the browser prototype

As an alternative to the desktop app:

```bash
python web/app.py
```

Open <http://localhost:7860>, allow webcam access and start streaming. Phone detection is optional and uses additional CPU and memory.

For hosting instructions, see [web/DEPLOY.md](web/DEPLOY.md).

## Troubleshooting

- **Camera does not open:** close other apps using the webcam and check camera permissions for your terminal or Python application. The desktop app selects camera index `0` in `main.py`.
- **Missing module:** activate `.venv` and install the dependencies using `python -m pip install -r web/requirements.txt`.
- **MediaPipe compatibility errors:** use Python 3.11 and the pinned `web/requirements.txt` dependencies in a fresh virtual environment.
- **Model file not found:** run from the project root and confirm the model files are present.
- **Slow processing:** disable optional phone detection in the browser prototype.

TensorFlow is needed only for the separate Keras model utilities:

```bash
python -m pip install tensorflow
```

Test the prototype while stationary. It is not a validated driving safety system.
