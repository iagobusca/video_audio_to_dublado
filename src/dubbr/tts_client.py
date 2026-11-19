"""Facade de TTS para a UI (Modos A e B) - sobe/derruba o worker por chamada."""
from pathlib import Path
from .workers.client import Worker
from .config import MODELS_DIR


def synthesize(text, ref_wav=None, backend="chatterbox-ptbr", exaggeration=0.5, out_path=None):
    name, port = {"chatterbox-ptbr": ("tts_chatterbox.py", 8022),
                  "f5-tts-ptbr": ("tts_f5.py", 8023)}.get(backend, ("tts_chatterbox.py", 8022))
    extra = []
    pack = MODELS_DIR / "chatterbox-ptbr"
    if name == "tts_chatterbox.py" and pack.exists():
        extra = ["--pack", str(pack)]
    with Worker("tts-ui", name, port, extra_args=extra) as w:
        r = w.post("/tts", {"text": text, "ref_wav": str(ref_wav) if ref_wav else None,
                            "language_id": "pt", "exaggeration": exaggeration}, timeout=900)
    if out_path:
        Path(out_path).write_bytes(r.content)
        return str(out_path)
    return r.content
