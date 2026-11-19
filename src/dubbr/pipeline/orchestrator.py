"""Orquestrador real do pipeline M1-M7 (video dublado ou audio dublado)."""
import json
from pathlib import Path
from . import m1_ingest, m2_separacao, m3_asr, m4_ser, m5_traducao, m6_tts, m7_mux
from ..job_manager import JobCancelled

PRESET_MAP = {
    "leve":        {"asr": "leve",        "trad": "Q4_K_M", "tts": "chatterbox-ptbr"},
    "equilibrado": {"asr": "equilibrado", "trad": "Q8_0",   "tts": "chatterbox-ptbr"},
    "maximo":      {"asr": "maximo",      "trad": "F16",     "tts": "chatterbox-ptbr"},
}


def _check_cancel(job):
    if job.status == "cancelled":
        raise JobCancelled()


def run_pipeline(job, jm, backend_tts=None, preset=None):
    preset = preset or job.preset or "equilibrado"
    cfg = PRESET_MAP.get(preset, PRESET_MAP["equilibrado"])
    backend = backend_tts or job.extras.get("backend_tts") or cfg["tts"]
    wd = Path(job.dir)
    meta_p, seg_p = wd / "meta.json", wd / "segmentos.json"
    job.status = "running"
    jm.emit(job.id, "PIPE", "rodando", 0, f"iniciando (preset={preset}, tts={backend})")
    try:
        resume = job.extras.get("resume") and seg_p.exists() and meta_p.exists()
        if resume:
            meta = json.loads(meta_p.read_text(encoding="utf-8"))
            segs = json.loads(seg_p.read_text(encoding="utf-8"))
            jm.emit(job.id, "PIPE", "rodando", 0, "retomando do checkpoint (M6)")
        else:
            _check_cancel(job)
            jm.emit(job.id, "M1", "rodando", 0, "ingestao")
            meta = m1_ingest.run(job.entrada, wd)
            meta_p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            jm.emit(job.id, "M1", "ok", 100, "ingestao ok")
            _check_cancel(job)
            jm.emit(job.id, "M2", "rodando", 0, "separacao vocal")
            sep = m2_separacao.run(meta["audio"], wd)
            meta.update(sep)
            meta_p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            jm.emit(job.id, "M2", "ok", 100, "separacao ok")
            _check_cancel(job)
            jm.emit(job.id, "M3", "rodando", 0, "asr (extracao de texto)")
            segs = m3_asr.run(sep["vocal"], wd, preset=cfg["asr"])
            jm.emit(job.id, "M3", "ok", 100, f"asr: {len(segs)} segmentos")
            _check_cancel(job)
            jm.emit(job.id, "M4", "rodando", 0, "ser (emocao)")
            segs = m4_ser.run(segs, sep["vocal"], wd)
            jm.emit(job.id, "M4", "ok", 100, "ser ok")
            _check_cancel(job)
            jm.emit(job.id, "M5", "rodando", 0, "traducao EN->pt-BR")
            segs = m5_traducao.run(segs, variante=cfg["trad"], jm=jm, job_id=job.id)
            seg_p.write_text(json.dumps(segs, ensure_ascii=False, indent=2), encoding="utf-8")
            meta_p.write_text(json.dumps(meta, ensure_ascii=False), encoding="utf-8")
            jm.emit(job.id, "M5", "ok", 100, "traducao ok")
            if job.extras.get("revisar"):
                job.status = "awaiting_review"
                jm.emit(job.id, "M5", "aguardando", 100,
                        f"revise {seg_p} e clique em Retomar")
                return None
        _check_cancel(job)
        if not segs:
            raise RuntimeError("nenhum segmento para sintetizar")
        jm.emit(job.id, "M6", "rodando", 0, "tts (dublagem)")
        track = m6_tts.run(segs, meta.get("vocal") or meta["audio"], wd, backend=backend,
                           jm=jm, job_id=job.id,
                           emit=lambda i, n: jm.emit(job.id, "M6", "rodando", i / max(n, 1) * 100, f"seg {i}/{n}"))
        seg_p.write_text(json.dumps(segs, ensure_ascii=False, indent=2), encoding="utf-8")
        jm.emit(job.id, "M6", "ok", 100, "tts ok")
        _check_cancel(job)
        jm.emit(job.id, "M7", "rodando", 0, "mux final")
        out = m7_mux.run(meta.get("video"), track, wd, instrumental=meta.get("instrumental"))
        jm.emit(job.id, "M7", "ok", 100, "concluido")
        job.status = "done"
        job.result = out
        jm.emit(job.id, "PIPE", "ok", 100, out)
        return out
    except JobCancelled:
        job.status = "cancelled"
        jm.emit(job.id, "PIPE", "erro", 0, "cancelado pelo usuario")
        return None
    except Exception as e:
        job.status = "failed"
        jm.emit(job.id, "PIPE", "erro", 0, f"falha: {e}")
        raise
