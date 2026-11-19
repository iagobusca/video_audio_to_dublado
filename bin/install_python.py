# install_python.py
# -*- coding: utf-8 -*-
"""
VersÃ£o: 2.0 (Suporte a Python Embed e WinPython)

Funcionalidades:
- LÃª py_list.json no mesmo diretÃ³rio do script/EXE.
- MODO PADRÃƒO (Python.org Embed):
    - Baixa ZIP, extrai, ajusta ._pth, instala pip/setuptools/wheel.
- MODO WINPYTHON (Se a chave no json tiver 'winpython'):
    - Baixa ZIP.
    - Extrai para temp.
    - Localiza a pasta interna do Python (onde estÃ¡ o python.exe).
    - Move essa pasta para bin/runtime/python.
    - NÃƒO altera configuraÃ§Ãµes (jÃ¡ vem pronto).

Uso CLI:
    python install_python.py
    python install_python.py winPython_3.13
    python install_python.py --requirements
    python install_python.py --requirements --run check_falhas.py

JSON Exemplo:
{
  "python_3.12": "https://www.python.org/.../python-3.12.7-embed-amd64.zip",
  "winPython_3.13": "https://github.com/.../WinPython64-3.13.11.0dot_post1.zip"
}
"""

import json
import shutil
import subprocess
import sys
import zipfile
import ssl
import os
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.request import urlopen

GET_PIP_URL = "https://bootstrap.pypa.io/get-pip.py"

def get_ssl_context():
    """Retorna contexto SSL que ignora erros de certificado."""
    try:
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx
    except:
        return None

# ===================== GERENCIADOR DE ERRO GLOBAL =====================

_LAST_ERROR: str = ""

def set_last_error(msg: str) -> None:
    global _LAST_ERROR
    _LAST_ERROR = str(msg)

def clear_last_error() -> None:
    global _LAST_ERROR
    _LAST_ERROR = ""

def get_last_error() -> str:
    return _LAST_ERROR

# ===================== UTILITÃRIOS DE PATH =====================

def app_root_dir() -> Path:
    """Retorna o diretÃ³rio raiz do projeto (pai de bin/)."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent.parent
    here = Path(__file__).resolve().parent
    if here.name.lower() == "bin":
        return here.parent
    return here

def get_script_dir() -> Path:
    """Retorna o diretÃ³rio onde o script/EXE estÃ¡ localizado (bin/)"""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


def get_runtime_dir() -> Path:
    """Retorna o diretorio do runtime embutido (bin/runtime)."""
    return get_script_dir() / "runtime"

# ===================== LEITURA DO py_list.json =====================

def load_py_url(py_name: str) -> str:
    """LÃª py_list.json e retorna a URL."""
    script_dir = get_script_dir()
    json_path = script_dir / "py_list.json"
    
    if not json_path.exists():
        raise RuntimeError(f"Arquivo py_list.json nÃ£o encontrado em {json_path!r}")

    with json_path.open("r", encoding="utf-8") as f:
        data: Dict[str, Any] = json.load(f)

    # Normaliza chaves para busca case-insensitive se necessÃ¡rio, 
    # mas por padrÃ£o busca exato primeiro.
    if py_name in data:
        url = data[py_name]
    else:
        # Tenta achar ignorando case ou espaÃ§os se falhar o exato
        found = None
        for k, v in data.items():
            if k.lower().replace(" ", "") == py_name.lower().replace(" ", ""):
                found = v
                break
        if not found:
            raise RuntimeError(f"Entrada {py_name!r} nÃ£o encontrada em {json_path!r}")
        url = found

    if not isinstance(url, str) or not url.strip():
        raise RuntimeError(f"URL invÃ¡lida para {py_name!r}")

    return url

# ===================== DOWNLOAD E EXTRAÃ‡ÃƒO GENÃ‰RICA =====================

def download_file(url: str, dest: Path) -> None:
    if dest.parent is not None:
        dest.parent.mkdir(parents=True, exist_ok=True)
    try:
        ctx = get_ssl_context()
        with urlopen(url, context=ctx) as resp, dest.open("wb") as f:
            shutil.copyfileobj(resp, f)
    except Exception as e:
        raise RuntimeError(f"Falha no download de {url}: {e}") from e

def find_7z_executable() -> Optional[Path]:
    """Localiza o 7z (7z.exe/7za.exe) no PATH ou em locais comuns de instalaÃ§Ã£o."""
    for name in ("7z.exe", "7za.exe"):
        found = shutil.which(name)
        if found:
            return Path(found)
    common_paths = [
        r"C:\Program Files\7-Zip\7z.exe",
        r"C:\Program Files (x86)\7-Zip\7z.exe",
        os.path.expandvars(r"%LOCALAPPDATA%\Programs\7-Zip\7z.exe"),
    ]
    for p in common_paths:
        if os.path.exists(p):
            return Path(p)
    return None

def extract_with_7z(zip_path: Path, dest_dir: Path) -> None:
    """Extrai o arquivo usando o 7-Zip (fallback para SFX/7z/NSIS)."""
    seven_zip = find_7z_executable()
    if seven_zip is None:
        raise RuntimeError("Falha com zipfile e 7-Zip nÃ£o encontrado no sistema.")
    dest_dir.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [str(seven_zip), "x", str(zip_path), f"-o{dest_dir}", "-y"],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    if result.returncode != 0:
        raise RuntimeError(f"7-Zip falhou ao extrair {zip_path!r} (cÃ³digo {result.returncode})")

def extract_zip(zip_path: Path, dest_dir: Path) -> None:
    if not zip_path.exists():
        raise RuntimeError(f"ZIP nÃ£o encontrado em {zip_path!r}")
    dest_dir.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            zf.extractall(dest_dir)
    except Exception as e:
        print(f"[install_python] zipfile falhou ({e}), tentando com 7-Zip...")
        try:
            extract_with_7z(zip_path, dest_dir)
        except Exception as e7:
            raise RuntimeError(
                f"Erro ao extrair {zip_path!r}: zipfile ({e}) e 7-Zip ({e7})"
            ) from e

# ===================== LÃ“GICA WINPYTHON =====================

def extract_winpython_logic(zip_path: Path, final_dest: Path) -> None:
    """
    Extrai o WinPython para uma pasta temporÃ¡ria, encontra a subpasta 
    que contÃ©m 'python.exe' e move ELA para final_dest.
    """
    temp_extract_dir = final_dest.parent / "temp_winpy_extract"
    if temp_extract_dir.exists():
        shutil.rmtree(temp_extract_dir)
    temp_extract_dir.mkdir(parents=True, exist_ok=True)

    print("[install_python] Extraindo WinPython (pode demorar)...")
    extract_zip(zip_path, temp_extract_dir)

    # Procura onde estÃ¡ o python.exe dentro da extraÃ§Ã£o
    # WinPython costuma ter estrutura: WinPython/python-3.x.x.amd64/python.exe
    found_exe = list(temp_extract_dir.rglob("python.exe"))
    
    if not found_exe:
        shutil.rmtree(temp_extract_dir)
        raise RuntimeError("NÃ£o foi possÃ­vel encontrar 'python.exe' dentro do pacote WinPython.")

    # Pega o primeiro python.exe encontrado e define seu diretÃ³rio pai como a pasta alvo
    source_python_dir = found_exe[0].parent
    
    print(f"[install_python] Pasta do Python localizada em: {source_python_dir.name}")

    # Move o conteÃºdo para o destino final (bin/runtime/python)
    # Se bin/runtime/python jÃ¡ existe (vazio ou criado antes), remove pra garantir
    if final_dest.exists():
        shutil.rmtree(final_dest)
    
    # Move a pasta inteira
    shutil.move(str(source_python_dir), str(final_dest))

    # Limpa o resto do WinPython (Launchers, settings, etc que ficaram no temp)
    shutil.rmtree(temp_extract_dir)

# ===================== AJUSTES PYTHON EMBED (Standard) =====================

def find_python_exe(root: Path) -> Path:
    candidates = list(root.rglob("python.exe"))
    if candidates: return candidates[0]
    candidates = list(root.rglob("python3"))
    if candidates: return candidates[0]
    raise RuntimeError(f"python nÃ£o encontrado dentro de {root!r}")

def patch_python_pth(python_exe: Path) -> None:
    # (Mesma lÃ³gica anterior: habilita import site)
    pth_path = python_exe.with_name("python312._pth")
    if not pth_path.exists():
        pths = list(python_exe.parent.glob("*._pth"))
        if pths: pth_path = pths[0]
        else: return

    try:
        original_text = pth_path.read_text(encoding="utf-8")
    except Exception:
        return

    lines = original_text.splitlines()
    changed = False
    new_lines = []
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith("#import site"):
            prefix_len = len(line) - len(stripped)
            new_lines.append(line[:prefix_len] + "import site")
            changed = True
        else:
            new_lines.append(line)

    if changed:
        new_text = "\n".join(new_lines)
        if original_text.endswith("\n") and not new_text.endswith("\n"):
            new_text += "\n"
        pth_path.write_text(new_text, encoding="utf-8")

def ensure_pip_and_tools(python_exe: Path) -> None:
    # (Mesma lÃ³gica anterior: instala pip, setuptools e wheel)
    try:
        subprocess.check_call([str(python_exe), "-m", "pip", "--version"], 
                              stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        pip_exists = True
    except:
        pip_exists = False

    if not pip_exists:
        get_pip_path = python_exe.parent / "get-pip.py"
        if not get_pip_path.exists():
            print("[install_python] Baixando get-pip.py...")
            try:
                ctx = get_ssl_context()
                with urlopen(GET_PIP_URL, context=ctx) as resp, get_pip_path.open("wb") as f:
                    shutil.copyfileobj(resp, f)
            except Exception as e:
                raise RuntimeError(f"Erro download get-pip: {e}")

        print("[install_python] Instalando pip...")
        try:
            subprocess.check_call([str(python_exe), str(get_pip_path)])
        except Exception as e:
            raise RuntimeError(f"Erro ao instalar pip: {e}")

    print("[install_python] Verificando setuptools e wheel...")
    try:
        subprocess.check_call(
            [str(python_exe), "-m", "pip", "install", "--upgrade", "setuptools", "wheel"],
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
        )
    except:
        print("AVISO: Falha ao instalar setuptools/wheel.", file=sys.stderr)

# ===================== INSTALACAO DO REQUIREMENTS.TXT =====================

def install_requirements(python_exe: Path) -> bool:
    """Instala o requirements.txt no Python embutido (com marcador .requirements-installed)."""
    root = app_root_dir()
    req_file = root / "requirements.txt"
    marker = get_runtime_dir() / ".requirements-installed"

    if not req_file.exists():
        msg = f"requirements.txt nao encontrado em {req_file!r}"
        print(f"[install_python] {msg}")
        set_last_error(msg)
        return False

    if marker.exists():
        print("[install_python] requirements.txt ja instalados (marcador presente).")
        return True

    print("[install_python] Instalando requirements.txt...")
    try:
        subprocess.check_call(
            [str(python_exe), "-m", "pip", "install", "--upgrade", "-r", str(req_file)]
        )
    except Exception as e:
        set_last_error(f"Falha ao instalar requirements.txt: {e}")
        return False

    marker.write_text("ok", encoding="utf-8")
    print("[install_python] requirements.txt instalado com sucesso.")
    return True

# ===================== EXECUCAO DA APLICACAO =====================

def run_app(python_exe: Path, script: str) -> int:
    """Executa o script principal do projeto com o Python embutido."""
    root = app_root_dir()
    target = root / script
    if not target.exists():
        raise RuntimeError(f"Script {script!r} nao encontrado em {root!r}")
    print(f"[install_python] Iniciando aplicacao: {target.name}")
    return subprocess.call([str(python_exe), str(target)], cwd=str(root))

# ===================== HELPER GERAL =====================

def get_embedded_python() -> Optional[Path]:
    runtime_dir = get_runtime_dir()
    python_dir = runtime_dir / "python"
    if not python_dir.exists(): return None
    try:
        return find_python_exe(python_dir)
    except:
        return None

# ===================== FLUXO PRINCIPAL =====================

def install_python_flow(py_name: str = "winPython_3.13") -> bool:
    clear_last_error()
    try:
        runtime_dir = get_runtime_dir()
        python_dir = runtime_dir / "python"
        runtime_dir.mkdir(parents=True, exist_ok=True)

# Reaproveita o runtime somente quando ele corresponde ao flavor solicitado.
        # Se nao houver marcador de flavor, assume que o runtime existente e valido (nao apaga).
        flavor_file = runtime_dir / ".runtime-flavor"
        current_flavor = flavor_file.read_text(encoding="utf-8").strip() if flavor_file.exists() else ""
        if (
            python_dir.exists()
            and current_flavor
            and "winpython" in py_name.lower()
            and current_flavor != py_name
        ):
            print("[install_python] Migrando o runtime existente para WinPython...")
            shutil.rmtree(python_dir)
            requirements_marker = runtime_dir / ".requirements-installed"
            if requirements_marker.exists():
                requirements_marker.unlink()

        if python_dir.exists():
            try:
                py_exe = find_python_exe(python_dir)
                if "winpython" not in py_name.lower():
                    patch_python_pth(py_exe)
                    ensure_pip_and_tools(py_exe)
                flavor_file.write_text(py_name, encoding="utf-8")
                return True
            except Exception:
                pass
        # 1. Obter URL
        url = load_py_url(py_name)
        is_winpython = "winpython" in py_name.lower() or "winpython" in url.lower()

        # 2. Download
        tmp_zip = runtime_dir / "python_download.zip"
        print(f"[install_python] Baixando {py_name}...")
        download_file(url, tmp_zip)

        # 3. ExtraÃ§Ã£o
        if is_winpython:
            # LÃ³gica especial WinPython: Extrai, acha subpasta, move, ignora pip install
            extract_winpython_logic(tmp_zip, python_dir)
            try: tmp_zip.unlink() 
            except: pass
            
            print("[install_python] WinPython configurado. Pulando instalaÃ§Ã£o manual do pip (jÃ¡ incluÃ­do).")
            flavor_file.write_text(py_name, encoding="utf-8")
            # ValidaÃ§Ã£o final
            if not get_embedded_python():
                raise RuntimeError("WinPython extraÃ­do, mas executÃ¡vel nÃ£o encontrado.")
            return True

        else:
            # LÃ³gica PadrÃ£o (Embed)
            print("[install_python] Extraindo Python Embed...")
            extract_zip(tmp_zip, python_dir)
            try: tmp_zip.unlink() 
            except: pass

            python_exe = find_python_exe(python_dir)
            print("[install_python] Configurando ambiente (pip, setuptools)...")
            patch_python_pth(python_exe)
            ensure_pip_and_tools(python_exe)
            flavor_file.write_text(py_name, encoding="utf-8")
            return True

    except Exception as e:
        set_last_error(str(e))
        return False

# ===================== CLI =====================

def main(argv: Optional[list[str]] = None) -> int:
    if argv is None:
        argv = sys.argv[1:]

    # Flags: --requirements (instala requirements.txt) e --run <script> (inicia o projeto)
    req = False
    run_script: Optional[str] = None
    positional = []
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg in ("--requirements", "-r"):
            req = True
        elif arg == "--run":
            i += 1
            if i >= len(argv):
                print("ERRO: --run requer um script (ex: --run check_falhas.py)", file=sys.stderr)
                return 2
            run_script = argv[i]
        elif arg.startswith("-"):
            print(f"ERRO: opcao desconhecida {arg!r}", file=sys.stderr)
            return 2
        else:
            positional.append(arg)
        i += 1

    # Se nÃ£o passar argumento, tenta o padrÃ£o.
    # Se quiser testar o winpython, use: python install_python.py winPython_3.13
    py_name = positional[0] if positional else "winPython_3.13"

    if not install_python_flow(py_name):
        print(f"ERRO: {get_last_error()}", file=sys.stderr)
        return 2

    py_emb = get_embedded_python()
    if py_emb is None:
        print("ERRO: Python embutido nao encontrado em bin/runtime/python.", file=sys.stderr)
        return 2

    if req and not install_requirements(py_emb):
        print(f"ERRO: {get_last_error()}", file=sys.stderr)
        return 2

    print(f"[install_python] SUCESSO. Python em: {py_emb}")

    if run_script:
        try:
            return run_app(py_emb, run_script)
        except Exception as e:
            print(f"ERRO: {e}", file=sys.stderr)
            return 2
    return 0

if __name__ == "__main__":
    raise SystemExit(main())

