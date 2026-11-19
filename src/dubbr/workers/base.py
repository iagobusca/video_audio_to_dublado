"""Base para workers HTTP locais (processos isolados)."""
import subprocess
import sys
from pathlib import Path


class WorkerBase:
    def __init__(self, name, venv_python, script, port):
        self.name = name
        self.venv_python = Path(venv_python)
        self.script = Path(script)
        self.port = port
        self.proc = None

    def start(self):
        self.proc = subprocess.Popen(
            [str(self.venv_python), str(self.script), "--port", str(self.port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
        )
        return self.proc

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=10)
            except Exception:
                self.proc.kill()
        self.proc = None

    def is_alive(self):
        return self.proc is not None and self.proc.poll() is None
