"""M4 - SER (audeering arousal/valence) + banco de refs - stub."""


def run(segments, workdir):
    for s in segments:
        s["emotion"] = "neutro"
        s["arousal"] = 0.5
        s["ref_text"] = s.get("text", "")
    return segments
