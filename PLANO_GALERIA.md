# Plano - Galeria + Pipeline Interativo (dubbr v1.1)

## Objetivo
Permitir que o usuario gerencie midias (audio/video) em uma Galeria, assista originais/dublados, e dispare a dublagem a partir de um card, com painel HTML de pipeline/preset/status/progresso e botao "Start Dublagem".

## Estrutura de abas (Trabalho > Modo C)
1. Arquivo local  -> upload drag-and-drop ou clique (ja existe)
2. Baixar do YouTube -> so download (ja existe)
3. Galeria -> sub-abas:
   - Audio: cards dos audios adicionados (originais + dublados)
   - Video: cards dos videos (originais + dublados + baixados do YT)

## Card (Video)
- Thumbnail (frame) + titulo + duracao + status (original/dublado)
- Botoes:
  - Assistir original (player)
  - Assistir dublado (se existir)
  - Dublar (seleciona o video e abre painel pipeline)
- Ao clicar "Dublar": carrega o video no pipeline, exibe painel HTML com:
  - Preset (leve/equilibrado/maximo/custom)
  - Override por estagio (ASR/SER/Traducao/TTS)
  - Toggle revisar traducao
  - Status por estagio M1-M7 (aguardando/rodando/ok/fallback/erro)
  - Barra de progresso geral + por segmento
  - Pico VRAM / tempo decorrido
  - Botao "Start Dublagem"
- Ao final: exibe video dublado no player.

## Card (Audio)
- Mesma ideia, mas saida em audio (sem video).

## Backend
- JobManager + ProgressBus (ja existem) publicam eventos (estagio, pct, msg).
- UI consome via gr.Timer (1s) e atualiza painel HTML.
- Pipeline orchestrator (stub) a ser integrado.

## Armazenamento
- Originais: youtube_download/, saidas/, uploads/
- Dublados: saidas/<job_id>/dublado.mp4 (ou .wav)
- Indice: saidas/galeria.json (lista de itens com id, tipo, path_original, path_dublado, status)

## Implementacao incremental
1. (feito) Download YT com resolucao.
2. (proximo) Galeria listando arquivos de youtube_download + saidas.
3. Cards HTML + botoes.
4. Painel pipeline HTML + Start Dublagem.
5. Integracao com orchestrator real.
