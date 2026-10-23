# Drishti — Driver Drowsiness Monitoring

A driver-monitoring prototype with a Next.js dashboard and Flask backend. It uses MediaPipe face landmarks, eye and mouth ratios, temporal warning rules, head pose, and YOLO phone detection.

## Run in GitHub Codespaces

Choose **Code → Codespaces → Create codespace on main**, wait for container setup, then run:

```bash
python3.11 run.py --no-open
```

In the **Ports** panel, open port **3001** in an external browser and visit `/dashboard` on its forwarded HTTPS URL. Press **Start monitoring** and grant camera permission. The browser sends your camera frames to Flask through the frontend, so no laptop filesystem path or remote webcam is needed. If 3001 is occupied, use the port printed by the launcher.

Existing Codespaces need the latest code and a container rebuild to apply `.devcontainer/devcontainer.json`.

## Run in VS Code locally

Install Python **3.11**, Node.js **22** (including npm), and Git:

```bash
git clone https://github.com/dhvicore/driver_drowsiness-dhrishti.git
cd driver_drowsiness-dhrishti
python3.11 run.py
```

On Windows, use `py -3.11 run.py`. First launch installs dependencies; later launches reuse them. The launcher starts both services, selects free ports, and opens the correct dashboard, normally <http://localhost:3001/dashboard>. Press **Ctrl+C** to stop both.

See [HOW_TO_RUN.md](HOW_TO_RUN.md) for full instructions, separate-terminal commands, and troubleshooting, and [PROJECT_NOTES.md](PROJECT_NOTES.md) for the existing detector notes.

## Run backend and frontend in separate VS Code terminals

For a new checkout, install dependencies once from the repository root (macOS/Linux):

```bash
python3.11 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
npm --prefix web ci
```

**Terminal 1 — backend:**

```bash
source .venv/bin/activate
python server.py
```

Leave it running on port **5001**. Open a second VS Code terminal in the **same project root**.

**Terminal 2 — frontend:**

```bash
npm --prefix web run dev -- --port 3001
```

Open <http://localhost:3001/dashboard>, click **Start monitoring**, and allow camera access. Press **Ctrl+C** in each terminal to stop. The frontend command needs no Python environment activation. If a port is occupied by another project, use `python3.11 run.py` to select free ports automatically.

On Windows, create the environment with `py -3.11 -m venv .venv`, install requirements with `.venv\Scripts\python.exe -m pip install -r requirements.txt`, and activate with `.\.venv\Scripts\Activate.ps1` in PowerShell. The npm commands are the same.

## Project files

| Path | Purpose |
|---|---|
| `run.py` | Dependency setup and combined backend/frontend launcher |
| `server.py` | Flask APIs, browser camera frame input, detection and MJPEG output |
| `web/app`, `web/components`, `web/lib` | Next.js landing page and monitoring dashboard |
| `temporal_engine.py` | Eye closure, yawning, evidence score and warning rules |
| `head_pose.py`, `phone_detector.py` | Head pose and phone detection |
| `main.py` | Separate desktop OpenCV application |
| `.devcontainer/devcontainer.json` | Codespaces Python/Node environment and port forwarding |

The active pipeline uses `face_landmarker.task` and `yolo11s.pt`. Other saved Keras models and the notebook are separate experiments; they are not loaded by the dashboard pipeline.

The Flask backend defaults to port 5001 and the launcher prefers frontend port 3001. The frontend proxies `/api` to Flask, so only one port needs forwarding. Each running backend has one monitoring session shared across its browser tabs; keep your Codespaces port private. Uploaded camera frames are processed in memory rather than saved to disk.

Research papers, generated documents, virtual environments and installed dependencies stay outside version control. CPU resources, camera quality and network sampling affect behavior. Use this prototype while stationary; it is not a validated driving safety system.
