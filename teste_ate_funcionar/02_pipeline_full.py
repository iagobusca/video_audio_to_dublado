"""Teste pipeline completo em um video real."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.stdout.reconfigure(encoding="utf-8")
from dubbr.job_manager import JobManager
from dubbr.pipeline.orchestrator import run_pipeline

src = ROOT / "youtube_download" / "Carro brasileiro 🇧🇷 chegando na fronteira da Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿 veja como fomos recebidos! [jOD_H6wH7ac].mp4"
jm = JobManager()
j = jm.submit(str(src), preset="leve", extras={"revisar": False})
print("job", j.id, j.status)
# consumir eventos em thread
import threading
def drain():
    while j.status in ("queued", "running"):
        evs = jm.bus.drain()
        for e in evs:
            print(f"[{e['estagio']}] {e['status']} {e['pct']:.0f}% - {e['msg']}")
        time.sleep(1)
threading.Thread(target=drain, daemon=True).start()
try:
    res = run_pipeline(j, jm)
    print("RESULT:", res)
except Exception as e:
    import traceback; traceback.print_exc()
print("STATUS:", j.status)
print("RESULT:", j.result)
