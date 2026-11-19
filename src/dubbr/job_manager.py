"""JobManager: fila real com consumidor, 1 job GPU por vez, checkpoint/resume."""
import json
import threading
import time
import uuid
from pathlib import Path
from .config import OUTPUT_DIR
from .progress import ProgressBus, Evento


class JobCancelled(Exception):
    pass


class Job:
    def __init__(self, entrada, preset="equilibrado", modo="dublagem", extras=None):
        self.id = uuid.uuid4().hex[:8]
        self.entrada = entrada
        self.preset = preset
        self.modo = modo
        self.extras = extras or {}
        self.status = "queued"   # queued/running/awaiting_review/done/failed/cancelled
        self.criado = time.time()
        self.result = None
        self.dir = OUTPUT_DIR / self.id
        self.dir.mkdir(parents=True, exist_ok=True)
        self.segmentos_path = self.dir / "segmentos.json"

    def to_dict(self):
        return {"id": self.id, "entrada": str(self.entrada), "preset": self.preset,
                "modo": self.modo, "status": self.status, "criado": self.criado,
                "dir": str(self.dir), "result": self.result, "extras": self.extras}


class JobManager:
    def __init__(self):
        self.jobs = {}
        self.queue = []
        self.bus = ProgressBus()
        self.current = None
        self._lock = threading.Lock()
        self._load()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def _persist(self):
        try:
            (OUTPUT_DIR / "jobs.json").write_text(
                json.dumps([j.to_dict() for j in self.jobs.values()], ensure_ascii=False),
                encoding="utf-8")
        except Exception:
            pass

    def _load(self):
        p = OUTPUT_DIR / "jobs.json"
        if not p.exists():
            return
        try:
            for d in json.loads(p.read_text(encoding="utf-8")):
                j = Job.__new__(Job)
                j.__dict__.update(d)
                j.dir = Path(d["dir"])
                j.extras = d.get("extras", {})
                j.segmentos_path = j.dir / "segmentos.json"
                if j.status in ("running", "queued"):
                    j.status = "failed"
                self.jobs[j.id] = j
        except Exception:
            pass

    def submit(self, entrada, preset="equilibrado", modo="dublagem", extras=None):
        j = Job(entrada, preset, modo, extras)
        with self._lock:
            self.jobs[j.id] = j
            self.queue.append(j.id)
        self._persist()
        self.emit(j.id, "PIPE", "aguardando", 0, "job enfileirado")
        return j

    def cancel(self, jid):
        j = self.jobs.get(jid)
        if j:
            j.status = "cancelled"
            if jid in self.queue:
                self.queue.remove(jid)
            self._persist()
        return j

    def resume(self, jid):
        j = self.jobs.get(jid)
        if j and j.status in ("failed", "cancelled", "awaiting_review"):
            j.extras["resume"] = j.segmentos_path.exists()
            j.status = "queued"
            with self._lock:
                if jid not in self.queue:
                    self.queue.append(jid)
            self._persist()
        return j

    def list_jobs(self):
        return [j.to_dict() for j in self.jobs.values()]

    def emit(self, jid, estagio, status, pct, msg, **kw):
        self.bus.emit(Evento(job_id=jid, estagio=estagio, status=status, pct=pct, msg=msg, **kw))

    def _loop(self):
        from .pipeline.orchestrator import run_pipeline
        while True:
            jid = None
            with self._lock:
                if self.queue and self.current is None:
                    jid = self.queue.pop(0)
            if jid:
                job = self.jobs.get(jid)
                if job is None or job.status != "queued":
                    continue
                self.current = job
                try:
                    run_pipeline(job, self)
                except Exception as e:
                    # JobCancelled ja seta status dentro do orchestrator
                    if job.status not in ("cancelled", "done"):
                        job.status = "failed"
                        self.emit(job.id, "PIPE", "erro", 0, f"falha: {e}")
                finally:
                    self.current = None
                    self._persist()
            time.sleep(0.5)
