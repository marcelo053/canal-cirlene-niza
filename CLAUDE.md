# Canal Cirlene Niza — Project Guide

## Project

Automação de conteúdo short-form para o canal da influencer Cirlene Niza (nutrição e saúde).
Pipeline: Tema → Roteiro → Narração → Imagens → Aprovação → Publicação (TikTok + YouTube Shorts + Instagram).

## VPS

- **Host**: 186.202.209.88
- **n8n**: http://186.202.209.88:5678
- **Baserow**: http://186.202.209.88:85
- **MinIO**: http://186.202.209.88:9000
- **Kokoro TTS**: http://kokoro-tts:8880 (interno na VPS)
- **Streamlit Aprovação CIRL**: http://186.202.209.88:8503
- **Streamlit Dashboard CIRL**: http://186.202.209.88:8504

## Naming Convention

- Workflows n8n: sufixo `-cirl` (ex: `orquestrador-cirl`, `narracao-cirl`)
- Tabelas Baserow: sufixo `_cirlene` (ex: `productions_cirlene`, `scenes_cirlene`)
- Buckets MinIO: prefixo `cirlene-` (ex: `cirlene-audio`, `cirlene-video`)
- Webhooks: `/webhook/*-cirl` (ex: `/webhook/producao-cirl`)

## Approval Status Flow

```
pending_script → approved_script → pending_arts → approved_arts → pending_video → approved_video → published
                → revise_script                  → revise_arts                  → revise_video
```

## Reference: OpenClaw Redesign

Reutilizar padrões do projeto OpenClaw FEM (Documents/Brain/Openclaw Redesign/):
- `src/openclaw/tools/baserow.py` — BaserowClient com numeric field IDs (NUNCA usar display names)
- `src/openclaw/tools/minio.py` — Upload/download pattern
- `src/openclaw/platform/aprovacao.py` — Template Streamlit approval UI
- `src/openclaw/platform/timeout_checker.py` — Lógica 48h/72h auto-approve
- `systemd/` — Templates de services/timer

## GSD Workflow

```
/gsd:plan-phase N   → planeja fase N
/gsd:execute-phase N → executa fase N
/gsd:progress       → estado atual
```

## Critical Rules (herdadas do OpenClaw)

1. Baserow: SEMPRE usar numeric field IDs (field_XXXX), NUNCA display names
2. Workflows n8n: `continueOnFail: true` em chamadas HTTP para resiliência por cena
3. Approval gates: NUNCA pular gates, mesmo em modo YOLO
4. Budget check antes de criar cada produção
5. MinIO URLs: sempre construir como `minio://{bucket}/{path}`, resolver em presigned URL na exibição
