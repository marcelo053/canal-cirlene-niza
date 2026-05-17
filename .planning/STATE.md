# Project State — Canal Cirlene Niza

## Current Position

- **Milestone**: v1.0 OpenClaw Pipeline
- **Phase**: 1 — Infra & Credenciais (in progress)
- **Status**: VPS infra done, aguardando HeyGen + Postiz + voz Cirlene
- **Last updated**: 2026-05-17

## Architecture

OpenClaw agent profile `cirlene` (port 18790) no VPS 186.202.209.88, isolado do FEM (port 18789).
8 agentes: Roteirista → Narrador (clonev) → Avatar (HeyGen) → Criativo (evolink) → Montador (ffmpeg) → Publicador (postiz) → Analista.
Aprovação via Streamlit :8503. Dashboard via Streamlit :8504.

## Phase 1 — Infra & Credenciais (2026-05-17)

| Task | Status | Notas |
|------|--------|-------|
| 1 — OpenClaw cirlene profile :18790 | ✅ Done | systemd openclaw-cirlene.service |
| 2 — Baserow 5 tabelas _cirlene | ✅ Done | DB 175, IDs no .env VPS |
| 3 — MinIO 4 buckets cirlene-* | ✅ Done | lifecycle 90d em audio+arts |
| 4 — Voz Cirlene (clonev sample) | ⏸ Blocked | Precisa URLs YouTube da Cirlene |
| 5 — 8 skills instaladas (clawhub) | ✅ Done | clonev, heygen-avatar-lite, evolink-image/media, postiz, etc |
| 6 — HeyGen API + avatar | ⏸ Blocked | Precisa conta HeyGen + foto Cirlene |
| 7 — Postiz social accounts | ⏸ Blocked | Precisa OAuth TikTok + YouTube + Instagram |
| 8 — Clone de voz (smoke test) | ⏸ Blocked | Depende task 4 |
| 9–13, 15 — Skills SKILL.md (7) | ✅ Done | identidade, roteiro, narrador, avatar, criativo, montador, publicacao |
| 14 — Streamlit Aprovação :8503 | ✅ Done | systemd cirlene-aprovacao.service |
| 17 — Streamlit Dashboard :8504 | ✅ Done | systemd cirlene-dashboard.service |
| 18 — Analista + systemd | ✅ Done | cirlene-analista skill + services enabled |
| 16, 19 — E2E tests | ⏸ Blocked | Depende tasks 4, 6, 7 |

## Context

- VPS: 186.202.209.88
- OpenClaw cirlene profile: `/root/.openclaw-cirlene/`
- Workspace: `/root/.openclaw-cirlene/workspace/canal-cirlene-niza/`
- .env VPS: `/root/.openclaw-cirlene/workspace/canal-cirlene-niza/.env`
- Baserow: DB 175, tabelas 720-725 (productions, scenes, posts, metrics, costs)
- MinIO buckets: cirlene-audio, cirlene-arts, cirlene-avatar, cirlene-final
- Streamlit aprovação: http://186.202.209.88:8503
- Streamlit dashboard: http://186.202.209.88:8504
- FEM isolado em :18789 (não tocado)

## Next Steps

1. Fornecer URLs YouTube Cirlene → Task 4 (voz)
2. Criar conta HeyGen + gerar avatar → Task 6
3. Conectar redes sociais no Postiz → Task 7
4. Após todas acima: Task 8 (smoke test voz) + Tasks 16/19 (E2E)
