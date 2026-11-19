"""Eventos de progresso para a UI (fila consumida por gr.Timer)."""
import queue
import time
from dataclasses import dataclass, asdict


@dataclass
class Evento:
    job_id: str
    estagio: str          # M1..M7 ou nome
    status: str           # aguardando/rodando/ok/fallback/erro
    pct: float            # 0..100
    msg: str
    segmento: str = ""
    vram_gb: float = 0.0
    ts: float = 0.0

    def __post_init__(self):
        if not self.ts:
            self.ts = time.time()

    def to_dict(self):
        return asdict(self)


class ProgressBus:
    def __init__(self):
        self.q = queue.Queue()

    def emit(self, ev: Evento):
        self.q.put(ev)

    def drain(self, maxn=200):
        out = []
        for _ in range(maxn):
            try:
                out.append(self.q.get_nowait().to_dict())
            except queue.Empty:
                break
        return out
