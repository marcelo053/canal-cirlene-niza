# Requirements — Canal Cirlene Niza

## v1 Requirements

### INFRA — Infraestrutura & Credenciais

- [ ] **INFRA-01**: Tabelas Baserow criadas (productions_cirlene, scenes_cirlene, costs_cirlene, run_events_cirlene, social_posts_cirlene)
- [ ] **INFRA-02**: Buckets MinIO criados (cirlene-audio, cirlene-video, cirlene-arts, cirlene-final)
- [ ] **INFRA-03**: Telegram bot exclusivo do canal criado e configurado
- [ ] **INFRA-04**: App YouTube Data API v3 registrado com OAuth 2.0 (escopo youtube.upload)
- [ ] **INFRA-05**: App TikTok for Developers registrado com Content Posting API aprovado
- [ ] **INFRA-06**: App Meta Graph API configurado com permissões instagram_content_publish
- [ ] **INFRA-07**: Variáveis de ambiente configuradas na VPS (/etc/cirlene/.env)

### PIPE — Pipeline de Conteúdo

- [ ] **PIPE-01**: Workflow `orquestrador-cirl` recebe tema via Telegram e cria production em Baserow
- [ ] **PIPE-02**: Workflow `roteirista-cirl` gera roteiro de nutrição 60s estruturado por cenas
- [ ] **PIPE-03**: Workflow `diretor-cena-cirl` divide roteiro em 4-6 cenas com rows em scenes_cirlene
- [ ] **PIPE-04**: Workflow `narracao-cirl` converte narração de cada cena em áudio via Kokoro TTS
- [ ] **PIPE-05**: Workflow `gerador-imagens-cirl` gera imagem por cena via fal.ai (estética saúde/nutrição)
- [ ] **PIPE-06**: Workflow `montagem-cirl` monta vídeo vertical 9:16 com ffmpeg (max 60s)
- [ ] **PIPE-07**: Workflow `gerador-carrossel-cirl` gera slides PNG de dicas para Instagram

### APROV — Aprovação

- [ ] **APROV-01**: Gate 1 — após Roteirista, enviar roteiro via Telegram com botões /aprovar_script e /revisar_script
- [ ] **APROV-02**: Gate 2 — após Gerador de Imagens, Streamlit :8503 exibe galeria com approve/revise por produção
- [ ] **APROV-03**: Gate 3 — após Montagem, Streamlit :8503 exibe preview de vídeo com botão publicar/revisar
- [ ] **APROV-04**: Timer systemd: 48h → alerta Telegram, 72h → auto-approve e avança pipeline
- [ ] **APROV-05**: Feedback de revisão armazenado em Baserow e passado de volta ao agente de origem

### PUB — Publicação Social

- [ ] **PUB-01**: Workflow `publicar-youtube-shorts` faz upload via YouTube Data API v3 (título, descrição, tags de nutrição)
- [ ] **PUB-02**: Workflow `publicar-tiktok` faz upload via TikTok Content Posting API
- [ ] **PUB-03**: Workflow `publicar-instagram` publica Reels via Media Container API (Meta Graph)
- [ ] **PUB-04**: Workflow `publicar-instagram` publica Carrossel via Carousel Container API
- [ ] **PUB-05**: Registro de post publicado em `social_posts_cirlene` (platform, post_id, url, published_at)
- [ ] **PUB-06**: Notificação Telegram após publicação com links de todos os posts

### MON — Monitoramento

- [ ] **MON-01**: Dashboard Streamlit :8504 com lista de produções, status e links publicados
- [ ] **MON-02**: Calendário visual de publicações por plataforma
- [ ] **MON-03**: Alerta de budget via Telegram quando custo mensal exceder limite configurado
- [ ] **MON-04**: Rastreamento de métricas básicas (views, likes) via polling de API após 24h

---

## v2 Requirements (Deferred)

- Agendamento de posts (publicar em horário pré-definido)
- Analytics avançados e relatórios semanais
- Multi-canal (outros influencers na mesma estrutura)
- Edição manual assistida de vídeo
- Thumbnail personalizada com rosto da Cirlene (IP-Adapter ou LoRA)

---

## Out of Scope

- Long-form YouTube — canal foca em short-form (45-60s)
- Publicação automática sem aprovação — 3 gates obrigatórios
- Idiomas além do pt-BR
- Integração com CRM ou e-commerce
- Publicação em Pinterest, Twitter/X, LinkedIn

---

## Traceability

| Phase | Requirements |
|-------|-------------|
| Phase 1 — Infra & Credenciais | INFRA-01 a INFRA-07 |
| Phase 2 — Pipeline de Conteúdo | PIPE-01 a PIPE-07 |
| Phase 3 — Workflow de Aprovação | APROV-01 a APROV-05 |
| Phase 4 — Montagem & Formatos | PIPE-06, PIPE-07 |
| Phase 5 — Publicação Social | PUB-01 a PUB-06 |
| Phase 6 — Dashboard & Monitoramento | MON-01 a MON-04 |
