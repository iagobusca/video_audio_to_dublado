"""M2 - separacao vocal real (Demucs em worker isolado; processo morre -> VRAM livre)."""
from ..workers.client import Worker


def run(audio_path, workdir):
    try:
        with Worker("sep", "sep.py", 8012) as w:
            r = w.post("/separate", {"audio_path": str(audio_path), "workdir": str(workdir)}, timeout=1800)
            return r.json()
    except Exception as e:
        # Demucs ausente/falhou -> segue sem separacao (vocal = input)
        return {"vocal": str(audio_path), "instrumental": None, "sep_error": str(e)}
