"""M5 - traducao LFM3-Omni - stub."""


def run(segments, glossario=None):
    for s in segments:
        s["text_pt"] = s.get("text", "")
    return segments
