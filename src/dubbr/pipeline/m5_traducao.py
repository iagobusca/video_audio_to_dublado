"""M5 - traducao real EN->pt-BR via llama-server (LFM3-Omni GGUF) + glossario."""
import json
import subprocess
import time
from pathlib import Path
import requests
import yaml
from ..config import ROOT, GLOSSARIO, MODELS_DIR

LLAMA = ROOT / "bin" / "llama.cpp" / "llama-server.exe"
PORT = 8030


def _glossario():
    try:
        return (yaml.safe_load(GLOSSARIO.read_text(encoding="utf-8")) or {}).get("termos", {}) or {}
    except Exception:
        return {}


def _start_server(variante, ctx=4096, ngl=99):
    gguf = MODELS_DIR / "lfm3-omni-2b" / f"LFM3-Omni-2B-{variante}.gguf"
    if not gguf.exists():
        raise FileNotFoundError(f"Modelo de traducao ausente: {gguf} (baixe na aba Modelos)")
    if not LLAMA.exists():
        raise FileNotFoundError("bin/llama.cpp/llama-server.exe ausente (rode bin/get_binaries.py)")
    proc = subprocess.Popen([str(LLAMA), "-m", str(gguf), "-c", str(ctx), "-ngl", str(ngl),
                             "--host", "127.0.0.1", "--port", str(PORT)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    t0 = time.time()
    while time.time() - t0 < 180:
        if proc.poll() is not None:
            raise RuntimeError("llama-server morreu no startup")
        try:
            if requests.get(f"http://127.0.0.1:{PORT}/health", timeout=2).ok:
                return proc
        except requests.RequestException:
            pass
        time.sleep(1)
    proc.kill()
    raise TimeoutError("llama-server nao ficou pronto em 180s")


def _chat(messages, temperature=0.2):
    r = requests.post(f"http://127.0.0.1:{PORT}/v1/chat/completions",
                      json={"messages": messages, "temperature": temperature, "max_tokens": 2048},
                      timeout=300)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()


def run(segments, variante="Q4_K_M", jm=None, job_id=None):
    termos = _glossario()
    gloss = "\n".join(f"- {k} -> {v}" for k, v in termos.items())
    sys_prompt = ("Voce e um tradutor profissional EN->pt-BR para dublagem. Traduza preservando "
                  "sentido, tom e emocao, em portugues brasileiro natural e falado. "
                  "Responda APENAS com um array JSON de strings, na mesma ordem dos textos. "
                  + (f"Glossario obrigatorio:\n{gloss}" if gloss else ""))
    proc = _start_server(variante)
    try:
        B = 8
        n = len(segments)
        for i in range(0, n, B):
            batch = segments[i:i + B]
            texts = [s.get("text", "") for s in batch]
            out = _chat([{"role": "system", "content": sys_prompt},
                         {"role": "user", "content": json.dumps(texts, ensure_ascii=False)}])
            try:
                trads = json.loads(out[out.find("["):out.rfind("]") + 1])
                if not (isinstance(trads, list) and len(trads) == len(batch)):
                    raise ValueError("contagem divergente")
            except Exception:
                trads = [_chat([{"role": "system", "content": sys_prompt},
                                {"role": "user", "content": t}]) for t in texts]
            for s, t in zip(batch, trads):
                s["text_pt"] = str(t).strip()
                for k, v in termos.items():
                    s["text_pt"] = s["text_pt"].replace(k, v)
            if jm:
                jm.emit(job_id, "M5", "rodando", min(100, (i + B) / max(n, 1) * 100),
                        f"traduzindo {min(i + B, n)}/{n}")
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except Exception:
            proc.kill()
    return segments
