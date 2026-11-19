# dubbr — Dublagem automática EN→PT-BR

**dubbr** é uma ferramenta para **Windows 11** que realiza **dublagem automática de vídeos/áudios do inglês para português brasileiro (pt-BR)**, com **Web UI (Gradio)**, gerenciador de modelos e quantização configurável. Tudo roda **100% local**, sem enviar dados para a nuvem.

- **Versão atual:** `1.1.0` (branch `main`)
- **Compatibilidade alvo:** Windows 11 + Python 3.11/3.12 (GPU NVIDIA Turing+ recomendada)
- **Licença:** Apache-2.0 (modelos com licenças próprias; ver catálogo)
- **Repositório:** https://github.com/iagobusca/video_audio_to_dublado

---

## Demonstração

A interface Gradio (`http://127.0.0.1:7860`) oferece 4 abas:

- **Trabalho** — 3 modos: A (clonar voz + texto), B (texto→áudio) e C (dublagem de vídeo/áudio).
- **Modelos** — download/apagar modelos por função (Extrair texto / Tradução / Áudio-Texto dublado) e quantização.
- **Jobs** — histórico, retomar/cancelar, fila GPU.
- **Config** — orçamento de VRAM, caminhos, glossário.

---

## Sobre o Projeto

O `dubbr` orquestra um pipeline de 7 estágios (M1–M7) para dublar vídeos/áudios:

1. **M1 Ingestão** — normaliza entrada (arquivo ou URL do YouTube) para WAV 16 kHz.
2. **M2 Separação** — separa vocal/instrumental (Demucs).
3. **M3 ASR** — transcrição com timestamps (Parakeet GGUF / faster-whisper).
4. **M4 SER** — análise de emoção (audeering) + banco de referências + `ref_text`.
5. **M5 Tradução** — EN→PT-BR (LFM3-Omni GGUF) com glossário.
6. **M6 TTS** — síntese com trio pt-BR selecionável (Qwen3-TTS / Chatterbox pt-br / F5-TTS pt-br).
7. **M7 Mux** — montagem final do vídeo/áudio dublado (ffmpeg).

### Modelos suportados (catálogo selecionável)

| Modelo | Papel | Licença | Destaque |
| --- | --- | --- | --- |
| Qwen3-TTS-1.7B-Base (GGUF) ★ padrão | TTS | Apache-2.0 | cloning em 3 s + `ref_text` |
| Qwen3-TTS-0.6B-Base (GGUF) | TTS | Apache-2.0 | variante econômica |
| Chatterbox pt-br (pack) | TTS | MIT | controle fino de emoção (exaggeration) |
| F5-TTS pt-br | TTS | CC-BY-NC-4.0 | treinado em pt-BR (~330 h) |
| LFM3-Omni-2B (GGUF) | Tradução | Apache-2.0 | LLM multimodal |
| Parakeet v3 (GGUF) | ASR | CC-BY-4.0 | timestamps |
| audeering wav2vec2 (dim) | SER | Apache-2.0 | arousal/valence |
| Demucs (htdemucs-ft) | Separação | MIT | vocal/instrumental |

### Arquitetura de processos (Windows)

Cada worker (torch) roda em processo/venv isolado e é encerrado ao fim do estágio → VRAM 100% liberada. Binários GGUF (llama.cpp/parakeet.cpp/qwentts.cpp) ficam em `bin/`, gerenciados pela aba Modelos. IPC via HTTP localhost + artefatos em disco.

### Presets (pico de VRAM, sequencial)

| Preset | ASR | SER | Tradução | TTS | Pico |
| --- | --- | --- | --- | --- | --- |
| leve | GGUF Q4 | CPU | Omni Q4_K_M | Qwen3 0.6B Q4 | ≈2,5 GB |
| equilibrado ★ | GGUF Q8 | fp16 | Omni Q8_0 | Qwen3 1.7B Q8_0 | ≈3 GB |
| máximo | GGUF Q8 | fp32 | Omni F16 | Qwen3 BF16 / Chatterbox fp32 | ≈5 GB |

---

## Como Instalar

### Pré-requisitos

- Windows 11
- Python 3.11 e 3.12 (`winget install Python.Python.3.11 Python.Python.3.12`)
- ffmpeg no PATH (`winget install Gyan.FFmpeg`)
- Git

### Setup

```powershell
git clone https://github.com/iagobusca/video_audio_to_dublado.git
cd video_audio_to_dublado
.\setup.ps1
```

O `setup.ps1` cria o venv principal, instala dependências e configura `HF_HOME`.

### Instalar o Python embutido (opcional)

Se preferir o runtime embutido em `bin/runtime/python`:

```bat
start.bat
```

### Iniciar a UI

```bat
iniciar.bat
```

Acesse `http://127.0.0.1:7860`.

---

## Uso Rápido

1. Aba **Modelos** → baixe os modelos necessários (ex.: Qwen3 1.7B Q8_0, Parakeet Q8_0, LFM3 Omni Q4_K_M).
2. Aba **Trabalho**:
   - **Modo A** — clonar voz + texto (upload de referência de 3 s).
   - **Modo B** — texto→áudio (CustomVoice / VoiceDesign / Chatterbox).
   - **Modo C** — dublagem: arraste um vídeo/áudio ou baixe do YouTube (escolhendo a resolução) e clique em *Iniciar pipeline*.
3. Acompanhe o progresso por estágio/segmento e assista o resultado na UI.

---

## Estrutura do Repositório

```text
video_audio_to_dublado/
  README.md
  PLANO_GALERIA.md
  app.py
  catalogo.yaml
  glossario.yaml
  requirements.txt
  setup.ps1
  iniciar.bat
  start.bat
  src/dubbr/
    config.py
    catalog.py
    models_manager.py
    job_manager.py
    progress.py
    youtube.py
    workers/        # workers isolados (ser, sep, tts_*)
    pipeline/       # M1..M7 + orchestrator
    ui/             # abas Gradio
  bin/
    install_python.py
    py_list.json
```

---

## Limitações Declaradas

- Qwen3-TTS não tem checkpoint pt-BR dedicado — o sotaque BR vem da referência; validar no A/B.
- Base sem instruct: grito = referência exaltada + ganho + camada original.
- `qwentts.cpp` no Windows e GGUF do Chatterbox pt-br: validar build/qualidade (marcados como experimentais).
- F5-pt-br CC-BY-NC: aviso de licença na UI para uso comercial.
- Música com vocal, lip-sync e multi-falante automático: roadmap v1.2.

---

## Licença

Apache-2.0 para o código do projeto. Modelos possuem licenças próprias (ver `catalogo.yaml`). F5-TTS pt-br é CC-BY-NC-4.0 (uso não-comercial).
