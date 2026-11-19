"""Chama run_pipeline diretamente para ver o traceback."""
import sys, traceback
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dubbr.job_manager import JobManager
from dubbr.pipeline.orchestrator import run_pipeline
jm = JobManager()
j = jm.submit(str(ROOT / "saidas" / "dummy.wav"))
j.extras["resume"] = False
try:
    run_pipeline(j, jm)
    print("RESULT:", j.result)
except Exception:
    traceback.print_exc()
print("STATUS:", j.status)
