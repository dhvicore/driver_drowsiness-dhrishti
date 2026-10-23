# Drishti frontend

This Next.js app is the Drishti landing page and driver-monitoring dashboard.

Run `python3.11 run.py` from the repository root to set up and start both the Flask backend and this frontend. See [the project run guide](../HOW_TO_RUN.md), including Codespaces instructions.

For frontend-only development after installation, use `npm run dev -- --port 3001` here, with Flask running separately. `/api/*` requests are proxied to `DRISHTI_BACKEND_URL` (default `http://127.0.0.1:5001`). Camera frames come from the visitor's browser, with their permission.
