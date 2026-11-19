"""M7 - mux real: video dublado (mp4, video sem re-encode) ou audio dublado (wav)."""
import json
import subprocess
from pathlib import Path


def _probe_dur(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "json", str(path)], capture_output=True, text=True, check=True)
    return float(json.loads(r.stdout)["format"]["duration"])


def run(video_path, audio_track, workdir, instrumental=None, bed_gain=0.12):
    wd = Path(workdir)
    if video_path:
        out = wd / "dublado.mp4"
        cmd = ["ffmpeg", "-y", "-i", str(video_path), "-i", str(audio_track)]
        if instrumental and Path(instrumental).exists():
            cmd += ["-i", str(instrumental), "-filter_complex",
                    f"[1:a]volume=1.0[d];[2:a]volume={bed_gain}[b];[d][b]amix=inputs=2:duration=first:normalize=0[a]",
                    "-map", "0:v:0", "-map", "[a]"]
        else:
            cmd += ["-map", "0:v:0", "-map", "1:a:0"]
        cmd += ["-c:v", "copy", "-c:a", "aac", "-b:a", "192k", "-shortest", str(out)]
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    else:
        out = wd / "dublado.wav"
        subprocess.run(["ffmpeg", "-y", "-i", str(audio_track), "-ar", "48000", "-ac", "2", str(out)],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError("mux falhou: saida vazia")
    if _probe_dur(out) <= 0:
        raise RuntimeError("mux falhou: duracao zero")
    return str(out)
