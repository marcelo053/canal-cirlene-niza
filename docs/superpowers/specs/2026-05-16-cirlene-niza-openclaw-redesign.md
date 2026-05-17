# Canal Cirlene Niza — OpenClaw Redesign Spec

**Date:** 2026-05-16  
**Status:** Approved  
**Replaces:** Python/crewAI local project (phases 1-2 kept as reference only)

---

## 1. Context & Goal

Build Canal Cirlene Niza content pipeline entirely within the VPS OpenClaw agent system — no n8n, no Python crewAI. The system creates, produces, posts, and monitors short-form content (45-60s) across TikTok, YouTube Shorts, and Instagram, using Cirlene's cloned voice and AI avatar.

**Core value:** One command → script → Cirlene's voice + avatar → approved → published on 3 platforms.

**Constraint:** FEM project (`main` agent, port 18789) remains completely untouched.

---

## 2. Architecture

### VPS Topology

```
VPS 186.202.209.88
├── OpenClaw :18789  (main — FEM)     ← untouched
└── OpenClaw :18790  (cirlene — NEW)  ← this project

Shared infrastructure (no changes):
├── Kokoro TTS      :8880
├── MinIO           :9000
├── Baserow         :85
└── Postiz                            ← already configured via larry

New web apps:
├── Streamlit :8503  → Aprovação Cirlene
└── Streamlit :8504  → Dashboard unificado (FEM tab + Cirlene tab)
```

### OpenClaw Cirlene Profile

- **Primary LLM:** MiniMax M2.7 (same as FEM — no new API key)
- **Secondary LLM:** Claude Sonnet 4.6 (orchestration decisions)
- **Port:** 18790
- **Skills installed:** see Section 4

---

## 3. Agent Team

8 agents orchestrated via `agent-team-orchestration`:

```
DIRETOR (orchestrator)
├── Roteirista   → script generation
├── Narrador     → voice cloning
├── Avatar       → talking head + static assets
├── Criativo     → scene images + thumbnails + carousel
├── Montador     → video assembly
├── Publicador   → multi-platform posting
└── Analista     → metrics + alerts
```

### Agent Definitions

| Agent | Role | Primary Skills | Output |
|---|---|---|---|
| **Diretor** | Orchestrator — routes tasks, tracks Baserow state, enforces gates | agent-team-orchestration, Claude Sonnet | Task routing |
| **Roteirista** | Generates pt-BR script in Cirlene's brand voice | brand-voice-profile, MiniMax M2.7 | Script 60s, 4-6 scenes, image prompt per scene |
| **Narrador** | Clones and synthesizes Cirlene's voice | clonev (Coqui XTTS v2, local) | WAV/MP3 → MinIO `cirlene-audio/` |
| **Avatar** | Creates talking head video + static avatars | heygen-avatar-lite, ai-avatar-generation | MP4 talking head, PNG avatares → MinIO `cirlene-avatar/` |
| **Criativo** | Generates scene images, thumbnails, carousel slides | evolink-media | JPEG/PNG → MinIO `cirlene-arts/` |
| **Montador** | Assembles final 9:16 video | ffmpeg-master | MP4 1080×1920 → MinIO `cirlene-final/` |
| **Publicador** | Posts to 3 platforms simultaneously | postiz, instagram-api | Post IDs/URLs → Baserow `social_posts_cirlene` |
| **Analista** | Polls metrics, fires alerts | Postiz analytics | Metrics → Baserow, alerts → Telegram |

### Two Video Modes

Diretor selects mode based on content type:

| Mode | When | Pipeline |
|---|---|---|
| **AVATAR** | Tips, opinions, personal delivery | Roteirista → Narrador → Avatar (HeyGen lip-sync) → Montador |
| **CENAS** | Recipes, tutorials, visual content | Roteirista → Narrador + Criativo (evolink scenes) → Montador |

---

## 4. Skills Stack

### New Skills to Install (cirlene profile)

```bash
clawhub install clonev               # voice cloning — Coqui XTTS v2, local
clawhub install heygen-avatar-lite   # talking head avatar video
clawhub install ai-avatar-generation # static avatars — each::sense
clawhub install brand-voice-profile  # Cirlene persona storage
clawhub install postiz               # multi-platform publishing (28+)
clawhub install instagram-api        # Meta Graph API — Reels + Carousel direct
clawhub install ffmpeg-master        # FFmpeg from natural language
```

### Skills Already on VPS (carry over)

```
evolink-media        # image + video generation (60+ models)
agent-team-orchestration
agent-commons
```

### Brand Voice Profile — Cirlene Niza

Stored in `brand-voice-profile` on first setup:

- **Persona:** Nutricionista acolhedora, prática, motivacional
- **Tom:** Feminino, próximo, sem jargão técnico excessivo
- **Nicho:** Nutrição e saúde, público geral
- **Formato:** 60s max, 4-6 cenas, gancho forte nos primeiros 3s
- **Plataformas:** TikTok (primário), YouTube Shorts, Instagram Reels

---

## 5. Data Layer

### Baserow Tables (database 175, suffix `_cirlene`)

| Table | Fields | Purpose |
|---|---|---|
| `productions_cirlene` | id, title, theme, mode(avatar\|cenas), status, approval_status, created_at, cost_usd | Production lifecycle |
| `scenes_cirlene` | id, production_id, order, script_text, image_prompt, audio_url, image_url, duration_s | Per-scene assets |
| `social_posts_cirlene` | id, production_id, platform, post_id, post_url, published_at | Published content |
| `metrics_cirlene` | id, post_id, platform, views, likes, shares, collected_at | Analytics |
| `costs_cirlene` | id, production_id, step, provider, cost_usd, tokens, created_at | Cost tracking |

### MinIO Buckets (prefix `cirlene-`)

```
cirlene-audio/    {production_id}/{scene_id}.mp3
cirlene-arts/     {production_id}/scene_{n}.jpg + thumbnail.jpg + carousel_{n}.png
cirlene-avatar/   {production_id}/talking_head.mp4 + profile.png
cirlene-final/    {production_id}/final.mp4
```

---

## 6. Approval Flow

```
GATE 1 — Script
  Roteirista done → Diretor → Telegram alert → link Streamlit 8503
  Operador: Aprovar / Revisar script
  Timeout: 48h alert, 72h auto-approve

GATE 2 — Assets (avatar + artes)
  Avatar + Criativo done → Streamlit 8503 shows preview gallery
  Operador: Aprovar artes / Revisar
  Timeout: 48h alert, 72h auto-approve

GATE 3 — Final Video → Publish
  Montador done → Streamlit 8503 shows video player
  Operador: PUBLICAR → triggers Publicador
  No auto-approve on this gate
```

---

## 7. Publishing Flow (Publicador)

```
Postiz API call → simultaneous:
  ├── TikTok (caption + hashtags nutrição)
  ├── YouTube Shorts (title + description + tags)
  └── Instagram Reels (caption + first comment hashtags)

instagram-api separate call:
  └── Instagram Carousel (5-8 slides PNG 1080×1080)

All URLs + post IDs → Baserow social_posts_cirlene
Telegram notification: "✅ Publicado! [links]"
```

---

## 8. Dashboard (Streamlit 8504)

Single app, two tabs:

**Tab "Cirlene Niza"**
- Kanban: productions by status (pending_script → published)
- Calendar: posts by platform by day
- Metrics card: views + likes last 7d (Postiz analytics)
- Budget: total cost this month (Baserow costs_cirlene)
- Quick action: "Nova produção" → input theme + mode → triggers Diretor

**Tab "FEM"**
- Reads from FEM Baserow tables (database 175, no suffix)
- Read-only — no actions, no agent calls
- Status only: recent productions, latest metrics

---

## 9. Implementation Phases

| Phase | Goal | Key Deliverables |
|---|---|---|
| **1** | Setup `cirlene` profile + infra | OpenClaw :18790, Baserow tables, MinIO buckets, brand-voice-profile onboarding, clonev voice clone setup |
| **2** | Voice + Avatar pipeline | Narrador (clonev), Avatar (HeyGen + ai-avatar), first talking head test |
| **3** | Visual + Assembly pipeline | Criativo (evolink), Montador (ffmpeg), both video modes working E2E |
| **4** | Approval + Publishing | Streamlit 8503, 3 gates, Postiz + instagram-api, Gate 3 → publish flow |
| **5** | Dashboard + Monitoring | Streamlit 8504 (both tabs), Analista polling, Telegram alerts |

---

## 10. Constraints

- **RAM:** VPS 4GB total, 1.5GB available — cirlene profile target <300MB steady-state
- **HeyGen:** Paid API — verify account/quota before Phase 2
- **clonev:** Needs ~5min audio sample of Cirlene's voice for quality clone
- **evolink-media:** Confirm EVOLINK_API_KEY available on VPS before Phase 3
- **Postiz:** Verify TikTok, YouTube, Instagram accounts connected in Postiz dashboard before Phase 4
- **FEM isolation:** cirlene profile must never call FEM agent or modify FEM Baserow tables

---

## 11. Success Criteria (v1.0)

1. Theme input → published on TikTok + YouTube Shorts + Instagram Reels within 2h (excluding approval time)
2. Avatar video: Cirlene's voice and face recognizable, lip-sync quality acceptable
3. All 3 gates operational — no content published without human approval
4. Dashboard shows real metrics 24h after publication
5. FEM project untouched and operational throughout
