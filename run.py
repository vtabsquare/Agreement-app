#!/usr/bin/env python3
"""Aurelia Contract Studio - single local launcher.

Usage:
    python run.py

The launcher:
- checks the host Python version;
- creates/reuses backend/.venv;
- installs backend dependencies only when requirements change;
- uses system Node/npm when suitable, otherwise downloads a portable Node runtime
  into .runtime (no system-wide installation);
- installs frontend dependencies only when package metadata changes;
- starts FastAPI and Vite;
- opens the local application in the default browser;
- preserves any existing .env and never creates/overwrites it;
- shuts down child processes cleanly on Ctrl+C.
"""

from __future__ import annotations

import hashlib
import json
import os
import platform
import shutil
import signal
import socket
import subprocess
import sys
import tarfile
import time
import urllib.error
import urllib.request
import webbrowser
import zipfile
from pathlib import Path

APP_NAME = "Aurelia Contract Studio"
HOST = "127.0.0.1"
BACKEND_PORT = 8000
FRONTEND_PORT = 5173
FRONTEND_URL = f"http://{HOST}:{FRONTEND_PORT}"
BACKEND_URL = f"http://{HOST}:{BACKEND_PORT}"
MIN_PYTHON = (3, 10)
MIN_NODE_MAJOR = 20
# Portable fallback only; system Node/npm is preferred when available.
PORTABLE_NODE_VERSION = "22.14.0"

ROOT = Path(__file__).resolve().parent
BACKEND_DIR = ROOT / "backend"
FRONTEND_DIR = ROOT / "frontend"
VENV_DIR = BACKEND_DIR / ".venv"
RUNTIME_DIR = ROOT / ".runtime"
STATE_DIR = ROOT / ".launcher"
STATE_FILE = STATE_DIR / "state.json"


def banner() -> None:
    print("=" * 70)
    print(f"  {APP_NAME}")
    print("  One-command local environment check & launcher")
    print("=" * 70)


def fail(message: str, exit_code: int = 1) -> None:
    print(f"\n[ERROR] {message}")
    raise SystemExit(exit_code)


def info(message: str) -> None:
    print(f"[INFO]  {message}")


def ok(message: str) -> None:
    print(f"[OK]    {message}")


def warn(message: str) -> None:
    print(f"[WARN]  {message}")


def check_project_layout() -> None:
    required = [
        BACKEND_DIR / "requirements.txt",
        BACKEND_DIR / "app" / "main.py",
        FRONTEND_DIR / "package.json",
    ]
    missing = [str(p.relative_to(ROOT)) for p in required if not p.exists()]
    if missing:
        fail("Project files are missing: " + ", ".join(missing))


def check_python() -> None:
    version = sys.version_info
    if version < MIN_PYTHON:
        fail(
            f"Python {MIN_PYTHON[0]}.{MIN_PYTHON[1]}+ is required. "
            f"Current version: {version.major}.{version.minor}.{version.micro}. "
            "Install a current Python release from python.org, enable 'Add Python to PATH', "
            "then run `python run.py` again."
        )
    ok(f"Python {version.major}.{version.minor}.{version.micro}")


def load_state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}


def save_state(state: dict) -> None:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def fingerprint(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in paths:
        if path.exists():
            digest.update(path.name.encode("utf-8"))
            digest.update(path.read_bytes())
    return digest.hexdigest()


def venv_python() -> Path:
    if os.name == "nt":
        return VENV_DIR / "Scripts" / "python.exe"
    return VENV_DIR / "bin" / "python"


def run_checked(command: list[str], *, cwd: Path | None = None, env: dict | None = None) -> None:
    printable = " ".join(str(x) for x in command)
    info(f"Running: {printable}")
    result = subprocess.run(command, cwd=cwd, env=env)
    if result.returncode != 0:
        fail(f"Command failed with exit code {result.returncode}: {printable}")


def venv_python_version() -> tuple[int, int] | None:
    """Return the venv interpreter major/minor, or None when unusable."""
    py = venv_python()
    if not py.exists():
        return None
    try:
        output = subprocess.check_output(
            [str(py), "-c", "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"],
            text=True,
            stderr=subprocess.DEVNULL,
        ).strip()
        major, minor = output.split(".", 1)
        return int(major), int(minor)
    except Exception:
        return None


def recreate_backend_venv(state: dict, reason: str) -> None:
    warn(reason)
    if VENV_DIR.exists():
        info("Removing stale backend/.venv ...")
        shutil.rmtree(VENV_DIR, ignore_errors=True)
    state.pop("backend_requirements", None)
    save_state(state)
    info("Creating a clean backend/.venv ...")
    run_checked([sys.executable, "-m", "venv", str(VENV_DIR)])
    ok("Clean backend virtual environment created")


def install_backend_packages(req_file: Path) -> bool:
    """Install backend packages; return False instead of exiting on pip failure."""
    commands = [
        [str(venv_python()), "-m", "pip", "install", "--upgrade", "pip"],
        [
            str(venv_python()), "-m", "pip", "install",
            "--prefer-binary", "-r", str(req_file),
        ],
    ]
    for command in commands:
        printable = " ".join(str(x) for x in command)
        info(f"Running: {printable}")
        result = subprocess.run(command)
        if result.returncode != 0:
            warn(f"Command failed with exit code {result.returncode}: {printable}")
            return False
    return True


def ensure_backend(state: dict) -> None:
    host_version = (sys.version_info.major, sys.version_info.minor)
    existing_version = venv_python_version()

    if VENV_DIR.exists() and existing_version != host_version:
        if existing_version is None:
            reason = "Existing backend/.venv is incomplete or unusable; rebuilding it automatically."
        else:
            reason = (
                f"Existing backend/.venv uses Python {existing_version[0]}.{existing_version[1]}, "
                f"but launcher uses Python {host_version[0]}.{host_version[1]}; rebuilding it automatically."
            )
        recreate_backend_venv(state, reason)
    elif not venv_python().exists():
        info("Backend virtual environment not found. Creating backend/.venv ...")
        run_checked([sys.executable, "-m", "venv", str(VENV_DIR)])
        state.pop("backend_requirements", None)
        ok("Backend virtual environment created")
    else:
        ok(f"Backend virtual environment already exists (Python {host_version[0]}.{host_version[1]})")

    req_file = BACKEND_DIR / "requirements.txt"
    req_hash = fingerprint([req_file])
    needs_install = state.get("backend_requirements") != req_hash

    if not needs_install:
        probe = subprocess.run(
            [str(venv_python()), "-c", "import fastapi, uvicorn, pydantic, reportlab"],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        needs_install = probe.returncode != 0

    if needs_install:
        info("Installing/checking backend Python packages ...")
        if not install_backend_packages(req_file):
            recreate_backend_venv(
                state,
                "Backend dependency installation failed. Rebuilding the virtual environment once and retrying.",
            )
            if not install_backend_packages(req_file):
                fail(
                    "Backend dependency installation still failed after automatic repair. "
                    "Please copy the pip error shown above and share it for diagnosis."
                )
        state["backend_requirements"] = req_hash
        state["backend_python"] = f"{host_version[0]}.{host_version[1]}"
        save_state(state)
        ok("Backend dependencies are ready")
    else:
        ok("Backend dependencies already match requirements.txt")

def command_path(name: str, extra_path: Path | None = None) -> str | None:
    path = os.environ.get("PATH", "")
    if extra_path:
        path = str(extra_path) + os.pathsep + path
    return shutil.which(name, path=path)


def node_major(node_exe: str) -> int | None:
    try:
        output = subprocess.check_output([node_exe, "--version"], text=True, stderr=subprocess.STDOUT).strip()
        return int(output.lstrip("v").split(".")[0])
    except Exception:
        return None


def portable_node_target() -> tuple[str, str, str]:
    system = platform.system().lower()
    machine = platform.machine().lower()

    if machine in {"amd64", "x86_64"}:
        arch = "x64"
    elif machine in {"arm64", "aarch64"}:
        arch = "arm64"
    else:
        fail(f"Unsupported CPU architecture for automatic Node provisioning: {machine}")

    version_tag = f"v{PORTABLE_NODE_VERSION}"
    if system == "windows":
        filename = f"node-{version_tag}-win-{arch}.zip"
        url = f"https://nodejs.org/dist/{version_tag}/{filename}"
        folder = f"node-{version_tag}-win-{arch}"
    elif system == "linux":
        filename = f"node-{version_tag}-linux-{arch}.tar.xz"
        url = f"https://nodejs.org/dist/{version_tag}/{filename}"
        folder = f"node-{version_tag}-linux-{arch}"
    elif system == "darwin":
        filename = f"node-{version_tag}-darwin-{arch}.tar.gz"
        url = f"https://nodejs.org/dist/{version_tag}/{filename}"
        folder = f"node-{version_tag}-darwin-{arch}"
    else:
        fail(f"Unsupported operating system for automatic Node provisioning: {system}")

    return url, filename, folder


def download_with_progress(url: str, destination: Path) -> None:
    info(f"Downloading portable Node.js from official Node.js distribution ...")
    info(url)
    try:
        with urllib.request.urlopen(url, timeout=45) as response, destination.open("wb") as target:
            total_raw = response.headers.get("Content-Length")
            total = int(total_raw) if total_raw and total_raw.isdigit() else 0
            downloaded = 0
            last_percent = -1
            while True:
                chunk = response.read(1024 * 1024)
                if not chunk:
                    break
                target.write(chunk)
                downloaded += len(chunk)
                if total:
                    percent = int(downloaded * 100 / total)
                    if percent // 10 != last_percent // 10:
                        print(f"        {percent}%")
                        last_percent = percent
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        if destination.exists():
            destination.unlink(missing_ok=True)
        fail(
            "Node.js/npm is not installed and automatic portable download failed. "
            f"Reason: {exc}\nInstall Node.js 20+ manually, then run `python run.py` again."
        )


def ensure_node() -> tuple[str, str, dict]:
    system_node = command_path("node")
    system_npm = command_path("npm.cmd" if os.name == "nt" else "npm")

    if system_node and system_npm:
        major = node_major(system_node)
        if major is not None and major >= MIN_NODE_MAJOR:
            version = subprocess.check_output([system_node, "--version"], text=True).strip()
            ok(f"Node.js {version} and npm found on system PATH")
            return system_node, system_npm, os.environ.copy()
        warn(f"System Node.js is older than recommended major version {MIN_NODE_MAJOR}; using portable runtime instead.")

    url, filename, folder_name = portable_node_target()
    RUNTIME_DIR.mkdir(parents=True, exist_ok=True)
    node_root = RUNTIME_DIR / folder_name

    node_bin = node_root if os.name == "nt" else node_root / "bin"
    node_exe = node_bin / ("node.exe" if os.name == "nt" else "node")
    npm_exe = node_bin / ("npm.cmd" if os.name == "nt" else "npm")

    if not node_exe.exists() or not npm_exe.exists():
        archive = RUNTIME_DIR / filename
        if not archive.exists():
            download_with_progress(url, archive)

        info("Extracting portable Node.js runtime ...")
        try:
            if filename.endswith(".zip"):
                with zipfile.ZipFile(archive, "r") as zf:
                    zf.extractall(RUNTIME_DIR)
            else:
                with tarfile.open(archive, "r:*") as tf:
                    tf.extractall(RUNTIME_DIR)
        except (zipfile.BadZipFile, tarfile.TarError, OSError) as exc:
            archive.unlink(missing_ok=True)
            fail(f"Could not extract portable Node.js runtime: {exc}")

        archive.unlink(missing_ok=True)

    if not node_exe.exists() or not npm_exe.exists():
        fail("Portable Node.js extraction completed but node/npm could not be located.")

    env = os.environ.copy()
    env["PATH"] = str(node_bin) + os.pathsep + env.get("PATH", "")
    version = subprocess.check_output([str(node_exe), "--version"], text=True, env=env).strip()
    ok(f"Portable Node.js {version} ready at {node_root.relative_to(ROOT)}")
    return str(node_exe), str(npm_exe), env


def ensure_frontend(state: dict, npm_exe: str, env: dict) -> None:
    package_files = [FRONTEND_DIR / "package.json"]
    if (FRONTEND_DIR / "package-lock.json").exists():
        package_files.append(FRONTEND_DIR / "package-lock.json")
    pkg_hash = fingerprint(package_files)
    node_modules = FRONTEND_DIR / "node_modules"

    needs_install = not node_modules.exists() or state.get("frontend_packages") != pkg_hash
    if needs_install:
        info("Installing/checking frontend packages ...")
        if (FRONTEND_DIR / "package-lock.json").exists():
            run_checked([npm_exe, "install"], cwd=FRONTEND_DIR, env=env)
        else:
            run_checked([npm_exe, "install"], cwd=FRONTEND_DIR, env=env)
        # package-lock may have been created/updated by npm; fingerprint the final package metadata.
        final_files = [FRONTEND_DIR / "package.json"]
        if (FRONTEND_DIR / "package-lock.json").exists():
            final_files.append(FRONTEND_DIR / "package-lock.json")
        state["frontend_packages"] = fingerprint(final_files)
        save_state(state)
        ok("Frontend dependencies are ready")
    else:
        ok("Frontend dependencies already match package metadata")


def port_is_open(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.25)
        return sock.connect_ex((HOST, port)) == 0


def wait_for_port(port: int, process: subprocess.Popen, timeout: float = 45.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        if port_is_open(port):
            return True
        time.sleep(0.25)
    return False


def start_services(npm_exe: str, node_env: dict) -> tuple[subprocess.Popen, subprocess.Popen]:
    if port_is_open(BACKEND_PORT):
        fail(f"Port {BACKEND_PORT} is already in use. Close the existing service and run again.")
    if port_is_open(FRONTEND_PORT):
        fail(f"Port {FRONTEND_PORT} is already in use. Close the existing service and run again.")

    info("Starting FastAPI backend ...")
    backend = subprocess.Popen(
        [
            str(venv_python()),
            "-m",
            "uvicorn",
            "app.main:app",
            "--host",
            HOST,
            "--port",
            str(BACKEND_PORT),
        ],
        cwd=BACKEND_DIR,
    )

    if not wait_for_port(BACKEND_PORT, backend):
        terminate_process(backend)
        fail("Backend did not become ready. Review the error output above.")
    ok(f"Backend running: {BACKEND_URL}")

    info("Starting React/Vite frontend ...")
    frontend = subprocess.Popen(
        [
            npm_exe,
            "run",
            "dev",
            "--",
            "--host",
            HOST,
            "--port",
            str(FRONTEND_PORT),
        ],
        cwd=FRONTEND_DIR,
        env=node_env,
    )

    if not wait_for_port(FRONTEND_PORT, frontend):
        terminate_process(frontend)
        terminate_process(backend)
        fail("Frontend did not become ready. Review the error output above.")
    ok(f"Frontend running: {FRONTEND_URL}")
    return backend, frontend


def terminate_process(process: subprocess.Popen | None) -> None:
    if process is None or process.poll() is not None:
        return
    try:
        if os.name == "nt":
            process.send_signal(signal.CTRL_BREAK_EVENT)
            try:
                process.wait(timeout=4)
                return
            except subprocess.TimeoutExpired:
                process.terminate()
        else:
            process.terminate()
        try:
            process.wait(timeout=4)
        except subprocess.TimeoutExpired:
            process.kill()
    except Exception:
        try:
            process.kill()
        except Exception:
            pass


def main() -> None:
    banner()
    check_project_layout()
    check_python()

    # Explicitly preserve environment files. The launcher never creates/copies/removes .env.
    env_path = ROOT / ".env"
    if env_path.exists():
        ok("Existing .env detected and will be left untouched")
    else:
        info("No .env detected; continuing without creating one")

    state = load_state()
    ensure_backend(state)
    _, npm_exe, node_env = ensure_node()
    ensure_frontend(state, npm_exe, node_env)

    backend: subprocess.Popen | None = None
    frontend: subprocess.Popen | None = None
    try:
        backend, frontend = start_services(npm_exe, node_env)
        print("\n" + "-" * 70)
        print(f"{APP_NAME} is ready.")
        print(f"Application : {FRONTEND_URL}")
        print(f"API         : {BACKEND_URL}")
        print(f"API Docs    : {BACKEND_URL}/docs")
        print("Press Ctrl+C once to stop both services.")
        print("-" * 70 + "\n")

        try:
            webbrowser.open(FRONTEND_URL, new=2)
        except Exception:
            warn(f"Could not open the browser automatically. Open {FRONTEND_URL} manually.")

        while True:
            if backend.poll() is not None:
                fail("Backend process stopped unexpectedly.")
            if frontend.poll() is not None:
                fail("Frontend process stopped unexpectedly.")
            time.sleep(1)

    except KeyboardInterrupt:
        print("\nStopping Aurelia Contract Studio ...")
    finally:
        terminate_process(frontend)
        terminate_process(backend)
        ok("Local services stopped")


if __name__ == "__main__":
    main()
