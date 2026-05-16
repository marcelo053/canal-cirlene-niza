# Roadmap — Canal Cirlene Niza

**6 phases** | **23 requirements** | Milestone: v1.0 Pipeline Completo

---

## Phase Overview

| # | Phase | Goal | Requirements | Status |
|---|-------|------|--------------|--------|
| 1 | Infra & Credenciais | VPS pronta, APIs registradas, tabelas criadas | INFRA-01 a 07 | Not Started |
| 2 | Pipeline de Conteúdo | Roteiro → Narração → Imagens funcionando ponta-a-ponta | PIPE-01 a 05 | Not Started |
| 3 | Workflow de Aprovação | 3 gates operacionais com Telegram + Streamlit | APROV-01 a 05 | Not Started |
| 4 | Montagem & Formatos | Vídeo 9:16 e carrossel gerados corretamente | PIPE-06, PIPE-07 | Not Started |
| 5 | Publicação Social | Posts chegando nas 3 plataformas após aprovação | PUB-01 a 06 | Not Started |
| 6 | Dashboard & Monitoramento | Visibilidade completa de produções e publicações | MON-01 a 04 | Not Started |

---

## Phase 1 — Infra & Credenciais

**Goal**: VPS configurada com todas as dependências necessárias para o canal Cirlene Niza, sem interferir com o canal FEM existente.

**Requirements**: INFRA-01, INFRA-02, INFRA-03, INFRA-04, INFRA-05, INFRA-06, INFRA-07

**Success criteria**:
1. `curl http://186.202.209.88:85` retorna Baserow com tabelas productions_cirlene e scenes_cirlene visíveis
2. `mc ls minio/cirlene-audio` retorna bucket vazio (sem erro)
3. Telegram bot @CirleneNizaBot responde `/start`
4. YouTube OAuth flow completo — token salvo em /etc/cirlene/youtube_token.json
5. Meta Graph API retorna profile da conta Instagram da Cirlene via curl

**Plans**:
- 01-01: Criar tabelas Baserow + buckets MinIO
- 01-02: Registrar apps YouTube, TikTok, Meta Graph + OAuth flow
- 01-03: Criar Telegram bot + configurar variáveis de ambiente na VPS

**Dependencies**: Nenhuma (primeira fase)

---

## Phase 2 — Pipeline de Conteúdo

**Goal**: Dado um tema de nutrição, o sistema gera roteiro estruturado → divide em cenas → narra cada cena → gera imagem por cena.

**Requirements**: PIPE-01, PIPE-02, PIPE-03, PIPE-04, PIPE-05

**Success criteria**:
1. Comando `/produzir Benefícios da vitamina D` cria production em Baserow com status "pending_script"
2. Roteirista gera roteiro com 4-6 cenas em português, foco nutrição, duração total ≤60s de narração
3. Kokoro TTS gera áudio de cada cena e salva em `minio/cirlene-audio/{production_id}/{scene_id}.mp3`
4. fal.ai gera imagem estilo saúde/nutrição para cada cena e salva em `minio/cirlene-arts/{production_id}/{scene_id}.jpg`
5. Scenes_cirlene no Baserow tem audio_url e image_url preenchidos para todas as cenas

**Plans**:
- 02-01: Workflows orquestrador-cirl + roteirista-cirl
- 02-02: Workflows diretor-cena-cirl + narracao-cirl
- 02-03: Workflow gerador-imagens-cirl

**Dependencies**: Phase 1

---

## Phase 3 — Workflow de Aprovação

**Goal**: Operador aprova script, artes e vídeo antes de qualquer publicação. Timeouts automáticos evitam bloqueio indefinido.

**Requirements**: APROV-01, APROV-02, APROV-03, APROV-04, APROV-05

**Success criteria**:
1. Após roteiro gerado, Telegram envia mensagem com texto do script e botões /aprovar_script_{id} e /revisar_script_{id}
2. Streamlit :8503 carrega e lista produções em approval_status = "pending_arts"
3. Botão "Aprovar Artes" atualiza Baserow e avança para montagem
4. Botão "Aprovar Vídeo" dispara publicação nas 3 plataformas
5. Produção com 72h sem aprovação avança automaticamente (se budget OK)

**Plans**:
- 03-01: Gate 1 Script via Telegram bot
- 03-02: Streamlit aprovacao-cirl.py (:8503) com Gate 2 (Artes) e Gate 3 (Vídeo)
- 03-03: systemd timer timeout 48h/72h + systemd service aprovacao-cirl

**Dependencies**: Phase 2

---

## Phase 4 — Montagem & Formatos

**Goal**: Vídeo vertical 9:16 de 45-60s montado corretamente, mais slides de carrossel PNG para Instagram.

**Requirements**: PIPE-06, PIPE-07

**Success criteria**:
1. Vídeo montado em 1080×1920 com duração total entre 45s e 60s
2. Transições suaves entre cenas (fade 0.3s)
3. Narração sincronizada com imagem de cada cena
4. Carrossel: 5-8 slides PNG 1080×1080 com dica de nutrição por slide
5. Arquivos salvos em `minio/cirlene-video/{production_id}/final.mp4` e `minio/cirlene-arts/{production_id}/carousel_{n}.png`

**Plans**:
- 04-01: Workflow montagem-cirl (ffmpeg vertical)
- 04-02: Workflow gerador-carrossel-cirl (slides PNG)

**Dependencies**: Phase 3

---

## Phase 5 — Publicação Social

**Goal**: Após aprovação do vídeo, publicar automaticamente nas 3 plataformas com metadados de nutrição.

**Requirements**: PUB-01, PUB-02, PUB-03, PUB-04, PUB-05, PUB-06

**Success criteria**:
1. YouTube Shorts: vídeo publicado com título, descrição e tags de nutrição. URL retornada em social_posts_cirlene
2. TikTok: vídeo publicado com caption. post_id registrado no Baserow
3. Instagram Reels: Reel publicado via Media Container API. permalink registrado
4. Instagram Carrossel: post de carrossel publicado com legenda
5. Telegram notifica com todos os links após publicação completa

**Plans**:
- 05-01: Workflows publicar-youtube-shorts + publicar-tiktok
- 05-02: Workflow publicar-instagram (Reels + Carrossel)
- 05-03: Registro em social_posts_cirlene + notificação Telegram

**Dependencies**: Phase 4

---

## Phase 6 — Dashboard & Monitoramento

**Goal**: Visibilidade completa do pipeline de produções e posts publicados, com alertas de budget.

**Requirements**: MON-01, MON-02, MON-03, MON-04

**Success criteria**:
1. Dashboard :8504 lista todas produções com status, custo estimado e links publicados
2. Calendário visual mostra posts por plataforma por dia
3. Alerta Telegram disparado quando custo mensal > R$200 (ou valor configurado)
4. Após 24h de publicação, métricas (views, likes) coletadas e exibidas no dashboard

**Plans**:
- 06-01: Streamlit dashboard-cirl.py (:8504) com lista de produções e calendário
- 06-02: Coleta de métricas via API + alerta de budget

**Dependencies**: Phase 5

---

## Milestone: v1.0 Pipeline Completo

**Done when**: Produção ponta-a-ponta funciona — tema inserido via Telegram, 3 gates aprovados, publicado em TikTok + YouTube Shorts + Instagram Reels, métricas visíveis no dashboard.
