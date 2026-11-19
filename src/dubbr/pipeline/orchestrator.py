"""Orquestrador do pipeline de dublagem."""
import json
from pathlib import Path
from . import m1_ingest, m2_separacao, m3_asr, m4_ser, m5_traducao, m6_tts, m7_mux


def run_pipeline(job, jm, backend_tts="qwen3-tts-1.7b-base"):
    wd = Path(job.dir)
    jm.emit(job.id, "M1", "rodando", 0, "ingestao")
    audio = m1_ingest.run(job.entrada, wd)
    jm.emit(job.id, "M1", "ok", 100, "ingestao ok")

    jm.emit(job.id, "M2", "rodando", 0, "separacao")
    sep = m2_separacao.run(audio, wd)
    jm.emit(job.id, "M2", "ok", 100, "separacao ok")

    jm.emit(job.id, "M3", "rodando", 0, "asr")
    segs = m3_asr.run(sep["vocal"], wd)
    jm.emit(job.id, "M3", "ok", 100, f"asr: {len(segs)} segs")

    jm.emit(job.id, "M4", "rodando", 0, "ser")
    segs = m4_ser.run(segs, wd)
    jm.emit(job.id, "M4", "ok", 100, "ser ok")

    jm.emit(job.id, "M5", "rodando", 0, "traducao")
    segs = m5_traducao.run(segs)
    jm.emit(job.id, "M5", "ok", 100, "traducao ok")

    # checkpoint segmentos.json
    (wd / "segmentos.json").write_text(json.dumps(segs, ensure_ascii=False, indent=2), encoding="utf-8")

    jm.emit(job.id, "M6", "rodando", 0, "tts")
    m6_tts.run(segs, backend=backend_tts, workdir=wd,
               progress_cb=lambda i, n: jm.emit(job.id, "M6", "rodando", i / n * 100, f"seg {i}/{n}"))
    jm.emit(job.id, "M6", "ok", 100, "tts ok")

    jm.emit(job.id, "M7", "rodando", 0, "mux")
    out = m7_mux.run(None, None, wd)
    jm.emit(job.id, "M7", "ok", 100, "concluido")
    job.status = "done"
    return out
