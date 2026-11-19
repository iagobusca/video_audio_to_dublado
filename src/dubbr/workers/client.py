"""Cliente HTTP + ciclo de vida dos workers (processo isolado por estagio)."""
import time
from pathlib import Path
import requests
from .base import WorkerBase

import shutil
from ..config import ROOT
_candidates = [
    ROOT / "venv_workers" / "Scripts" / "python.exe",
    ROOT / "venv" / "Scripts" / "python.exe",
    ROOT / "bin" / "runtime" / "python" / "python.exe",
]
VENV_WORKERS = None
for c in _candidates:
    if c.exists():
        VENV_WORKERS = c
        break
if VENV_WORKERS is None:
    found = shutil.which("python")
    VENV_WORKERS = Path(found) if found else Path("python")


class Worker(WorkerBase):
    def __init__(self, name, script, port, extra_args=None):
        super().__init__(name, VENV_WORKERS, ROOT / "src" / "dubbr" / "workers" / script, port, extra_args)
        self.base_url = f"http://127.0.0.1:{port}"

    def wait_ready(self, timeout=300):
        t0 = time.time()
        while time.time() - t0 < timeout:
            if not self.is_alive():
                raise RuntimeError(f"worker {self.name} morreu no startup (veja logs/worker_{self.name}.log)")
            try:
                if requests.get(self.base_url + "/health", timeout=2).ok:
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)
        raise TimeoutError(f"worker {self.name} nao ficou pronto em {timeout}s")

    def post(self, path, payload, timeout=600):
        r = requests.post(self.base_url + path, json=payload, timeout=timeout)
        r.raise_for_status()
        return r

    def __enter__(self):
        self.start()
        self.wait_ready()
        return self

    def __exit__(self, *a):
        self.stop()
