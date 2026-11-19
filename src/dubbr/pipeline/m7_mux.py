"""M7 - mux final (ffmpeg) - stub."""


def run(video_path, audio_path, workdir, srt_path=None):
    out = Path(workdir) / "dublado.mp4" if video_path else Path(workdir) / "dublado.wav"
    return str(out)
