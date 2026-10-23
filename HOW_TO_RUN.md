# How to run Drishti

Drishti includes a Flask detection backend and the Next.js website. The launcher starts both. The browser asks for camera permission and sends frames to the backend; this works locally and is designed for GitHub Codespaces. No personal Mac folder paths are needed.

## GitHub Codespaces

1. On this repository, choose **Code → Codespaces → Create codespace on main**. Wait for the container setup to finish. Existing Codespaces should pull the latest changes and run **Codespaces: Rebuild Container** from the command palette.
2. In the terminal at the project root, run:

   ```bash
   python3.11 run.py --no-open
   ```

3. Open the **Ports** panel and select **Open in Browser** for port **3001**. Use the external browser tab, then visit `/dashboard` on that forwarded HTTPS URL. If the launcher reports another port because 3001 is occupied, forward that port instead.
4. Press **Start monitoring** and allow camera access. Use **Stop monitoring** to stop the camera. Keep the port private; the app has one monitoring session shared by connected tabs.
5. Press **Ctrl+C** in the terminal to stop both services.

Only the frontend port needs forwarding. It proxies `/api` to Flask inside the container. Do not use `localhost:3001` on your laptop to reach Codespaces; use the forwarded URL from the Ports panel.

## VS Code on your computer

Install **Python 3.11**, **Node.js 22** (with npm), and Git. Then run:

```bash
git clone https://github.com/dhvicore/driver_drowsiness-dhrishti.git
cd driver_drowsiness-dhrishti
python3.11 run.py
```

On Windows, use `py -3.11 run.py` for the last command.

On first launch, the launcher creates `.venv`, installs the Python requirements, and runs `npm ci` in `web/`. Installation can take several minutes and downloads large ML dependencies. Later launches reuse the environment. It starts both services and opens the dashboard, normally at <http://localhost:3001/dashboard>. If a port is busy, it selects another free port and prints the correct URL, so it will not open another project such as VoltRoute.

Open the cloned folder in VS Code with **File → Open Folder**. You can also open your existing complete Desktop project folder and run the launcher there.

## Separate terminals (optional)

After the first launcher setup, stop the launcher before starting these commands:

Terminal 1, from the project root:

```bash
.venv/bin/python server.py
```

Terminal 2, from the same folder:

```bash
npm --prefix web run dev -- --hostname 0.0.0.0 --port 3001
```

The frontend proxies the backend at `http://127.0.0.1:5001`. If you change the backend port, set `DRISHTI_PORT` for Flask and `DRISHTI_BACKEND_URL` for Next.js to matching values. On Windows, the Python executable is `.venv\Scripts\python.exe`.

## Troubleshooting

- **Missing `server.py`:** confirm you opened the current repository folder, not the older `-backup` folder, and run `git pull`.
- **Wrong project opens:** use the dashboard URL printed by `run.py`; other projects may occupy port 3000 or 3001.
- **Camera permission denied:** allow camera access for the browser and OS, then retry. Close other camera apps if needed.
- **Codespaces camera unavailable:** open the forwarded HTTPS URL in an external browser tab, not the editor's embedded preview.
- **Backend unreachable:** check the launcher logs. If running manually, start Flask before the frontend.
- **Linux missing `libGL.so.1`:** install `libgl1` and `libglib2.0-0`. The supplied Codespaces container installs these.
- **Slow monitoring:** CPU inference and upload speed affect frame rate. This project does not promise a fixed FPS or detection accuracy.

The backend receives camera images for processing and does not save uploaded frames to disk. Each Codespace is intended for a single monitoring session. Test while stationary; this is a prototype, not a validated driving safety system.

## Original desktop window

After setup, `.venv/bin/python main.py` runs the separate OpenCV camera window on a computer with a directly attached webcam. Press **q** in that window to quit. This desktop mode cannot open your laptop camera from a remote Codespace; use the browser dashboard there.
