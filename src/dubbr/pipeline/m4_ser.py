"""M4 - SER real (audeering arousal/valence/dominance) + emocao por segmento."""
import subprocess
from pathlib import Path
from ..workers.client import Worker


def _label(arousal, valence):
    if arousal >= 0.6 and valence >= 0.55:
        return "feliz/exaltado"
    if arousal >= 0.6 and valence < 0.45:
        return "raiva/tenso"
    if arousal < 0.4 and valence < 0.45:
        return "triste/calmo"
    return "neutro"


def _cut(src, start, end, out):
    subprocess.run(["ffmpeg", "-y", "-ss", str(start), "-to", str(end),
                    "-i", str(src), "-ar", "16000", "-ac", "1", str(out)],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def run(segments, vocal_path, workdir):
    wd = Path(workdir)
    clips = wd / "ser_clips"
    clips.mkdir(exist_ok=True)
    with Worker("ser", "ser.py", 8011) as w:
        for i, s in enumerate(segments):
            clip = clips / f"seg_{i:04d}.wav"
            _cut(vocal_path, s["start"], s["end"], clip)
            r = w.post("/ser", {"audio_path": str(clip)}).json()
            s["arousal"] = float(r.get("arousal", 0.5))
            s["valence"] = float(r.get("valence", 0.5))
            s["emotion"] = _label(s["arousal"], s["valence"])
            s["ref_text"] = s.get("text", "")
    return segments
