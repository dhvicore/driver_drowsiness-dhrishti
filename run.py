"""Start Drishti's backend and frontend from any checkout. Python 3.11."""
import argparse
import hashlib
import os
from pathlib import Path
import shutil
import signal
import socket
import subprocess
import sys
import time
import urllib.request
import venv
import webbrowser

ROOT = Path(__file__).resolve().parent


def free_port(preferred):
    for port in range(preferred, preferred + 100):
        with socket.socket() as sock:
            try:
                sock.bind(('127.0.0.1', port))
                return port
            except OSError:
                pass
    raise RuntimeError(f'No free port near {preferred}')


def ready(url, process):
    deadline = time.monotonic() + 120
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f'Service exited before {url} was ready; see logs above.')
        try:
            with urllib.request.urlopen(url, timeout=2) as response:
                if response.status == 200:
                    return
        except (OSError, TimeoutError):
            pass
        time.sleep(0.25)
    raise RuntimeError(f'Timed out waiting for {url}; see logs above.')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--no-open', action='store_true')
    parser.add_argument('--backend-port', type=int, default=5001)
    parser.add_argument('--frontend-port', type=int, default=3001)
    args = parser.parse_args()
    if sys.version_info[:2] != (3, 11):
        raise RuntimeError('Run this launcher with Python 3.11: python3.11 run.py')
    npm = shutil.which('npm')
    node = shutil.which('node')
    if not npm or not node:
        raise RuntimeError('Install Node.js 22 (including npm), then run again.')
    major = int(subprocess.check_output([node, '--version'], text=True).strip().lstrip('v').split('.')[0])
    if major < 22:
        raise RuntimeError('Use Node.js 22 or newer.')
    environment = ROOT / '.venv'
    python = environment / ('Scripts/python.exe' if os.name == 'nt' else 'bin/python')
    if not python.exists():
        venv.create(environment, with_pip=True)
    signature = hashlib.sha256((ROOT / 'requirements.txt').read_bytes()).hexdigest()
    marker = environment / '.drishti-requirements'
    if not marker.exists() or marker.read_text() != signature:
        subprocess.run([str(python), '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')], check=True)
        marker.write_text(signature)
    if not (ROOT / 'web/node_modules/next').exists():
        subprocess.run([npm, 'ci'], cwd=ROOT / 'web', check=True)
    backend = free_port(args.backend_port)
    frontend = free_port(args.frontend_port)
    if frontend == backend:
        frontend = free_port(frontend + 1)
    env = dict(os.environ, DRISHTI_PORT=str(backend), DRISHTI_BACKEND_URL=f'http://127.0.0.1:{backend}')
    # The frontend proxies /api to Flask, including on Codespaces HTTPS URLs.
    env.pop('NEXT_PUBLIC_DRISHTI_API', None)
    children = []
    def terminate(*_):
        raise KeyboardInterrupt

    signal.signal(signal.SIGTERM, terminate)
    try:
        children.append(subprocess.Popen([str(python), '-u', 'server.py'], cwd=ROOT, env=env))
        ready(f'http://127.0.0.1:{backend}/api/health', children[0])
        children.append(subprocess.Popen([node, str(ROOT / 'web/node_modules/next/dist/bin/next'),
                                         'dev', '--hostname', '0.0.0.0', '--port', str(frontend)],
                                        cwd=ROOT / 'web', env=env))
        url = f'http://localhost:{frontend}/dashboard'
        ready(f'http://127.0.0.1:{frontend}/api/health', children[1])
        print(f'\nDrishti dashboard: {url}\nPress Ctrl+C to stop both services.', flush=True)
        if os.environ.get('CODESPACES'):
            print(f'Codespaces: forward port {frontend} and open /dashboard in the browser.', flush=True)
        elif not args.no_open:
            webbrowser.open(url)
        while all(p.poll() is None for p in children):
            time.sleep(0.5)
        raise RuntimeError('A service stopped; see logs above.')
    except KeyboardInterrupt:
        print('\nStopping Drishti...', flush=True)
    finally:
        for child in reversed(children):
            if child.poll() is None:
                child.terminate()
                try:
                    child.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    child.kill()
                    child.wait()


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, subprocess.CalledProcessError) as error:
        print(f'Drishti: {error}', file=sys.stderr)
        sys.exit(1)
