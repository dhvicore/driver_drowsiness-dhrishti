# How to run Drishti

The project has two parts that run at the same time, each in its own terminal:

- **Backend** (Python) — reads the webcam and does the detection. Port **5001**.
- **Website** (Next.js) — shows the landing page and dashboard. Port **3000**.

> Always use the **`iCloud Drive (Archive)`** copy of the project.
> The folder in `~/Desktop` is an older partial copy and has no `server.py`.

---

## Terminal 1 — backend

```bash
cd "/Users/dhvani/iCloud Drive (Archive)/Desktop/driver_drowsiness-dhrishti-main" && source venv/bin/activate && python server.py
```

Wait until it prints `Running on http://127.0.0.1:5001`, then leave it running.

## Terminal 2 — website

```bash
cd "/Users/dhvani/iCloud Drive (Archive)/Desktop/driver_drowsiness-dhrishti-main" && npm --prefix web run dev
```

## Open it

| Page | Address |
|---|---|
| Landing page | http://localhost:3000 |
| Live dashboard | http://localhost:3000/dashboard |

On the dashboard, press **Start monitoring** to open the camera. Press **Stop monitoring** to close it.

To shut everything down, press **Ctrl-C** in each terminal.

---

## Running the original OpenCV window instead

`main.py` is the original program and shows its output in a desktop window rather than the browser:

```bash
cd "/Users/dhvani/iCloud Drive (Archive)/Desktop/driver_drowsiness-dhrishti-main" && source venv/bin/activate && python main.py
```

Press **Q** to quit. Only one program can use the camera at a time, so stop `server.py` first.

---

## Running from VS Code

1. Open the project: **File → Open Folder**, then pick the `iCloud Drive (Archive)` project folder.
2. **Terminal → New Terminal**, and run the two commands above in separate tabs (use the **+** button for the second one).

To enable the `code` command in your shell: press Cmd+Shift+P in VS Code and choose **Shell Command: Install 'code' command in PATH**.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `Address already in use` / `Port 5001 is in use` | The backend is already running. Use it, or free the port: `lsof -ti:5001 \| xargs kill` |
| `zsh: no such file or directory: /venv/bin/python` | The leading `/` is wrong. Use `./venv/bin/python`, or activate the venv and just run `python server.py` |
| `command not found: code` | Install the VS Code shell command (see above), or use **File → Open Folder** |
| **Not Found** page in the browser | You opened port 5001, which is the data feed only. The website is on **port 3000** |
| Dashboard says **Backend unreachable** | The backend isn't running. Do Terminal 1 above |
| Camera doesn't open | Allow camera access for your terminal or VS Code in **System Settings → Privacy & Security → Camera**, then restart the backend |
| Status stays **No Driver** | Face the webcam directly; the face must be visible and reasonably lit |

---

## If the environment ever breaks

Rebuild the Python environment (one-time, downloads about 1–2 GB):

```bash
cd "/Users/dhvani/iCloud Drive (Archive)/Desktop/driver_drowsiness-dhrishti-main" && python3.11 -m venv --clear venv && ./venv/bin/pip install flask flask-cors opencv-contrib-python==5.0.0.93 mediapipe==0.10.14 ultralytics numpy
```

Reinstall the website packages:

```bash
npm --prefix "/Users/dhvani/iCloud Drive (Archive)/Desktop/driver_drowsiness-dhrishti-main/web" install
```
