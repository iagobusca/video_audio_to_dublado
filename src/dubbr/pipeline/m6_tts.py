"""M6 - TTS real: clona a voz do falante original e monta a trilha dublada no tempo certo."""
import subprocess
from pathlib import Path
import numpy as np
import soundfile as sf
from ..job_manager import JobCancelled
from ..workers.client import Worker

SR = 24000
SCRIPTS = {"chatterbox-ptbr": ("tts_chatterbox.py", 8022),
           "f5-tts-ptbr": ("tts_f5.py", 8023),
           "qwen3-tts-1.7b-base": ("tts_qwen.py", 8021),
           "qwen3-tts-0.6b-base": ("tts_qwen.py", 8021)}


def _dur(path):
    return float(sf.info(str(path)).duration)


def _cut(src, start, end, out):
    subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-to", str(end),
                    "-i", str(src), "-ar", str(SR), "-ac", "1", str(out)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def _atempo(src, ratio, out):
    filters, r = [], ratio
    while r > 2.0:
        filters.append("atempo=2.0")
        r /= 2.0
    while r < 0.5:
        filters.append("atempo=0.5")
        r /= 0.5
    filters.append(f"atempo={r:.4f}")
    subprocess.run(["ffmpeg", "-y", "-i", str(src), "-filter:a", ",".join(filters), str(out)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run(segments, vocal_path, workdir, backend="chatterbox-ptbr", jm=None, job_id=None, emit=None):
    wd = Path(workdir)
    tts_dir = wd / "tts"
    tts_dir.mkdir(exist_ok=True)
    cand = [s for s in segments if s["end"] - s["start"] >= 3.0] or segments
    ref = max(cand, key=lambda s: s["end"] - s["start"])
    ref_wav = tts_dir / "ref.wav"
    _cut(vocal_path, ref["start"], min(ref["end"], ref["start"] + 12.0), ref_wav)
    ref_text = ref.get("text", "")
    script, port = SCRIPTS.get(backend, SCRIPTS["chatterbox-ptbr"])
    extra = []
    if script == "tts_chatterbox.py":
        from ..config import MODELS_DIR
        pack = MODELS_DIR / "chatterbox-ptbr"
        if pack.exists():
            extra = ["--pack", str(pack)]
    total = len(segments)
    with Worker("tts", script, port, extra_args=extra) as w:
        for i, s in enumerate(segments):
            if jm and job_id and jm.jobs[job_id].status == "cancelled":
                raise JobCancelled()
            txt = (s.get("text_pt") or s.get("text") or "").strip()
            if not txt:
                continue
            raw = tts_dir / f"seg_{i:04d}.wav"
            exag = float(np.clip(0.3 + 0.5 * s.get("arousal", 0.5), 0.25, 1.5))
            r = w.post("/tts", {"text": txt, "ref_wav": str(ref_wav), "ref_text": ref_text,
                                "language_id": "pt", "exaggeration": exag}, timeout=900)
            raw.write_bytes(r.content)
            target = s["end"] - s["start"]
            d = _dur(raw)
            fit = raw
            if d > 0 and target > 0:
                ratio = d / target
                if not (0.9 <= ratio <= 1.1):
                    fit = tts_dir / f"fit_{i:04d}.wav"
                    _atempo(raw, float(np.clip(ratio, 0.5, 2.0)), fit)
            s["tts_wav"] = str(fit)
            if emit:
                emit(i + 1, total)
    total_dur = max((s["end"] for s in segments), default=0.0) + 0.5
    track = np.zeros(int(total_dur * SR), dtype=np.float32)
    for s in segments:
        p = s.get("tts_wav")
        if not p:
            continue
        wav, sr2 = sf.read(p, dtype="float32")
        if wav.ndim > 1:
            wav = wav.mean(axis=1)
        if sr2 != SR:
            raise RuntimeError(f"sample rate inesperado do worker: {sr2} (esperado {SR})")
        off = int(s["start"] * SR)
        end = min(off + len(wav), len(track))
        if end > off:
            track[off:end] += wav[:end - off]
    peak = float(np.max(np.abs(track))) if len(track) else 0.0
    if peak > 0.95:
        track *= 0.95 / peak
    out = wd / "dub_track.wav"
    sf.write(str(out), track, SR)
    return str(out)
