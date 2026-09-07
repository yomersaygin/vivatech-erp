import json
import os
import shutil
import subprocess
import sys
import time
import urllib.request
import webbrowser
from pathlib import Path

APP_NAME = "Vivatech ERP"
DEFAULT_TIMEOUT = 180


def app_root() -> Path:
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parents[1]


def load_config(root: Path | None = None) -> dict:
    root = Path(root) if root is not None else app_root()
    path = root / "CONFIG" / "vivatech.json"
    if not path.exists():
        return {
            "url": "http://localhost:8080",
            "runtime_dir": "RUNTIME/frappe_docker",
            "compose_file": "compose.vivatech.yaml",
            "health_timeout_seconds": DEFAULT_TIMEOUT,
            "open_browser": True,
        }
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def run_hidden(args, cwd=None, timeout=None):
    flags = 0
    startupinfo = None
    if os.name == "nt":
        flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        startupinfo = subprocess.STARTUPINFO()
        startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    return subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=timeout, creationflags=flags, startupinfo=startupinfo)


def docker_available() -> bool:
    if not shutil.which("docker"):
        return False
    try:
        return run_hidden(["docker", "info"], timeout=15).returncode == 0
    except Exception:
        return False


def start_docker_desktop() -> bool:
    if os.name != "nt":
        return False
    candidates = [
        Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Docker" / "Docker" / "Docker Desktop.exe",
        Path(os.environ.get("ProgramW6432", r"C:\Program Files")) / "Docker" / "Docker" / "Docker Desktop.exe",
    ]
    for exe in candidates:
        if exe.exists():
            try:
                subprocess.Popen([str(exe)], creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))
                return True
            except Exception:
                pass
    return False


def wait_for_docker(timeout=120) -> bool:
    started = time.time()
    while time.time() - started < timeout:
        if docker_available():
            return True
        time.sleep(3)
    return False


def compose_file_path(root: Path, cfg: dict) -> tuple[Path, Path]:
    runtime_dir = root / cfg.get("runtime_dir", "RUNTIME/frappe_docker")
    preferred = cfg.get("compose_file", "compose.yaml")
    candidates = [runtime_dir / preferred, runtime_dir / "compose.yaml", runtime_dir / "docker-compose.yml", runtime_dir / "pwd.yml"]
    for file in candidates:
        if file.exists():
            return runtime_dir, file
    return runtime_dir, runtime_dir / preferred


def start_stack(root: Path, cfg: dict):
    runtime_dir, compose_file = compose_file_path(root, cfg)
    if not runtime_dir.exists():
        raise RuntimeError("ERP runtime henüz kurulmamış. RUNTIME\\FIRST-RUN-SETUP.bat dosyasını çalıştırın.")
    if not compose_file.exists():
        raise RuntimeError("compose.vivatech.yaml bulunamadı. RUNTIME\\FIRST-RUN-SETUP.bat ile ilk kurulumu tamamlayın.")
    project = cfg.get("compose_project", "vivatech")
    r = run_hidden(["docker", "compose", "-p", project, "-f", str(compose_file), "up", "-d"], cwd=str(runtime_dir), timeout=180)
    if r.returncode != 0:
        raise RuntimeError((r.stderr or r.stdout or "Docker compose başlatılamadı.").strip())


def health_ok(url: str) -> bool:
    try:
        ping_url = url.rstrip("/") + "/api/method/ping"
        req = urllib.request.Request(ping_url, headers={"User-Agent": APP_NAME})
        with urllib.request.urlopen(req, timeout=5) as resp:
            if resp.status != 200:
                return False
            body = resp.read().decode("utf-8", errors="ignore").lower()
            return "pong" in body or '"message"' in body
    except Exception:
        return False


def wait_for_site(url: str, timeout: int) -> bool:
    started = time.time()
    while time.time() - started < timeout:
        if health_ok(url):
            return True
        time.sleep(3)
    return False


def show_error(message: str):
    if os.name == "nt":
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, message, APP_NAME, 0x10)
            return
        except Exception:
            pass
    print(message, file=sys.stderr)


def main() -> int:
    root = app_root()
    cfg = load_config()
    url = cfg.get("url", "http://localhost:8080")
    timeout = int(cfg.get("health_timeout_seconds", DEFAULT_TIMEOUT))
    if health_ok(url):
        if cfg.get("open_browser", True):
            webbrowser.open(url)
        return 0
    if not docker_available():
        start_docker_desktop()
        if not wait_for_docker(timeout=120):
            show_error("Docker çalışmıyor.\n\nDocker Desktop'ı başlatın ve tekrar deneyin.")
            return 10
    try:
        start_stack(root, cfg)
    except Exception as e:
        show_error(f"Vivatech ERP başlatılamadı.\n\n{e}")
        return 20
    if not wait_for_site(url, timeout):
        show_error("ERPNext/Vivatech servisi zamanında hazır olmadı.\n\nRUNTIME klasöründeki durum ve log scriptlerini kontrol edin.")
        return 30
    if cfg.get("open_browser", True):
        webbrowser.open(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
