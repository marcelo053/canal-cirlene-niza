# Canal Cirlene Niza — Automação de Conteúdo Short-Form

## What This Is

Pipeline de automação de conteúdo para o canal da influencer **Cirlene Niza**, especialista em nutrição e saúde. O sistema produz automaticamente vídeos curtos (45-60s) e posts para TikTok, YouTube Shorts e Instagram (Reels + Carrossel), com 3 gates de aprovação humana antes da publicação.

Roda na mesma VPS do OpenClaw (186.202.209.88), reutilizando infraestrutura existente (n8n, Baserow, MinIO, Kokoro TTS, fal.ai), mas como projeto independente com codebase própria.

## Core Value

**Produção → Aprovação → Publicação automatizada** de conteúdo de nutrição e saúde em 3 plataformas (TikTok, YouTube Shorts, Instagram), com controle humano em cada etapa.

## Context

- **Influencer**: Cirlene Niza
- **Nicho**: Nutrição e saúde
- **VPS**: 186.202.209.88 (compartilhada com OpenClaw FEM)
- **Padrão de nomenclatura**: sufixo `-cirl` em todos workflows e tabelas
- **Referência técnica**: OpenClaw Redesign (Documents/Brain/Openclaw Redesign/)

## Formats

| Formato | Especificação |
|---------|--------------|
| TikTok | Vertical 9:16 (1080×1920), 45-60s |
| YouTube Shorts | Vertical 9:16 (1080×1920), max 60s |
| Instagram Reels | Vertical 9:16 (1080×1920), 45-60s |
| Instagram Posts | Carrossel PNG, nutrição/dicas |

## Requirements

### Validated

(Nenhum ainda — projeto novo)

### Active

- [ ] **PIPE-01**: Sistema gera roteiro de nutrição de 60s a partir de tema
- [ ] **PIPE-02**: Roteiro dividido em 4-6 cenas com narração e prompt de imagem
- [ ] **PIPE-03**: TTS em voz feminina pt-BR via Kokoro
- [ ] **PIPE-04**: Geração de imagem por cena via fal.ai (estética saúde/nutrição)
- [ ] **PIPE-05**: Montagem vertical 9:16 com ffmpeg (max 60s)
- [ ] **PIPE-06**: Geração de carrossel de imagens para Instagram
- [ ] **APROV-01**: Gate 1 — aprovação de roteiro via Telegram (approve/revise)
- [ ] **APROV-02**: Gate 2 — aprovação de artes via Streamlit UI (galeria de imagens)
- [ ] **APROV-03**: Gate 3 — aprovação de vídeo via Streamlit UI (preview + publicar)
- [ ] **APROV-04**: Timeout 48h → alerta Telegram, 72h → auto-approve
- [ ] **PUB-01**: Publicar no YouTube Shorts via YouTube Data API v3
- [ ] **PUB-02**: Publicar no TikTok via Content Posting API
- [ ] **PUB-03**: Publicar no Instagram Reels + Posts via Meta Graph API
- [ ] **PUB-04**: Registro de posts publicados em Baserow (social_posts_cirlene)
- [ ] **INFRA-01**: Tabelas Baserow para produções, cenas, custos, eventos, posts
- [ ] **INFRA-02**: Buckets MinIO para áudio, artes, vídeo, final
- [ ] **INFRA-03**: Telegram bot exclusivo do canal (@CirleneNizaBot)
- [ ] **INFRA-04**: Credenciais de API: YouTube, TikTok, Meta Graph
- [ ] **MON-01**: Dashboard Streamlit com calendário e status de produções
- [ ] **MON-02**: Rastreamento de métricas básicas (views, likes via API)
- [ ] **MON-03**: Alertas de budget via Telegram

### Out of Scope

- Upload manual / intervenção humana na edição — todo fluxo é automatizado pós-aprovação
- Long-form YouTube (canal foca em short-form)
- Analytics avançados (v2+)
- Multi-language (apenas pt-BR)
- Agendamento de posts (v2+ — publicação imediata após aprovação)

## Key Decisions

| Decisão | Rationale | Outcome |
|---------|-----------|---------|
| Projeto independente (não fork do OpenClaw) | Evita acoplamento; OpenClaw FEM continua evoluindo separadamente | Codebase própria em Canal-Cirlene-Niza/ |
| Mesma VPS | Infraestrutura já existe e está operacional | Reusa n8n, Baserow, MinIO, Kokoro, fal.ai |
| Sufixo -cirl | Padrão OpenClaw (-fem) aplicado ao novo canal | Evita colisão de nomes em n8n e Baserow |
| 3 gates de aprovação | Controle humano: script → artes → vídeo | Nenhum conteúdo publicado sem aprovação |
| Short-form only | Cirlene foca em TikTok/Reels/Shorts | Vídeos 45-60s, 4-6 cenas max |

## Evolution

Este documento evolui a cada transição de fase.

**Após cada fase:** Mover requirements para Validated quando entregues.

---
*Last updated: 2026-05-15 após inicialização*
