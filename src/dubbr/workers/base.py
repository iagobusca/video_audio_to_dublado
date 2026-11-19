"""Base para workers HTTP locais (processos isolados, log em arquivo)."""
import subprocess
from pathlib import Path
from ..config import LOGS_DIR


class WorkerBase:
    def __init__(self, name, venv_python, script, port, extra_args=None):
        self.name = name
        self.venv_python = Path(venv_python)
        self.script = Path(script)
        self.port = port
        self.extra_args = list(extra_args or [])
        self.proc = None
        self._log = None

    def start(self):
        if not self.venv_python.exists():
            raise FileNotFoundError(f"{self.venv_python} ausente - rode setup.ps1 (venv_workers)")
        LOGS_DIR.mkdir(parents=True, exist_ok=True)
        self._log = open(LOGS_DIR / f"worker_{self.name}.log", "ab")
        self.proc = subprocess.Popen(
            [str(self.venv_python), str(self.script), "--port", str(self.port)] + self.extra_args,
            stdout=self._log, stderr=subprocess.STDOUT)
        return self.proc

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        self.proc = None
        if self._log:
            self._log.close()
            self._log = None

    def is_alive(self):
        return self.proc is not None and self.proc.poll() is None
