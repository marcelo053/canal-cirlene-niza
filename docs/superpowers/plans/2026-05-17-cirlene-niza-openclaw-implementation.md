# Canal Cirlene Niza — OpenClaw Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Deploy Canal Cirlene Niza as a standalone OpenClaw agent profile on the VPS, producing short-form content (45-60s) with Cirlene's cloned voice and AI avatar, published automatically to TikTok + YouTube Shorts + Instagram.

**Architecture:** Second OpenClaw profile (`cirlene`, port 18790) on VPS 186.202.209.88, isolated from FEM (`main`, port 18789). 8-agent team coordinated via `agent-team-orchestration`: Roteirista → Narrador (clonev) → Avatar (HeyGen) → Criativo (evolink) → Montador (ffmpeg) → Publicador (postiz + instagram-api) → Analista. Approval via Streamlit :8503. Dashboard via Streamlit :8504.

**Tech Stack:** OpenClaw 2026.4.9, MiniMax M2.7, Claude Sonnet 4.6, Coqui XTTS v2 (clonev), HeyGen API, Evolink API, Postiz API, Meta Graph API, Baserow REST API, MinIO (boto3/mc), FFmpeg, Streamlit, Python 3.11, systemd.

**Spec:** `Canal-Cirlene-Niza/docs/superpowers/specs/2026-05-16-cirlene-niza-openclaw-redesign.md`

---

## File Map

```
VPS /root/.openclaw/
├── agents/cirlene/                        ← new OpenClaw profile
│   └── agent/
│       ├── auth-profiles.json             ← API keys (minimax, anthropic, heygen, evolink)
│       ├── models.json                    ← MiniMax M2.7 + Claude Sonnet config
│       └── openclaw.json                  ← profile config (port 18790)
├── workspace/canal-cirlene-niza/
│   ├── .env                               ← all env vars (Baserow field IDs, API keys)
│   ├── voice/
│   │   └── cirlene_sample.wav             ← 5min voice reference for clonev
│   ├── skills/                            ← custom skills for cirlene profile
│   │   ├── cirlene-identidade/SKILL.md    ← persona + brand voice config
│   │   ├── cirlene-roteiro/SKILL.md       ← script generation rules
│   │   ├── cirlene-aprovacao/SKILL.md     ← approval gate flow
│   │   └── cirlene-publicacao/SKILL.md    ← Postiz + instagram-api flow
│   └── platform/
│       ├── aprovacao.py                   ← Streamlit :8503 (3 gates)
│       ├── dashboard.py                   ← Streamlit :8504 (2 tabs)
│       └── requirements.txt
└── workspace/skills/ (installed via clawhub)
    ├── clonev/
    ├── heygen-avatar-lite/
    ├── ai-avatar-generation/
    ├── brand-voice-profile/
    ├── postiz/
    ├── instagram-api/
    └── ffmpeg-master/

Local ~/Documents/Brain/Canal-Cirlene-Niza/
├── docs/superpowers/specs/2026-05-16-cirlene-niza-openclaw-redesign.md
└── docs/superpowers/plans/2026-05-17-cirlene-niza-openclaw-implementation.md  ← this file
```

---

## Phase 1 — Infrastructure Setup

### Task 1: Create `cirlene` OpenClaw profile on VPS

**Files:**
- Create: `/root/.openclaw/agents/cirlene/agent/openclaw.json`
- Create: `/root/.openclaw/agents/cirlene/agent/models.json`
- Create: `/root/.openclaw/agents/cirlene/agent/auth-profiles.json`

- [ ] **Step 1: SSH into VPS**

```bash
ssh vps
```

- [ ] **Step 2: Check OpenClaw CLI version and profile commands**

```bash
openclaw --version
openclaw agent --help
```

Expected: OpenClaw 2026.4.9, see list of agent subcommands

- [ ] **Step 3: Create cirlene agent profile**

```bash
openclaw agent create cirlene --port 18790
```

If that command doesn't exist, create manually:

```bash
mkdir -p /root/.openclaw/agents/cirlene/agent
cp /root/.openclaw/agents/main/agent/models.json /root/.openclaw/agents/cirlene/agent/
cp /root/.openclaw/agents/main/agent/auth-profiles.json /root/.openclaw/agents/cirlene/agent/
```

- [ ] **Step 4: Configure port in profile config**

```bash
cat > /root/.openclaw/agents/cirlene/agent/openclaw.json << 'EOF'
{
  "agent": {
    "name": "cirlene",
    "port": 18790,
    "channel": "webchat",
    "model": {
      "primary": "minimax/MiniMax-M2.7",
      "secondary": "anthropic/claude-sonnet-4-6"
    }
  }
}
EOF
```

- [ ] **Step 5: Start cirlene profile and verify it responds**

```bash
openclaw agent start cirlene
sleep 5
curl -s http://localhost:18790/health | grep -i ok
```

Expected: `{"status":"ok"}` or similar health response

- [ ] **Step 6: Verify FEM profile still running (isolation check)**

```bash
curl -s http://localhost:18789/health | grep -i ok
```

Expected: FEM still responds — profiles isolated

- [ ] **Step 7: Commit**

```bash
# On local machine — note the port in project memory
echo "cirlene OpenClaw profile running on VPS port 18790" >> /root/.openclaw/workspace/OPENCLAW-VPS-ARQUITETURA.md
```

---

### Task 2: Create Baserow tables (_cirlene suffix)

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/.env` (starts empty, fills here)

- [ ] **Step 1: Create workspace directory**

```bash
ssh vps
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza
touch /root/.openclaw/workspace/canal-cirlene-niza/.env
```

- [ ] **Step 2: Get Baserow auth token and database ID**

```bash
# Baserow runs on port 85. Get the token from FEM config
grep -i "baserow\|token" /root/.openclaw/agents/main/agent/auth-profiles.json
```

Note the `BASEROW_TOKEN` and database ID (should be 175 from FEM project).

- [ ] **Step 3: Create `productions_cirlene` table**

```bash
BASEROW_TOKEN="<token-from-step-2>"
DB_ID=175

curl -s -X POST "http://localhost:85/api/database/tables/database/${DB_ID}/" \
  -H "Authorization: Token ${BASEROW_TOKEN}" \
  -H "Content-Type: application/json" \
  -d '{"name": "productions_cirlene"}' | python3 -m json.tool
```

Note the `id` field in response → `PROD_TABLE_ID`

- [ ] **Step 4: Add fields to productions_cirlene**

```bash
PROD_TABLE_ID=<id-from-step-3>

# Add fields one by one
for field_def in \
  '{"name":"title","type":"text"}' \
  '{"name":"theme","type":"text"}' \
  '{"name":"mode","type":"single_select","select_options":[{"value":"avatar","color":"blue"},{"value":"cenas","color":"green"}]}' \
  '{"name":"status","type":"single_select","select_options":[{"value":"pending_script"},{"value":"pending_assets"},{"value":"pending_video"},{"value":"published"},{"value":"failed"}]}' \
  '{"name":"approval_status","type":"single_select","select_options":[{"value":"pending"},{"value":"approved"},{"value":"revise"},{"value":"rejected"}]}' \
  '{"name":"cost_usd","type":"number","number_decimal_places":4}' \
  '{"name":"final_video_url","type":"text"}'; do

  curl -s -X POST "http://localhost:85/api/database/fields/table/${PROD_TABLE_ID}/" \
    -H "Authorization: Token ${BASEROW_TOKEN}" \
    -H "Content-Type: application/json" \
    -d "$field_def" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d['name'], d['id'])"
done
```

Write all field IDs to `.env`:

```bash
# Example output from above: title 6900, theme 6901 ...
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
BASEROW_URL=http://localhost:85
BASEROW_TOKEN=<your-token>
PROD_TABLE_ID=<id>
FIELD_PROD_TITLE=<id>
FIELD_PROD_THEME=<id>
FIELD_PROD_MODE=<id>
FIELD_PROD_STATUS=<id>
FIELD_PROD_APPROVAL_STATUS=<id>
FIELD_PROD_COST_USD=<id>
FIELD_PROD_FINAL_URL=<id>
EOF
```

- [ ] **Step 5: Create `scenes_cirlene`, `social_posts_cirlene`, `metrics_cirlene`, `costs_cirlene` tables**

Repeat Step 3-4 pattern for each table. Fields per spec Section 5.

After each, add the table ID and all field IDs to `.env` with prefix `SCENES_`, `POSTS_`, `METRICS_`, `COSTS_`.

- [ ] **Step 6: Verify all tables visible in Baserow UI**

```bash
curl -s "http://localhost:85/api/database/tables/database/${DB_ID}/" \
  -H "Authorization: Token ${BASEROW_TOKEN}" | python3 -c "
import sys, json
tables = json.load(sys.stdin)
for t in tables: print(t['name'], t['id'])
" | grep cirlene
```

Expected output (5 tables with _cirlene suffix):
```
productions_cirlene <id>
scenes_cirlene <id>
social_posts_cirlene <id>
metrics_cirlene <id>
costs_cirlene <id>
```

- [ ] **Step 7: Commit env file template (no secrets)**

```bash
# On local machine
cat > /Users/studio/Documents/Brain/Canal-Cirlene-Niza/.env.example << 'EOF'
BASEROW_URL=http://localhost:85
BASEROW_TOKEN=
PROD_TABLE_ID=
FIELD_PROD_TITLE=
FIELD_PROD_THEME=
FIELD_PROD_MODE=
FIELD_PROD_STATUS=
FIELD_PROD_APPROVAL_STATUS=
FIELD_PROD_COST_USD=
SCENES_TABLE_ID=
FIELD_SCENE_PRODUCTION_ID=
FIELD_SCENE_ORDER=
FIELD_SCENE_SCRIPT_TEXT=
FIELD_SCENE_IMAGE_PROMPT=
FIELD_SCENE_AUDIO_URL=
FIELD_SCENE_IMAGE_URL=
FIELD_SCENE_DURATION_S=
POSTS_TABLE_ID=
FIELD_POST_PRODUCTION_ID=
FIELD_POST_PLATFORM=
FIELD_POST_POST_ID=
FIELD_POST_POST_URL=
FIELD_POST_PUBLISHED_AT=
METRICS_TABLE_ID=
FIELD_METRIC_POST_ID=
FIELD_METRIC_PLATFORM=
FIELD_METRIC_VIEWS=
FIELD_METRIC_LIKES=
FIELD_METRIC_SHARES=
COSTS_TABLE_ID=
FIELD_COST_PRODUCTION_ID=
FIELD_COST_STEP=
FIELD_COST_PROVIDER=
FIELD_COST_USD=
FIELD_COST_TOKENS=
EOF
```

---

### Task 3: Create MinIO buckets (cirlene-*)

- [ ] **Step 1: List existing buckets to confirm MinIO running**

```bash
ssh vps
mc ls minio/ 2>/dev/null || mc alias set minio http://localhost:9000 minioadmin minioadmin
mc ls minio/
```

Expected: see existing FEM buckets (`openclaw-work/`, `openclaw-final/`)

- [ ] **Step 2: Create all cirlene buckets**

```bash
for bucket in cirlene-audio cirlene-arts cirlene-avatar cirlene-final; do
  mc mb minio/${bucket} && echo "Created ${bucket}"
done
```

Expected:
```
Bucket created successfully `minio/cirlene-audio`.
Bucket created successfully `minio/cirlene-arts`.
Bucket created successfully `minio/cirlene-avatar`.
Bucket created successfully `minio/cirlene-final`.
```

- [ ] **Step 3: Set lifecycle policy (90-day auto-delete for cirlene-audio and cirlene-arts)**

```bash
cat > /tmp/lifecycle-cirlene.json << 'EOF'
{
  "Rules": [
    {
      "ID": "cirlene-90day-cleanup",
      "Status": "Enabled",
      "Expiration": {"Days": 90}
    }
  ]
}
EOF

mc ilm import minio/cirlene-audio < /tmp/lifecycle-cirlene.json
mc ilm import minio/cirlene-arts < /tmp/lifecycle-cirlene.json
```

- [ ] **Step 4: Verify all 4 buckets exist**

```bash
mc ls minio/ | grep cirlene
```

Expected: 4 lines with `cirlene-audio`, `cirlene-arts`, `cirlene-avatar`, `cirlene-final`

- [ ] **Step 5: Add MinIO config to .env**

```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
MINIO_ENDPOINT=http://localhost:9000
MINIO_ACCESS_KEY=minioadmin
MINIO_SECRET_KEY=minioadmin
MINIO_BUCKET_AUDIO=cirlene-audio
MINIO_BUCKET_ARTS=cirlene-arts
MINIO_BUCKET_AVATAR=cirlene-avatar
MINIO_BUCKET_FINAL=cirlene-final
EOF
```

---

### Task 4: Prepare Cirlene's voice sample for clonev

- [ ] **Step 1: Install yt-dlp on VPS if not present**

```bash
ssh vps
which yt-dlp || pip3 install yt-dlp
yt-dlp --version
```

- [ ] **Step 2: Extract audio from Cirlene's YouTube videos**

Ask Cirlene (or find) 2-3 existing videos where she speaks clearly. Then:

```bash
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/voice/raw

# Replace URLs with actual Cirlene Niza YouTube video URLs
yt-dlp -x --audio-format wav \
  -o "/root/.openclaw/workspace/canal-cirlene-niza/voice/raw/%(title)s.wav" \
  "https://www.youtube.com/watch?v=VIDEO_ID_1" \
  "https://www.youtube.com/watch?v=VIDEO_ID_2"
```

- [ ] **Step 3: Concatenate and normalize voice samples**

```bash
# List downloaded files
ls /root/.openclaw/workspace/canal-cirlene-niza/voice/raw/

# Concatenate into single reference file (ffmpeg)
ffmpeg -i "concat:$(ls /root/.openclaw/workspace/canal-cirlene-niza/voice/raw/*.wav | tr '\n' '|' | sed 's/|$//')" \
  -ac 1 -ar 22050 \
  /root/.openclaw/workspace/canal-cirlene-niza/voice/cirlene_sample.wav

# Verify duration (target: ≥5 minutes = 300 seconds)
ffprobe -i /root/.openclaw/workspace/canal-cirlene-niza/voice/cirlene_sample.wav \
  -show_entries format=duration -v quiet -of csv=p=0
```

Expected: number ≥ 300.0

- [ ] **Step 4: If no existing videos — record fresh sample**

Record Cirlene reading the following script (5 min continuous, natural pace, no music):

```
"Olá, eu sou a Cirlene Niza e hoje vamos falar sobre alimentação saudável.
Nutrição é a base de tudo na nossa vida. Quando a gente cuida do que come,
cuida da saúde, da energia e do bem-estar. Vamos começar com o café da manhã...
[continue com tópicos variados de nutrição por 5 minutos]"
```

Export as WAV, copy to VPS:
```bash
scp ~/cirlene_recording.wav vps:/root/.openclaw/workspace/canal-cirlene-niza/voice/cirlene_sample.wav
```

- [ ] **Step 5: Add voice path to .env**

```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
CIRLENE_VOICE_SAMPLE=/root/.openclaw/workspace/canal-cirlene-niza/voice/cirlene_sample.wav
EOF
```

---

### Task 5: Install skills on cirlene profile

- [ ] **Step 1: Switch to cirlene profile context on VPS**

```bash
ssh vps
export OPENCLAW_PROFILE=cirlene
# Or: openclaw profile use cirlene
```

- [ ] **Step 2: Install all 7 new skills**

```bash
clawhub install clonev
clawhub install heygen-avatar-lite
clawhub install ai-avatar-generation
clawhub install brand-voice-profile
clawhub install postiz
clawhub install instagram-api
clawhub install ffmpeg-master
```

- [ ] **Step 3: Verify skills installed**

```bash
ls /root/.openclaw/workspace/skills/ | sort
```

Expected output includes all 7 new skills plus existing `evolink-media`, `agent-team-orchestration`, `agent-commons`.

- [ ] **Step 4: Copy evolink-media to cirlene profile skills if needed**

```bash
# evolink-media is workspace-level, accessible to all profiles
ls /root/.openclaw/workspace/skills/evolink-media/SKILL.md && echo "OK"
```

---

### Task 6: Configure HeyGen API

- [ ] **Step 1: Create HeyGen account**

Go to https://app.heygen.com → Sign Up → Upgrade to API plan (check current pricing)

- [ ] **Step 2: Get API key**

HeyGen Dashboard → API → Generate Key → copy

- [ ] **Step 3: Create Cirlene's HeyGen avatar**

```bash
# Upload Cirlene's photo to HeyGen
# Option A: Use HeyGen UI (Avatars → Create → Photo Avatar)
# Option B: Use API
HEYGEN_API_KEY="<your-key>"

curl -s -X POST "https://upload.heygen.com/v1/photo_avatar" \
  -H "X-Api-Key: ${HEYGEN_API_KEY}" \
  -F "file=@/path/to/cirlene_photo.jpg" \
  -F "name=Cirlene Niza"
```

Note the `avatar_id` from response.

- [ ] **Step 4: Add HeyGen config to .env**

```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
HEYGEN_API_KEY=<your-heygen-api-key>
HEYGEN_AVATAR_ID=<avatar-id-from-step-3>
EOF
```

- [ ] **Step 5: Smoke test HeyGen — generate 5s test video**

```bash
HEYGEN_API_KEY=$(grep HEYGEN_API_KEY /root/.openclaw/workspace/canal-cirlene-niza/.env | cut -d= -f2)
AVATAR_ID=$(grep HEYGEN_AVATAR_ID /root/.openclaw/workspace/canal-cirlene-niza/.env | cut -d= -f2)

VIDEO_ID=$(curl -s -X POST "https://api.heygen.com/v2/video/generate" \
  -H "X-Api-Key: ${HEYGEN_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"video_inputs\":[{\"character\":{\"type\":\"avatar\",\"avatar_id\":\"${AVATAR_ID}\",\"avatar_style\":\"normal\"},\"voice\":{\"type\":\"text\",\"input_text\":\"Olá, eu sou a Cirlene Niza.\",\"voice_id\":\"pt-BR-FranciscaNeural\"}}],\"dimension\":{\"width\":1080,\"height\":1920}}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['video_id'])")

echo "Video ID: ${VIDEO_ID}"
```

- [ ] **Step 6: Poll until complete and download test video**

```bash
sleep 30
STATUS=$(curl -s "https://api.heygen.com/v1/video_status.get?video_id=${VIDEO_ID}" \
  -H "X-Api-Key: ${HEYGEN_API_KEY}" \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(d['status'], d.get('video_url',''))")
echo $STATUS
```

Expected: `completed https://...heygen.com/.../video.mp4`

---

### Task 7: Connect social accounts in Postiz

- [ ] **Step 1: Open Postiz dashboard**

```bash
# Postiz URL (check VPS - may be running locally or via cloud)
# If self-hosted on VPS, find the port:
ssh vps "docker ps | grep postiz"
```

Or access cloud Postiz at postiz.pro/dashboard

- [ ] **Step 2: Connect TikTok account**

Postiz dashboard → Channels → Add Channel → TikTok → OAuth flow → Authorize

Verify: TikTok channel shows as "Connected" in Postiz

- [ ] **Step 3: Connect YouTube account**

Postiz → Channels → Add Channel → YouTube → OAuth → Authorize (Cirlene's Google account)

Verify: YouTube channel shows connected

- [ ] **Step 4: Connect Instagram account**

Postiz → Channels → Add Channel → Instagram → Meta OAuth → Authorize (Cirlene's Instagram business account)

Note: Instagram requires a Business or Creator account connected to a Facebook Page.

- [ ] **Step 5: Get Postiz API key and channel IDs**

Postiz → Settings → API Key → Copy

Then get channel IDs:
```bash
POSTIZ_API_KEY="<your-postiz-key>"
curl -s "https://api.postiz.com/public/v1/integrations" \
  -H "Authorization: Bearer ${POSTIZ_API_KEY}" \
  | python3 -c "import sys,json; [print(i['name'], i['id']) for i in json.load(sys.stdin)['integrations']]"
```

- [ ] **Step 6: Add Postiz config to .env**

```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
POSTIZ_API_KEY=<your-postiz-api-key>
POSTIZ_TIKTOK_ID=<id-from-step-5>
POSTIZ_YOUTUBE_ID=<id-from-step-5>
POSTIZ_INSTAGRAM_ID=<id-from-step-5>
EOF
```

- [ ] **Step 7: Smoke test — post draft to Postiz (do not publish)**

```bash
curl -s -X POST "https://api.postiz.com/public/v1/posts" \
  -H "Authorization: Bearer ${POSTIZ_API_KEY}" \
  -H "Content-Type: application/json" \
  -d "{\"type\":\"draft\",\"content\":\"Teste Cirlene Niza\",\"integrations\":[\"${POSTIZ_TIKTOK_ID}\"]}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('id','FAILED'))"
```

Expected: a draft post ID (not "FAILED")

---

## Phase 2 — Voice + Avatar Pipeline

### Task 8: Clone Cirlene's voice with clonev

- [ ] **Step 1: Verify clonev skill is installed and read its docs**

```bash
ssh vps
cat /root/.openclaw/workspace/skills/clonev/SKILL.md | head -60
```

Note the clonev API endpoint and required parameters.

- [ ] **Step 2: Install Coqui XTTS v2 dependencies**

```bash
# clonev likely installs deps automatically, or:
pip3 install TTS torch torchaudio
# Verify
python3 -c "from TTS.api import TTS; print('TTS OK')"
```

- [ ] **Step 3: Generate first test with clonev using Cirlene's voice**

Ask the cirlene OpenClaw agent (via webchat at localhost:18790) to:
```
Use the clonev skill to generate speech from this text:
"Olá, eu sou a Cirlene Niza, nutricionista apaixonada por saúde e bem-estar."
Use the voice reference at: /root/.openclaw/workspace/canal-cirlene-niza/voice/cirlene_sample.wav
Save output to: /root/.openclaw/workspace/canal-cirlene-niza/voice/test_output.wav
```

- [ ] **Step 4: Listen and evaluate quality**

```bash
# Copy test output to local machine for listening
scp vps:/root/.openclaw/workspace/canal-cirlene-niza/voice/test_output.wav ~/Desktop/cirlene_test.wav
open ~/Desktop/cirlene_test.wav
```

If quality unacceptable: gather more voice samples (Task 4) and repeat.

- [ ] **Step 5: Add clonev config to .env**

```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
CLONEV_MODEL=xtts_v2
CLONEV_LANGUAGE=pt
CLONEV_VOICE_REF=/root/.openclaw/workspace/canal-cirlene-niza/voice/cirlene_sample.wav
CLONEV_OUTPUT_DIR=/root/.openclaw/workspace/canal-cirlene-niza/audio_tmp
EOF
```

---

### Task 9: Write `cirlene-identidade` and `cirlene-roteiro` skills

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-identidade/SKILL.md`
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-roteiro/SKILL.md`

- [ ] **Step 1: Create skills directory**

```bash
ssh vps
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-identidade
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-roteiro
```

- [ ] **Step 2: Write cirlene-identidade skill**

```bash
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-identidade/SKILL.md << 'SKILL'
---
name: cirlene-identidade
description: Cirlene Niza brand identity — persona, voice, visual guidelines. Load before generating any content for this channel.
---

# Cirlene Niza — Canal Identity

## Persona
Cirlene Niza é nutricionista especializada em nutrição prática para o dia a dia.
Tom: acolhedor, prático, motivacional. Próxima do público. Sem jargão técnico desnecessário.
Público: mulheres 25-45 anos, interessadas em saúde, bem-estar e nutrição acessível.

## Voice Guidelines (for Roteirista)
- Linguagem: português brasileiro, informal mas profissional
- Abertura: gancho nos primeiros 3 segundos ("Você sabia que...", "Esse erro está te impedindo de...")
- Estrutura: problema → solução → call-to-action
- Duração: 45-60 segundos de narração (≈120-150 palavras no ritmo natural)
- Cenas: 4-6 por vídeo, cada uma com 1 ideia clara
- Nunca usar: palavras em inglês sem necessidade, jargão médico, promessas exageradas

## Visual Guidelines (for Criativo)
- Estética: cores quentes (verde-limão, branco, coral), clean, natural
- Imagens: alimentos reais, pessoa saudável, cozinha acessível — sem filtros artificiais
- Texto on-screen: fonte clara, contraste alto, máximo 6 palavras por frame
- Formato: 9:16 vertical (1080×1920) para TikTok/Reels/Shorts

## Platform Tone
- TikTok: mais descontraída, trending hooks, hashtags nutrição/saúde
- YouTube Shorts: título descritivo, descrição com keywords nutrição
- Instagram: caption mais elaborada, primeiro comentário com hashtags

## Approval Status Flow
pending_script → approved_script → pending_assets → approved_assets → pending_video → published
SKILL
```

- [ ] **Step 3: Write cirlene-roteiro skill**

```bash
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-roteiro/SKILL.md << 'SKILL'
---
name: cirlene-roteiro
description: Generate a 45-60s short-form video script in Cirlene Niza's voice. Use after loading cirlene-identidade. Produces structured JSON with scenes for downstream agents.
---

# Roteirista — Cirlene Niza

## Always load cirlene-identidade before generating any script.

## Input
- theme: string (topic in pt-BR, e.g., "Benefícios da vitamina D")
- mode: "avatar" | "cenas" (avatar = talking head, cenas = scene images)

## Output Format
Return a JSON object:

```json
{
  "title": "título do vídeo (max 60 chars, SEO)",
  "hook": "primeiros 3 segundos — gancho forte",
  "total_duration_s": 55,
  "scenes": [
    {
      "order": 1,
      "narration": "texto da narração desta cena (max 30 palavras)",
      "duration_s": 10,
      "image_prompt": "prompt em inglês para geração de imagem (se mode=cenas)",
      "on_screen_text": "máx 6 palavras para exibir na tela"
    }
  ],
  "cta": "call-to-action final",
  "caption_tiktok": "legenda TikTok com emojis e 3 hashtags",
  "caption_youtube": "título YouTube Shorts + descrição 2 linhas",
  "caption_instagram": "legenda Instagram Reels + primeiros comentário hashtags"
}
```

## Rules
1. total scenes: 4-6
2. sum of duration_s ≤ 60
3. narration per scene ≤ 30 words (spoken in ≤ 12s at natural pace)
4. image_prompt: in English, describe the visual — e.g., "fresh colorful vegetables on white kitchen counter, natural lighting, top-down view"
5. hook must create curiosity or urgency in the first 3 seconds
6. Never fabricate health claims not supported by mainstream nutrition science
SKILL
```

- [ ] **Step 4: Register custom skills with cirlene profile**

```bash
# Link custom skills into the cirlene profile skills directory
ln -s /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-identidade \
      /root/.openclaw/workspace/skills/cirlene-identidade
ln -s /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-roteiro \
      /root/.openclaw/workspace/skills/cirlene-roteiro
```

- [ ] **Step 5: Test script generation via cirlene agent**

Open chat at `http://localhost:18790` and send:
```
Load cirlene-identidade and cirlene-roteiro skills.
Generate a script for theme: "5 alimentos que aceleram o metabolismo"
Mode: cenas
Return the JSON.
```

Expected: valid JSON with 4-6 scenes, total_duration_s ≤ 60, all fields present.

- [ ] **Step 6: Commit**

```bash
# On VPS
cd /root/.openclaw/workspace
git add canal-cirlene-niza/skills/
git commit -m "feat(cirlene): add identidade + roteiro skills"
```

---

### Task 10: Configure Narrador agent (clonev voice synthesis)

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-narrador/SKILL.md`

- [ ] **Step 1: Write Narrador skill**

```bash
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-narrador
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-narrador/SKILL.md << 'SKILL'
---
name: cirlene-narrador
description: Synthesize narration audio for each scene using Cirlene's cloned voice via clonev. Uploads to MinIO cirlene-audio/. Use after Roteirista produces script JSON.
---

# Narrador — Cirlene Niza

## Inputs
- production_id: string
- scenes: array from roteiro JSON (fields: order, narration, duration_s)
- voice_ref: $CIRLENE_VOICE_SAMPLE

## Process (for each scene)
1. Strip any stage directions from narration text: remove [pause], (beat), *emphasis*, etc.
2. Call clonev skill to synthesize narration:
   - text: scene.narration
   - voice_ref: $CIRLENE_VOICE_SAMPLE
   - language: pt
   - output: /tmp/cirlene_audio_{production_id}_{scene_order}.wav
3. Upload WAV to MinIO:
   - bucket: cirlene-audio
   - key: {production_id}/{scene_order}.wav
4. Update Baserow scenes_cirlene row:
   - field $FIELD_SCENE_AUDIO_URL = "minio://cirlene-audio/{production_id}/{scene_order}.wav"

## Output
Return array of audio_url for each scene (minio:// format).
Log cost_usd = 0 (clonev is local, no API cost) to costs_cirlene.
SKILL
```

- [ ] **Step 2: Link to workspace skills**

```bash
ln -s /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-narrador \
      /root/.openclaw/workspace/skills/cirlene-narrador
```

- [ ] **Step 3: Test narration for one scene**

In cirlene agent chat at localhost:18790:
```
Use cirlene-narrador to synthesize audio for:
production_id: test-001
scene: {"order": 1, "narration": "Olá, hoje vamos falar sobre vitamina D, essencial para sua saúde e imunidade.", "duration_s": 8}

Upload to MinIO and return the audio URL.
```

Expected: `minio://cirlene-audio/test-001/1.wav` + file visible via `mc ls minio/cirlene-audio/test-001/`

---

### Task 11: Configure Avatar agent (HeyGen + ai-avatar-generation)

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-avatar/SKILL.md`

- [ ] **Step 1: Write Avatar skill**

```bash
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-avatar
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-avatar/SKILL.md << 'SKILL'
---
name: cirlene-avatar
description: Generate Cirlene Niza talking head video using HeyGen (avatar mode) or static avatar images using ai-avatar-generation. Use for AVATAR mode productions.
---

# Avatar — Cirlene Niza

## Inputs
- production_id: string
- audio_url: minio:// path to full narration audio (concatenated scenes)
- mode: "talking_head" | "static"

## Talking Head Flow (mode=talking_head)
1. Download audio from MinIO to /tmp/cirlene_full_{production_id}.wav
2. Convert to MP3 for HeyGen: ffmpeg -i input.wav -q:a 0 output.mp3
3. Upload audio to HeyGen:
   ```
   POST https://upload.heygen.com/v1/video/upload
   X-Api-Key: $HEYGEN_API_KEY
   Body: multipart/form-data, file=output.mp3
   ```
   Note: audio_asset_id from response
4. Generate video:
   ```
   POST https://api.heygen.com/v2/video/generate
   {
     "video_inputs": [{
       "character": {"type": "avatar", "avatar_id": "$HEYGEN_AVATAR_ID", "avatar_style": "normal"},
       "voice": {"type": "audio", "audio_asset_id": "<audio_asset_id>"}
     }],
     "dimension": {"width": 1080, "height": 1920}
   }
   ```
   Note: video_id from response
5. Poll status every 30s until complete:
   GET https://api.heygen.com/v1/video_status.get?video_id={video_id}
6. Download video_url → /tmp/cirlene_avatar_{production_id}.mp4
7. Upload to MinIO: cirlene-avatar/{production_id}/talking_head.mp4
8. Update Baserow: production avatar_url field

## Static Avatar Flow (mode=static)
Use ai-avatar-generation skill to generate:
- Profile photo: "Cirlene Niza, Brazilian nutritionist, warm smile, professional, health wellness setting"
- Thumbnail avatar: same prompt, different framing
Save PNG files to: MinIO cirlene-avatar/{production_id}/profile.png

## Output
Return video_url (minio:// format for talking head) or image_url (static).
Log cost to costs_cirlene (provider: heygen, estimated $0.10-0.30 per minute of video).
SKILL
```

- [ ] **Step 2: Link to workspace skills**

```bash
ln -s /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-avatar \
      /root/.openclaw/workspace/skills/cirlene-avatar
```

- [ ] **Step 3: E2E test — voice → avatar video**

In cirlene agent chat:
```
Use cirlene-avatar to create a talking head video:
production_id: test-001
audio_url: minio://cirlene-audio/test-001/1.wav
mode: talking_head

Return the video URL when complete.
```

Expected: `minio://cirlene-avatar/test-001/talking_head.mp4` (may take 2-3 minutes)

- [ ] **Step 4: Download and verify video locally**

```bash
mc cp minio/cirlene-avatar/test-001/talking_head.mp4 ~/Desktop/cirlene_avatar_test.mp4
open ~/Desktop/cirlene_avatar_test.mp4
```

Verify: Cirlene's face visible, lip-sync acceptable, vertical 9:16 format

---

## Phase 3 — Visual + Assembly Pipeline

### Task 12: Configure Criativo agent (evolink-media)

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-criativo/SKILL.md`

- [ ] **Step 1: Verify Evolink API key on VPS**

```bash
ssh vps
grep -i evolink /root/.openclaw/agents/main/agent/auth-profiles.json
grep -i EVOLINK /root/.openclaw/workspace/canal-cirlene-niza/.env || echo "Not set"
```

If not set, add to .env:
```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
EVOLINK_API_KEY=<your-evolink-api-key>
EOF
```

Get API key at https://evolink.ai → Dashboard → API Keys

- [ ] **Step 2: Write Criativo skill**

```bash
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-criativo
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-criativo/SKILL.md << 'SKILL'
---
name: cirlene-criativo
description: Generate scene images, YouTube thumbnail, and Instagram carousel slides for Cirlene Niza content using evolink-media. Use for CENAS mode productions.
---

# Criativo Visual — Cirlene Niza

## Load cirlene-identidade before generating any images.

## Inputs
- production_id: string
- scenes: array from roteiro JSON (fields: order, image_prompt, on_screen_text)
- title: string (for thumbnail text)

## Scene Images (for CENAS mode)
For each scene, use evolink-media to generate image:
- model: "gpt-image-1" (best quality for health/nutrition content)
- prompt: scene.image_prompt + " vertical composition 9:16, health wellness aesthetic, clean bright colors"
- size: 1080x1920
- Save to: MinIO cirlene-arts/{production_id}/scene_{order}.jpg
- Update Baserow scenes_cirlene field $FIELD_SCENE_IMAGE_URL

## Thumbnail
Generate thumbnail:
- prompt: "Brazilian nutritionist presenting health tips, professional studio background, text overlay space at bottom, YouTube thumbnail style, bright engaging colors"
- size: 1280x720 (horizontal for YouTube)
- Save to: MinIO cirlene-arts/{production_id}/thumbnail.jpg

## Instagram Carousel (5-8 slides)
Generate carousel slides (1080x1080 square):
- Slide 1: Hook/title card — clean background, large text: {title}
- Slides 2-6: One tip per slide — image_prompt from scenes + on_screen_text
- Last slide: CTA — "Siga @CirleneNiza para mais dicas!"
- Save each to: MinIO cirlene-arts/{production_id}/carousel_{n}.png

## Cost Logging
Log each API call to costs_cirlene:
- provider: evolink
- step: image_scene_{order} / thumbnail / carousel_{n}
- cost_usd: ~0.15 per image (gpt-image-1)
SKILL
```

- [ ] **Step 3: Link and test**

```bash
ln -s /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-criativo \
      /root/.openclaw/workspace/skills/cirlene-criativo
```

In cirlene agent chat:
```
Use cirlene-criativo to generate scene images for:
production_id: test-002
scenes: [{"order":1,"image_prompt":"fresh colorful fruits and vegetables on white marble surface, top view","on_screen_text":"Coma mais cores!"}]
title: "5 Alimentos que Mudam Sua Vida"

Return MinIO URLs for all generated images.
```

Expected: `minio://cirlene-arts/test-002/scene_1.jpg` + file visible in MinIO

---

### Task 13: Configure Montador agent (FFmpeg assembly)

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-montador/SKILL.md`

- [ ] **Step 1: Verify FFmpeg installed on VPS**

```bash
ssh vps
ffmpeg -version | head -1
```

Expected: `ffmpeg version 4.x.x` or higher

- [ ] **Step 2: Write Montador skill**

```bash
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-montador
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-montador/SKILL.md << 'SKILL'
---
name: cirlene-montador
description: Assemble final 9:16 vertical video for Cirlene Niza. Handles AVATAR mode (talking head) and CENAS mode (scene images + narration). Use after Narrador + Avatar/Criativo complete.
---

# Montador — Cirlene Niza

## Inputs
- production_id: string
- mode: "avatar" | "cenas"
- scenes: array with audio_url and image_url (cenas mode) or avatar video_url (avatar mode)

## AVATAR Mode Assembly
1. Download talking_head.mp4 from minio://cirlene-avatar/{production_id}/talking_head.mp4
2. Ensure 9:16 (1080×1920) — HeyGen should output this, verify with ffprobe
3. Add subtitles (optional — from SRT if generated):
   ffmpeg -i input.mp4 -vf "subtitles=subs.srt:force_style='FontSize=24,PrimaryColour=&Hffffff,Bold=1'" -c:a copy output.mp4
4. Upload to: minio://cirlene-final/{production_id}/final.mp4

## CENAS Mode Assembly
1. Download all scene audios from minio://cirlene-audio/{production_id}/{n}.wav
2. Download all scene images from minio://cirlene-arts/{production_id}/scene_{n}.jpg
3. For each scene, create video segment (image duration = scene.duration_s):
   ffmpeg -loop 1 -i scene_{n}.jpg -i audio_{n}.wav -c:v libx264 -tune stillimage -c:a aac -b:a 192k -pix_fmt yuv420p -t {duration_s} -vf "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2" segment_{n}.mp4
4. Create concat file:
   echo "file 'segment_1.mp4'" > concat.txt
   echo "file 'segment_2.mp4'" >> concat.txt
   # ... for all segments
5. Concatenate with crossfade:
   ffmpeg -f concat -safe 0 -i concat.txt -c:v libx264 -c:a aac -movflags +faststart final.mp4
6. Verify duration: ffprobe -i final.mp4 -show_entries format=duration -v quiet -of csv=p=0
   Must be between 40 and 65 seconds
7. Upload to: minio://cirlene-final/{production_id}/final.mp4

## Output
Return final_video_url (minio:// format).
Cleanup: remove all /tmp/cirlene_{production_id}_* files after upload.
SKILL
```

- [ ] **Step 3: Link and test assembly (CENAS mode)**

```bash
ln -s /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-montador \
      /root/.openclaw/workspace/skills/cirlene-montador
```

In cirlene agent chat (using test-001 audio from Task 10 and test-002 image from Task 12):
```
Use cirlene-montador to assemble a CENAS mode video:
production_id: test-003
mode: cenas
scenes: [
  {"order":1, "audio_url":"minio://cirlene-audio/test-001/1.wav", "image_url":"minio://cirlene-arts/test-002/scene_1.jpg", "duration_s":8}
]
Return the final video URL.
```

- [ ] **Step 4: Download and verify assembled video**

```bash
mc cp minio/cirlene-final/test-003/final.mp4 ~/Desktop/cirlene_cenas_test.mp4
open ~/Desktop/cirlene_cenas_test.mp4
```

Verify: 9:16 vertical, audio synced with image, no corruption, correct duration

---

## Phase 4 — Approval + Publishing

### Task 14: Build Streamlit Aprovação app (Streamlit :8503)

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/platform/aprovacao.py`
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/platform/requirements.txt`
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/platform/baserow_client.py`

- [ ] **Step 1: Create platform directory and requirements**

```bash
ssh vps
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/platform

cat > /root/.openclaw/workspace/canal-cirlene-niza/platform/requirements.txt << 'EOF'
streamlit>=1.40.0
requests>=2.31.0
boto3>=1.34.0
python-dotenv>=1.0.0
EOF

pip3 install -r /root/.openclaw/workspace/canal-cirlene-niza/platform/requirements.txt
```

- [ ] **Step 2: Write Baserow client helper**

```python
# /root/.openclaw/workspace/canal-cirlene-niza/platform/baserow_client.py
import os, requests
from dotenv import load_dotenv

load_dotenv("/root/.openclaw/workspace/canal-cirlene-niza/.env")

BASE = os.getenv("BASEROW_URL")
TOKEN = os.getenv("BASEROW_TOKEN")
HEADERS = {"Authorization": f"Token {TOKEN}", "Content-Type": "application/json"}

PROD_TABLE = os.getenv("PROD_TABLE_ID")
FIELD_PROD_TITLE = os.getenv("FIELD_PROD_TITLE")
FIELD_STATUS = os.getenv("FIELD_PROD_STATUS")
FIELD_APPROVAL = os.getenv("FIELD_PROD_APPROVAL_STATUS")
FIELD_PROD_FINAL_URL = os.getenv("FIELD_PROD_FINAL_URL")
SCENES_TABLE = os.getenv("SCENES_TABLE_ID")
FIELD_SCENE_PRODUCTION_ID = os.getenv("FIELD_SCENE_PRODUCTION_ID")
FIELD_SCENE_AUDIO_URL = os.getenv("FIELD_SCENE_AUDIO_URL")
FIELD_SCENE_IMAGE_URL = os.getenv("FIELD_SCENE_IMAGE_URL")
FIELD_SCENE_SCRIPT_TEXT = os.getenv("FIELD_SCENE_SCRIPT_TEXT")
FIELD_SCENE_ORDER = os.getenv("FIELD_SCENE_ORDER")


def get_productions_by_status(status: str) -> list:
    r = requests.get(
        f"{BASE}/api/database/rows/table/{PROD_TABLE}/",
        headers=HEADERS,
        params={"filter__field_{FIELD_STATUS}__equal": status}
    )
    return r.json().get("results", [])


def get_scenes_for_production(production_id: int) -> list:
    r = requests.get(
        f"{BASE}/api/database/rows/table/{SCENES_TABLE}/",
        headers=HEADERS,
        params={f"filter__field_{FIELD_SCENE_PRODUCTION_ID}__equal": production_id}
    )
    return sorted(r.json().get("results", []), key=lambda s: s.get(f"field_{FIELD_SCENE_ORDER}", 0))


def update_production(row_id: int, fields: dict) -> dict:
    r = requests.patch(
        f"{BASE}/api/database/rows/table/{PROD_TABLE}/{row_id}/",
        headers=HEADERS,
        json=fields
    )
    return r.json()


def set_approval_status(row_id: int, approval: str):
    update_production(row_id, {f"field_{FIELD_APPROVAL}": approval})


def advance_status(row_id: int, new_status: str):
    update_production(row_id, {f"field_{FIELD_STATUS}": new_status})
```

- [ ] **Step 3: Write Streamlit aprovação app**

```python
# /root/.openclaw/workspace/canal-cirlene-niza/platform/aprovacao.py
import streamlit as st
import boto3, os
from dotenv import load_dotenv
from baserow_client import (
    get_productions_by_status, get_scenes_for_production,
    set_approval_status, advance_status,
    FIELD_PROD_TITLE, FIELD_STATUS, FIELD_PROD_FINAL_URL,
    FIELD_SCENE_SCRIPT_TEXT, FIELD_SCENE_IMAGE_URL, FIELD_SCENE_AUDIO_URL, FIELD_SCENE_ORDER
)

load_dotenv("/root/.openclaw/workspace/canal-cirlene-niza/.env")

st.set_page_config(page_title="Aprovação — Cirlene Niza", layout="wide")

MINIO_ENDPOINT = os.getenv("MINIO_ENDPOINT")
MINIO_KEY = os.getenv("MINIO_ACCESS_KEY")
MINIO_SECRET = os.getenv("MINIO_SECRET_KEY")


def presigned_url(minio_url: str, expires: int = 3600) -> str:
    if not minio_url or not minio_url.startswith("minio://"):
        return ""
    parts = minio_url.replace("minio://", "").split("/", 1)
    bucket, key = parts[0], parts[1]
    s3 = boto3.client(
        "s3", endpoint_url=MINIO_ENDPOINT,
        aws_access_key_id=MINIO_KEY, aws_secret_access_key=MINIO_SECRET
    )
    return s3.generate_presigned_url("get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=expires)


st.title("Cirlene Niza — Aprovação de Conteúdo")

gate = st.sidebar.radio("Gate", ["Gate 1: Script", "Gate 2: Artes + Avatar", "Gate 3: Vídeo Final"])

# GATE 1 — Script approval
if gate == "Gate 1: Script":
    productions = get_productions_by_status("pending_script")
    if not productions:
        st.info("Nenhum roteiro aguardando aprovação.")
    for prod in productions:
        with st.expander(f"📝 {prod.get('field_' + os.getenv('FIELD_PROD_TITLE', ''), 'Sem título')} — ID {prod['id']}"):
            scenes = get_scenes_for_production(prod["id"])
            for s in scenes:
                st.markdown(f"**Cena {s.get('field_' + FIELD_SCENE_ORDER, '?')}:** {s.get('field_' + FIELD_SCENE_SCRIPT_TEXT, '')}")
            col1, col2 = st.columns(2)
            if col1.button("✅ Aprovar Script", key=f"approve_script_{prod['id']}"):
                set_approval_status(prod["id"], "approved")
                advance_status(prod["id"], "pending_assets")
                st.success("Script aprovado! Assets sendo gerados...")
                st.rerun()
            if col2.button("🔄 Revisar", key=f"revise_script_{prod['id']}"):
                set_approval_status(prod["id"], "revise")
                st.warning("Marcado para revisão.")
                st.rerun()

# GATE 2 — Arts + Avatar approval
elif gate == "Gate 2: Artes + Avatar":
    productions = get_productions_by_status("pending_assets")
    if not productions:
        st.info("Nenhuma arte aguardando aprovação.")
    for prod in productions:
        with st.expander(f"🎨 {prod.get('field_' + os.getenv('FIELD_PROD_TITLE', ''), 'Sem título')} — ID {prod['id']}"):
            scenes = get_scenes_for_production(prod["id"])
            cols = st.columns(min(len(scenes), 3))
            for i, s in enumerate(scenes):
                img_url = presigned_url(s.get("field_" + FIELD_SCENE_IMAGE_URL, ""))
                if img_url:
                    cols[i % 3].image(img_url, caption=f"Cena {i+1}", use_container_width=True)
            col1, col2 = st.columns(2)
            if col1.button("✅ Aprovar Artes", key=f"approve_arts_{prod['id']}"):
                set_approval_status(prod["id"], "approved")
                advance_status(prod["id"], "pending_video")
                st.success("Artes aprovadas! Montagem em andamento...")
                st.rerun()
            if col2.button("🔄 Revisar Artes", key=f"revise_arts_{prod['id']}"):
                set_approval_status(prod["id"], "revise")
                st.warning("Marcado para revisão.")
                st.rerun()

# GATE 3 — Final video + publish
elif gate == "Gate 3: Vídeo Final":
    productions = get_productions_by_status("pending_video")
    if not productions:
        st.info("Nenhum vídeo aguardando aprovação.")
    for prod in productions:
        final_minio = prod.get(f"field_{FIELD_PROD_FINAL_URL}", "")
        with st.expander(f"🎬 {prod.get(f'field_{FIELD_PROD_TITLE}', 'Sem título')} — ID {prod['id']}"):
            if final_minio:
                video_url = presigned_url(final_minio, expires=7200)
                if video_url:
                    st.video(video_url)
            col1, col2 = st.columns(2)
            if col1.button("🚀 PUBLICAR", key=f"publish_{prod['id']}", type="primary"):
                advance_status(prod["id"], "publishing")
                st.success("Publicação iniciada! Aguarde notificação no Telegram.")
                st.rerun()
            if col2.button("🔄 Revisar Vídeo", key=f"revise_video_{prod['id']}"):
                set_approval_status(prod["id"], "revise")
                st.warning("Marcado para revisão.")
                st.rerun()
```

- [ ] **Step 4: Start Streamlit aprovação and verify**

```bash
ssh vps
cd /root/.openclaw/workspace/canal-cirlene-niza/platform
nohup streamlit run aprovacao.py --server.port 8503 --server.address 0.0.0.0 &
sleep 5
curl -s http://localhost:8503 | grep -i "streamlit" | head -1
```

Expected: HTML response containing Streamlit content

- [ ] **Step 5: View in browser**

Open: `http://186.202.209.88:8503`

Verify: 3 gates visible in sidebar, Gate 1 shows "Nenhum roteiro aguardando aprovação" (no productions yet)

---

### Task 15: Write `cirlene-publicacao` skill and configure Publicador

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-publicacao/SKILL.md`

- [ ] **Step 1: Write Publicador skill**

```bash
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-publicacao
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-publicacao/SKILL.md << 'SKILL'
---
name: cirlene-publicacao
description: Publish Cirlene Niza content to TikTok, YouTube Shorts, and Instagram via Postiz API + instagram-api for carousel. Triggered after Gate 3 approval.
---

# Publicador — Cirlene Niza

## Inputs
- production_id: string
- final_video_url: minio:// path to assembled video
- carousel_urls: array of minio:// paths to carousel PNGs (for Instagram)
- captions: object with {tiktok, youtube_title, youtube_description, instagram}

## Step 1: Get presigned video URL (Postiz needs public URL)
Use MinIO presigned URL (7 days) for the final video:
Generate via boto3: s3.generate_presigned_url("get_object", Params={"Bucket": "cirlene-final", "Key": "{production_id}/final.mp4"}, ExpiresIn=604800)

## Step 2: Post to TikTok + YouTube + Instagram Reels via Postiz
```
POST https://api.postiz.com/public/v1/posts
{
  "type": "now",
  "integrations": ["$POSTIZ_TIKTOK_ID", "$POSTIZ_YOUTUBE_ID", "$POSTIZ_INSTAGRAM_ID"],
  "content": "<captions.instagram>",
  "media": [{"url": "<presigned_video_url>", "type": "video"}],
  "settings": {
    "$POSTIZ_YOUTUBE_ID": {"title": "<captions.youtube_title>", "description": "<captions.youtube_description>", "category": "People & Blogs"},
    "$POSTIZ_TIKTOK_ID": {"caption": "<captions.tiktok>"}
  }
}
```
Record post_ids from response → save to Baserow social_posts_cirlene for each platform.

## Step 3: Post Instagram Carousel separately via instagram-api
Use instagram-api skill to post carousel:
- images: carousel_urls (presigned URLs)
- caption: captions.instagram
- type: CAROUSEL
Record post_id → save to Baserow social_posts_cirlene (platform: instagram_carousel)

## Step 4: Update production status
Set Baserow productions_cirlene status = "published"
Send Telegram notification (use Telegram bot token from .env):
```
POST https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage
{
  "chat_id": "$TELEGRAM_CHAT_ID",
  "text": "✅ Publicado!\nTítulo: {title}\nTikTok: {tiktok_url}\nYouTube: {youtube_url}\nInstagram: {instagram_url}"
}
```
SKILL
```

- [ ] **Step 2: Add Telegram config to .env**

```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
TELEGRAM_BOT_TOKEN=<cirlene-bot-token-from-BotFather>
TELEGRAM_CHAT_ID=<your-telegram-user-or-group-id>
EOF
```

- [ ] **Step 3: Link skill**

```bash
ln -s /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-publicacao \
      /root/.openclaw/workspace/skills/cirlene-publicacao
```

- [ ] **Step 4: Test Postiz post (use a test video, do NOT publish on first run)**

In cirlene agent chat:
```
Use cirlene-publicacao to publish a TEST draft (do not actually post — set type:"draft"):
production_id: test-003
final_video_url: minio://cirlene-final/test-003/final.mp4
captions: {
  "tiktok": "Teste Cirlene Niza 🥗 #nutricao #saude",
  "youtube_title": "Teste - Cirlene Niza",
  "youtube_description": "Vídeo de teste do canal Cirlene Niza.",
  "instagram": "Teste @CirleneNiza 🌿"
}

Return the Postiz draft post ID.
```

Expected: Postiz draft post ID (visible in Postiz dashboard as draft)

---

### Task 16: E2E pipeline test with approval gates

- [ ] **Step 1: Trigger a full production via cirlene agent**

In cirlene agent chat at localhost:18790:
```
Start a new production pipeline:
theme: "Alimentos que melhoram o sono"
mode: cenas

Use these skills in order:
1. cirlene-identidade + cirlene-roteiro → generate script
2. Save script to Baserow productions_cirlene (status: pending_script)
3. cirlene-narrador → synthesize audio for each scene
4. cirlene-criativo → generate scene images
5. Update Baserow status to pending_assets
6. Send Telegram notification: "Roteiro pronto! Aprovar em http://186.202.209.88:8503"
```

- [ ] **Step 2: Approve script via Streamlit Gate 1**

Open `http://186.202.209.88:8503` → Gate 1 → see the new production → Aprovar Script

Verify Baserow: `productions_cirlene` status changes to `pending_assets`

- [ ] **Step 3: Continue pipeline — approve arts Gate 2**

Refresh Gate 2 in Streamlit → see scene images → Aprovar Artes

Verify: status advances to `pending_video`

- [ ] **Step 4: Montador assembles video**

In cirlene agent chat:
```
Production {id} status is now pending_video. Use cirlene-montador to assemble the final video.
Upload to minio://cirlene-final/{id}/final.mp4
Then notify via Telegram for Gate 3 approval.
```

- [ ] **Step 5: Gate 3 — preview and verify publish button works (do NOT publish real content yet)**

Streamlit Gate 3 → video player shows assembled video → verify layout correct

Do NOT click PUBLICAR yet — test publishing in a controlled way in Task 15 Step 4.

---

## Phase 5 — Dashboard + Monitoring

### Task 17: Build Streamlit Dashboard (Streamlit :8504)

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/platform/dashboard.py`

- [ ] **Step 1: Write dashboard app**

```python
# /root/.openclaw/workspace/canal-cirlene-niza/platform/dashboard.py
import streamlit as st
import requests, os
from datetime import datetime, timedelta
from dotenv import load_dotenv
from baserow_client import get_productions_by_status, HEADERS, BASE

load_dotenv("/root/.openclaw/workspace/canal-cirlene-niza/.env")

st.set_page_config(page_title="Dashboard — Cirlene Niza", layout="wide", page_icon="📊")

POSTIZ_KEY = os.getenv("POSTIZ_API_KEY")
POSTIZ_URL = "https://api.postiz.com/public/v1"
PROD_TABLE = os.getenv("PROD_TABLE_ID")
COSTS_TABLE = os.getenv("COSTS_TABLE_ID")
POSTS_TABLE = os.getenv("POSTS_TABLE_ID")
METRICS_TABLE = os.getenv("METRICS_TABLE_ID")


def all_productions() -> list:
    r = requests.get(f"{BASE}/api/database/rows/table/{PROD_TABLE}/", headers=HEADERS,
                     params={"order_by": "-id", "size": 50})
    return r.json().get("results", [])


def monthly_cost() -> float:
    month_start = datetime.now().replace(day=1).isoformat()
    r = requests.get(f"{BASE}/api/database/rows/table/{COSTS_TABLE}/", headers=HEADERS,
                     params={f"filter__field_{os.getenv('FIELD_COST_PRODUCTION_ID')}__date_after": month_start})
    costs = r.json().get("results", [])
    return sum(float(c.get(f"field_{os.getenv('FIELD_COST_USD')}", 0)) for c in costs)


def postiz_analytics() -> list:
    r = requests.get(f"{POSTIZ_URL}/analytics", headers={"Authorization": f"Bearer {POSTIZ_KEY}"})
    return r.json().get("posts", []) if r.status_code == 200 else []


st.title("Dashboard — Canal Cirlene Niza")
tab1, tab2 = st.tabs(["Cirlene Niza", "FEM"])

with tab1:
    col_budget, col_total, col_published = st.columns(3)
    cost = monthly_cost()
    col_budget.metric("Custo este mês", f"${cost:.2f}", delta=None)

    prods = all_productions()
    published = [p for p in prods if p.get(f"field_{os.getenv('FIELD_PROD_STATUS')}") == "published"]
    col_total.metric("Produções (total)", len(prods))
    col_published.metric("Publicados", len(published))

    st.subheader("Pipeline")
    statuses = ["pending_script", "pending_assets", "pending_video", "published", "failed"]
    cols = st.columns(len(statuses))
    for i, status in enumerate(statuses):
        items = [p for p in prods if p.get(f"field_{os.getenv('FIELD_PROD_STATUS')}") == status]
        with cols[i]:
            st.markdown(f"**{status.replace('_', ' ').title()}** ({len(items)})")
            for p in items[:5]:
                title_field = f"field_{os.getenv('FIELD_PROD_TITLE')}"
                st.markdown(f"- {p.get(title_field, 'Sem título')[:40]}")

    st.subheader("Nova Produção")
    with st.form("nova_producao"):
        theme = st.text_input("Tema", placeholder="Ex: Benefícios da vitamina D")
        mode = st.selectbox("Modo", ["cenas", "avatar"])
        submitted = st.form_submit_button("🚀 Iniciar Produção")
        if submitted and theme:
            st.info(f"Produção iniciada: '{theme}' ({mode}). O Diretor foi notificado.")
            # In production: call cirlene OpenClaw agent API to start pipeline

    st.subheader("Métricas (últimos 7 dias)")
    analytics = postiz_analytics()
    if analytics:
        for post in analytics[:10]:
            st.markdown(f"**{post.get('content', '')[:60]}** — {post.get('views', 0)} views, {post.get('likes', 0)} likes")
    else:
        st.info("Dados de métricas disponíveis 24h após publicação.")

with tab2:
    st.subheader("FEM — Status (read-only)")
    FEM_PROD_TABLE = os.getenv("FEM_PROD_TABLE_ID", "702")
    r = requests.get(f"{BASE}/api/database/rows/table/{FEM_PROD_TABLE}/", headers=HEADERS,
                     params={"order_by": "-id", "size": 10})
    fem_prods = r.json().get("results", []) if r.status_code == 200 else []
    if fem_prods:
        for p in fem_prods:
            st.markdown(f"- **{list(p.values())[1]}** — {list(p.values())[2]}")
    else:
        st.info("Sem produções FEM recentes ou tabela não configurada.")
    st.caption("FEM dashboard é read-only. Para ações, use o agente FEM em localhost:18789")
```

- [ ] **Step 2: Add FEM table ID to .env**

```bash
cat >> /root/.openclaw/workspace/canal-cirlene-niza/.env << 'EOF'
FEM_PROD_TABLE_ID=702
EOF
```

- [ ] **Step 3: Start dashboard and verify**

```bash
ssh vps
cd /root/.openclaw/workspace/canal-cirlene-niza/platform
nohup streamlit run dashboard.py --server.port 8504 --server.address 0.0.0.0 &
sleep 5
curl -s http://localhost:8504 | grep -i streamlit | head -1
```

- [ ] **Step 4: View in browser**

Open: `http://186.202.209.88:8504`

Verify:
- Tab "Cirlene Niza": metrics, pipeline kanban, "Nova Produção" form visible
- Tab "FEM": shows recent FEM productions (or "not configured" if FEM table structure differs)

---

### Task 18: Configure Analista agent + systemd services

**Files:**
- Create: `/root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-analista/SKILL.md`
- Create: `/etc/systemd/system/cirlene-aprovacao.service`
- Create: `/etc/systemd/system/cirlene-dashboard.service`
- Create: `/etc/systemd/system/cirlene-analista.timer`

- [ ] **Step 1: Write Analista skill**

```bash
mkdir -p /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-analista
cat > /root/.openclaw/workspace/canal-cirlene-niza/skills/cirlene-analista/SKILL.md << 'SKILL'
---
name: cirlene-analista
description: Collect social media metrics via Postiz analytics API, store in Baserow, and send Telegram alerts for viral posts or budget overruns. Run on schedule.
---

# Analista — Cirlene Niza

## Schedule: run daily at 9:00 AM UTC

## Step 1: Get posts published in last 24h from Baserow social_posts_cirlene
Query: published_at > now - 24h

## Step 2: Fetch metrics from Postiz for each post
GET https://api.postiz.com/public/v1/posts/{post_id}/analytics
Record: views, likes, shares, comments

## Step 3: Save to Baserow metrics_cirlene
One row per post per collection run.

## Step 4: Check alert thresholds
- Views > 10,000 in 24h → Telegram: "🔥 Vídeo viral! '{title}' tem {views} visualizações. Faça mais conteúdo sobre '{theme}'."
- Monthly cost > R$200 ($40 USD) → Telegram: "⚠️ Budget: ${cost:.2f} este mês. Limite: $40."

## Step 5: Check for productions stuck in approval > 48h
Query productions where status starts with "pending_" and updated > 48h ago.
Send Telegram reminder: "⏰ Aprovação pendente há 48h: '{title}'. Revisar em http://186.202.209.88:8503"
SKILL
```

- [ ] **Step 2: Create systemd service for Streamlit aprovação**

```bash
cat > /etc/systemd/system/cirlene-aprovacao.service << 'EOF'
[Unit]
Description=Cirlene Niza - Streamlit Aprovação
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/canal-cirlene-niza/platform
EnvironmentFile=/root/.openclaw/workspace/canal-cirlene-niza/.env
ExecStart=/usr/local/bin/streamlit run aprovacao.py --server.port 8503 --server.address 0.0.0.0 --server.headless true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

- [ ] **Step 3: Create systemd service for Streamlit dashboard**

```bash
cat > /etc/systemd/system/cirlene-dashboard.service << 'EOF'
[Unit]
Description=Cirlene Niza - Streamlit Dashboard
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/root/.openclaw/workspace/canal-cirlene-niza/platform
EnvironmentFile=/root/.openclaw/workspace/canal-cirlene-niza/.env
ExecStart=/usr/local/bin/streamlit run dashboard.py --server.port 8504 --server.address 0.0.0.0 --server.headless true
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
```

- [ ] **Step 4: Enable and start services**

```bash
systemctl daemon-reload
systemctl enable cirlene-aprovacao cirlene-dashboard
systemctl start cirlene-aprovacao cirlene-dashboard
systemctl status cirlene-aprovacao cirlene-dashboard
```

Expected: both services show `active (running)`

- [ ] **Step 5: Verify services survive reboot**

```bash
systemctl is-enabled cirlene-aprovacao
systemctl is-enabled cirlene-dashboard
```

Expected: `enabled` for both

---

## Phase 5 Complete — Final E2E Verification

### Task 19: Full pipeline production test (real content, no publish)

- [ ] **Step 1: Start new production from dashboard**

Open `http://186.202.209.88:8504` → "Nova Produção" → Theme: "Top 3 alimentos anti-inflamatórios" → Mode: cenas → Iniciar

- [ ] **Step 2: Approve script (Gate 1)**

Wait for Telegram notification → open `http://186.202.209.88:8503` → Gate 1 → Aprovar Script

- [ ] **Step 3: Approve arts (Gate 2)**

Wait for Telegram notification "Artes prontas" → Gate 2 → review images → Aprovar Artes

- [ ] **Step 4: Approve video (Gate 3)**

Wait for Telegram notification "Vídeo montado" → Gate 3 → review video → DO NOT publish yet

- [ ] **Step 5: Publish to staging (draft only)**

Ask cirlene agent to publish as draft to Postiz (type: "draft") → verify in Postiz dashboard

- [ ] **Step 6: Verify all success criteria from spec**

```
✅ 1. Theme → assets generated in <2h (excluding approval wait time)
✅ 2. Avatar/voice quality: check cirlene_avatar_test.mp4 from Task 11
✅ 3. All 3 gates enforced — no publish without Gate 3
✅ 4. Dashboard shows production status in both tabs
✅ 5. FEM agent at localhost:18789 still responds and untouched
```

Verify FEM isolation:
```bash
curl -s http://localhost:18789/health | grep ok
curl -s http://localhost:18790/health | grep ok
```

Both must respond.

- [ ] **Step 7: First real publish (when ready)**

When user confirms content is acceptable quality → Gate 3 → click PUBLICAR → verify Telegram notification with all 3 platform links.

---

## Post-Implementation Checklist

- [ ] All 5 Baserow tables created and accessible
- [ ] All 4 MinIO buckets created with lifecycle policies
- [ ] cirlene OpenClaw profile running on port 18790
- [ ] FEM profile still running on port 18789 (untouched)
- [ ] clonev: Cirlene voice clone working and quality acceptable
- [ ] HeyGen: talking head avatar test video passes visual inspection
- [ ] Evolink: scene images generated at health/nutrition aesthetic
- [ ] Postiz: TikTok + YouTube + Instagram all connected
- [ ] Streamlit :8503 (aprovação): all 3 gates functional
- [ ] Streamlit :8504 (dashboard): both tabs load, metrics shown after 24h
- [ ] systemd: both Streamlit services auto-start on reboot
- [ ] Telegram: bot notifications working for all alert types
- [ ] Full E2E: one production completed from theme input to published post
