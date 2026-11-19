"""JobManager: fila, 1 job GPU por vez, checkpoint/resume (ESPEC 4/5)."""
import uuid
import json
import time
from pathlib import Path
from .config import OUTPUT_DIR
from .progress import ProgressBus, Evento


class Job:
    def __init__(self, entrada, preset="equilibrado", modo="dublagem", extras=None):
        self.id = uuid.uuid4().hex[:8]
        self.entrada = entrada
        self.preset = preset
        self.modo = modo
        self.extras = extras or {}
        self.status = "queued"   # queued/running/done/failed/cancelled
        self.criado = time.time()
        self.dir = OUTPUT_DIR / self.id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.segmentos_path = self.dir / "segmentos.json"

    def to_dict(self):
        return {
            "id": self.id, "entrada": str(self.entrada), "preset": self.preset,
            "modo": self.modo, "status": self.status,
            "criado": self.criado, "dir": str(self.dir),
        }


class JobManager:
    def __init__(self):
        self.jobs = {}
        self.queue = []
        self.bus = ProgressBus()
        self.current = None

    def submit(self, entrada, preset="equilibrado", modo="dublagem", extras=None):
        j = Job(entrada, preset, modo, extras)
        self.jobs[j.id] = j
        self.queue.append(j.id)
        return j

    def cancel(self, jid):
        j = self.jobs.get(jid)
        if j:
            j.status = "cancelled"
        return j

    def resume(self, jid):
        j = self.jobs.get(jid)
        if j:
            j.status = "queued"
            if jid not in self.queue:
                self.queue.append(jid)
        return j

    def list_jobs(self):
        return [j.to_dict() for j in self.jobs.values()]

    def emit(self, jid, estagio, status, pct, msg, **kw):
        self.bus.emit(Evento(job_id=jid, estagio=estagio, status=status,
                            pct=pct, msg=msg, **kw))
