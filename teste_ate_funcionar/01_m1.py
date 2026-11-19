"""Teste M1 ingestao."""
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from dubbr.pipeline import m1_ingest
src = ROOT / "youtube_download" / "Carro brasileiro 🇧🇷 chegando na fronteira da Inglaterra 🏴󠁧󠁢󠁥󠁮󠁧󠁿 veja como fomos recebidos! [jOD_H6wH7ac].mp4"
wd = ROOT / "teste_ate_funcionar" / "out_m1"
wd.mkdir(parents=True, exist_ok=True)
import sys
sys.stdout.reconfigure(encoding="utf-8")
r = m1_ingest.run(str(src), wd)
print(repr(r))
