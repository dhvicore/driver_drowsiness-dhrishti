# Deploy the browser prototype

The browser adapter reuses `temporal_engine.py`, `head_pose.py` and `phone_detector.py`. It does not start the desktop webcam or modify `main.py`. A visitor supplies their own webcam through the browser; frames are processed by the server. Session counters and histories are separate for each visitor. Face-loss and gaps longer than two seconds reset temporal tracking to avoid counting a disconnected camera as a continuous closure.

## Try locally

From the project root, with Python 3.11:

```bash
python3.11 -m venv .venv
source .venv/bin/activate
python -m pip install -r web/requirements.txt
python web/app.py
```

Open `http://localhost:7860`. Allow webcam permission and start streaming. Phone detection is optional because tiled YOLO inference consumes substantially more CPU and memory. Network and browser sampling rates can change the temporal engine's response compared with the desktop application.

## Public deployment on Render

1. Sign in at https://dashboard.render.com/ using GitHub.
2. Create a **Web Service** and select `dhvicore/driver_drowsiness-dhrishti`.
3. Select the `main` branch, **Docker** runtime, repository root as the root directory and `./Dockerfile` as the Dockerfile path.
4. Name the service `drishti-demo` (or another available name).
5. Select an instance after reviewing its current price. For the complete app with YOLO, start with at least **2 GB RAM** and verify actual usage. A free or small instance may run out of memory when phone detection loads. Free instances also sleep while idle.
6. Set environment variable `PORT` to `7860` if the platform does not supply one. The app also accepts the platform-provided `PORT`.
7. Deploy, wait for the build and open the service's HTTPS `.onrender.com` URL. HTTPS is required for camera access outside localhost.
8. Test from a second device: grant camera permission, confirm face landmarks, close/reopen the eyes, open/close the mouth, enable phone detection if sufficient memory is available, and reset the session. Check service logs for errors and memory pressure.

The deployment is not complete until the remote service builds successfully and the HTTPS webcam flow has been tested. No account credentials belong in this repository.

## Scope

The browser app uses the same landmark ratios and temporal engine as the desktop app. It adds a Gradio browser interface, per-session state and frame-gap handling. It does not run the separate saved Keras classifiers, which are not part of `main.py`'s active pipeline. The interface score is evidence, not an accuracy estimate. Prototype use should be stationary; this is not a validated safety system.
