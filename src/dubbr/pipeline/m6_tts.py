"""M6 - TTS (Qwen3/Chatterbox/F5) - stub."""


def run(segments, backend="qwen3-tts-1.7b-base", workdir=None, progress_cb=None):
    out = []
    for i, s in enumerate(segments):
        if progress_cb:
            progress_cb(i, len(segments))
        out.append({"segment": i, "wav": None})
    return out
