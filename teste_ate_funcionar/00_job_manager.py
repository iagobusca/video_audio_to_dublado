"""Testa se o JobManager processa jobs (thread consumidora)."""
import sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dubbr.job_manager import JobManager
jm = JobManager()
print("thread alive:", jm._thread.is_alive())
j = jm.submit("dummy.wav", preset="leve")
print("submitted", j.id, j.status)
for i in range(20):
    time.sleep(0.5)
    print(i, j.id, j.status, jm.current.id if jm.current else None)
print("DONE")
