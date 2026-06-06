# Pipeline Avatar + Remotion — Canal Cirlene Niza

> Referência de sessão: decisões, arquitetura e estado atual do pipeline de vídeo com avatar IA.
> Gerado em: 2026-06-05

---

## Decisão central

Substituir **HeyGen** por stack própria de avatar IA:

| Componente anterior | Substituído por | Motivo |
|---|---|---|
| HeyGen (avatar falante) | fal.ai **Veo 3.1** `reference-to-video` | Menor custo, avatar consistente via fotos reais |
| Slides estáticos | **Remotion** (animado, React) | Animações brand-compliant, render CLI para n8n |
| FFmpeg avulso | Serviço **montagem** (Docker) | Replicável VPS, HTTP API para n8n |

---

## Fluxo completo do vídeo

```
[Tema] 
  → orquestrador-cirl (n8n)
  → roteirista-cirl → scenes_cirlene (Baserow)
  → Gate 1: aprovação script (Telegram)
  ↓
[gerador-avatar-staging-cirl]     ← fal.ai Veo 3.1
  intro_prompt + outro_prompt
  → intro.mp4  (minio://cirlene-video/{pid}/intro.mp4)
  → outro.mp4  (minio://cirlene-video/{pid}/outro.mp4)
  ↓
[gerador-slides-staging-cirl]     ← renderer service (Remotion)
  scenes[] (layout + props JSON)
  → slide-0.mp4 … slide-N.mp4  (minio://cirlene-slides/slides/)
  ↓
Gate 2: aprovação artes (Streamlit :8503)
  ↓
[montagem-staging-cirl]           ← montagem service (ffmpeg)
  clips: [intro, slides..., outro]
  → final.mp4  (minio://cirlene-video/{pid}/final.mp4)
  ↓
Gate 3: aprovação vídeo (Streamlit :8503)
  ↓
[publicar-*-cirl]  → TikTok + YouTube Shorts + Instagram Reels
```

---

## Avatar Cirlene — fal.ai Veo 3.1

### Endpoint
```
POST https://queue.fal.run/fal-ai/veo3.1/reference-to-video
Authorization: Key <FAL_KEY>
```

### Parâmetros validados
```json
{
  "prompt": "...",
  "image_urls": ["url1", "url2", "url3"],
  "aspect_ratio": "9:16",
  "generate_audio": true,
  "resolution": "720p"
}
```

### Fotos de referência (fal.ai CDN — permanentes)
```
CIRLENE_REF_1=https://v3b.fal.media/files/b/0a9d190b/eJgcWqX9t4DJ2Ypx_1InI_IMG_3628.JPG
CIRLENE_REF_2=https://v3b.fal.media/files/b/0a9d190d/MPANCIXNZroF4MEj3lQhq_IMG_3629.JPG
CIRLENE_REF_3=https://v3b.fal.media/files/b/0a9d1911/2agE2ANEpIiKnJWbYge44_IMG_3631.JPG
```
Fotos originais: `/Users/studio/Desktop/Cirlene-fotos/` (29 JPGs)

### Polling pattern (n8n Code node)
```javascript
async function submitFal(prompt) {
  const resp = await fetch('https://queue.fal.run/fal-ai/veo3.1/reference-to-video', {
    method: 'POST',
    headers: { 'Authorization': `Key ${FAL_KEY}`, 'Content-Type': 'application/json' },
    body: JSON.stringify({ prompt, image_urls: REF_IMGS, aspect_ratio: '9:16',
                           generate_audio: true, resolution: '720p' }),
  });
  return (await resp.json()).request_id;
}

async function pollFal(requestId) {
  for (let i = 0; i < 30; i++) {
    await sleep(15_000);
    const r = await fetch(`https://queue.fal.run/fal-ai/veo3.1/requests/${requestId}/status`,
      { headers: { 'Authorization': `Key ${FAL_KEY}` } });
    const data = await r.json();
    if (data.status === 'COMPLETED') {
      const res = await fetch(`https://queue.fal.run/fal-ai/veo3.1/requests/${requestId}`,
        { headers: { 'Authorization': `Key ${FAL_KEY}` } });
      return (await res.json()).video?.url;
    }
    if (data.status === 'FAILED') throw new Error('fal job failed');
  }
  throw new Error('timeout');
}
```

### Prompt que funcionou (aprovado)
```
"A young Brazilian woman with long black hair and bold eyebrows,
nutrition and wellness presenter, speaking confidently to camera in Portuguese,
warm smile, professional studio look, soft white background,
9:16 vertical video, natural gestures while talking"
```

### O que NÃO funciona no prompt
- Mencionar nome real da pessoa → safety filter 422
- Texto de diálogo entre aspas diretamente → 422
- `duration: "8s"` string → usar sem o campo duration

---

## Remotion Slides — 7 Layouts

**Localização:** `slides-cientificos/`

**Canvas:** 1080×1920 px | 30 FPS | Fontes: Inter + Georgia

### Layouts implementados

| Layout | Caso de uso | Duração |
|---|---|---|
| `StatCard` | Número grande + descrição | 4s (120f) |
| `CircleStat` | Arco SVG animado com valor % | 5s (150f) |
| `ComparisonBar` | Antes/depois horizontal bars | 5s (150f) |
| `StudyQuote` | Citação científica + destaque | 4s (120f) |
| `BenefitsList` | Lista com ícones emoji staggered | 5.3s (160f) |
| `TimelineProgress` | Linha do tempo vertical | 5s (150f) |
| `ScientificDefinition` | Termo + definição + analogia | 5s (150f) |

### Render CLI
```bash
node render.mjs --props '{"layout":"StatCard","stat":"73%","description":"...","source":"...","topic":"NUTRIÇÃO"}' --out output.mp4
```

### Env vars do render.mjs
```
CHROME_EXECUTABLE_PATH=/usr/bin/chromium   # Docker
REMOTION_CACHE_DIR=/tmp/remotion-cache     # evita escrita em volume read-only
```

### Design tokens (`src/tokens.ts`)
```typescript
bg:      "#FFF5ED"   // fundo terracota claro
primary: "#E07B39"   // laranja brand
dark:    "#1C1C1E"
medium:  "#636366"
light:   "#FDECD8"
white:   "#FFFFFF"
```

---

## Docker Staging Stack

**Localização:** `docker/`

### Serviços

| Serviço | Porta local | Porta VPS | Imagem |
|---|---|---|---|
| minio | 9001 (API), 9091 (UI) | 9000, 9090 | minio/minio |
| n8n | 5679 | 5678 | n8nio/n8n |
| renderer | 3001 | 3001 | docker-renderer (custom) |
| montagem | 3002 | 3002 | docker-montagem (custom) |

### Subir stack
```bash
cd docker/
docker compose -f docker-compose.staging.yml --env-file .env.staging up -d
```

### Parar stack
```bash
docker compose -f docker-compose.staging.yml --env-file .env.staging down
```

### Credenciais staging local
```
n8n:   marcelo053@gmail.com / Cirlene2026
MinIO: minioadmin / minioadmin
fal.ai key: 443a6432-3b5b-4abe-a925-a6336817f13f:70f93e62dbc7def11558314850ea375c
n8n API key: (em .env.staging → N8N_API_KEY)
```

### Buckets MinIO (criados pelo minio-init)
```
cirlene-audio    — áudios Kokoro TTS
cirlene-arts     — imagens por cena
cirlene-video    — intro.mp4, outro.mp4, final.mp4
cirlene-slides   — slides Remotion por cena
```

---

## Renderer Service (HTTP)

**Endpoint:** `POST http://renderer:3000/render` (interno) | `http://localhost:3001/render` (host)

```json
// Request
{
  "props": { "layout": "StatCard", "stat": "73%", "description": "...", "source": "...", "topic": "NUTRIÇÃO" },
  "output": "prod-001-slide-0.mp4"
}

// Response
{
  "ok": true,
  "path": "minio://cirlene-slides/slides/prod-001-slide-0.mp4",
  "url": "<presigned URL 7 dias>"
}
```

---

## Montagem Service (HTTP)

**Endpoint:** `POST http://montagem:3000/concat` | `POST http://montagem:3000/upload-from-url`

```json
// POST /concat — request
{
  "production_id": "prod-001",
  "clips": ["http://minio:9000/...", "http://minio:9000/...", "..."],
  "output_bucket": "cirlene-video",
  "output_key": "prod-001/final.mp4"
}

// POST /upload-from-url — para salvar clip externo (ex: fal.ai CDN) no MinIO
{
  "url": "https://v3b.fal.media/...",
  "bucket": "cirlene-video",
  "key": "prod-001/intro.mp4"
}

// Response (ambos)
{
  "ok": true,
  "path": "minio://cirlene-video/prod-001/final.mp4",
  "url": "<presigned URL>"
}
```

---

## n8n Workflows Staging

**Localização dos JSONs:** `docker/n8n-workflows/`

### gerador-avatar-staging-cirl
- **Webhook:** `POST /webhook/gerador-avatar-staging-cirl`
- **Input:** `{ production_id, intro_prompt, outro_prompt }`
- **Output:** `{ intro_path, intro_url, outro_path, outro_url }`
- **Fluxo:** Code node → fal.ai submit+poll intro → upload MinIO → fal.ai submit+poll outro → upload MinIO

### gerador-slides-staging-cirl
- **Webhook:** `POST /webhook/gerador-slides-staging-cirl`
- **Input:** `{ production_id, scenes: [{ layout, ...props }] }`
- **Output:** `{ slides: [{ index, path, url }] }`
- **Fluxo:** Code node → loop scenes → POST renderer/render → collect

### montagem-staging-cirl
- **Webhook:** `POST /webhook/montagem-staging-cirl`
- **Input:** `{ production_id, intro_url, slide_urls: [], outro_url }`
- **Output:** `{ final_path, final_url }`
- **Fluxo:** Code node → POST montagem/concat

### Importar workflows
```bash
# Via CLI dentro do container
docker cp docker/n8n-workflows/. cirlene-n8n-staging:/tmp/workflows/
docker exec cirlene-n8n-staging n8n import:workflow --input=/tmp/workflows --separate

# Ativar manualmente: http://localhost:5679 → toggle em cada workflow
```

---

## Estado atual (2026-06-05)

| Componente | Status | Observação |
|---|---|---|
| Avatar Veo 3.1 (fal.ai) | ✅ Testado e aprovado | Prompt neutro sem nome real |
| Slides Remotion (7 layouts) | ✅ Build + render OK | `npm run render:test` funciona |
| Docker stack (4 serviços) | ✅ Rodando | `docker compose up -d` |
| Renderer HTTP `/render` | ✅ Funcional | Testado, MP4 no MinIO |
| Montagem HTTP `/concat` | ✅ Build OK | Não testado end-to-end |
| n8n workflows importados | ⚠️ Importados, inativos | Ativar manualmente na UI |
| n8n webhooks funcionando | ❌ Pendente | Depende de ativar workflows |
| Pipeline completo e2e | ❌ Pendente | Após ativar n8n |

---

## Próximas sessões — ordem de prioridade

### 1. Ativar workflows n8n (5 min)
```
Abrir http://localhost:5679
Login: marcelo053@gmail.com / Cirlene2026
Ativar os 3 workflows pelo toggle
```

### 2. Testar pipeline local completo
```bash
# Teste slides
curl -X POST http://localhost:5679/webhook/gerador-slides-staging-cirl \
  -H "Content-Type: application/json" \
  -d '{"production_id":"test-001","scenes":[
    {"layout":"StatCard","stat":"73%","description":"adultos com deficiência de vitamina D","source":"Journal of Nutrition 2024","topic":"NUTRIÇÃO"},
    {"layout":"BenefitsList","title":"Benefícios da Vitamina D","items":[{"icon":"☀️","text":"Fortalece o sistema imune"},{"icon":"🦴","text":"Protege os ossos"}],"source":"NIH 2024"}
  ]}'

# Teste montagem (após ter intro_url e slide_urls)
curl -X POST http://localhost:5679/webhook/montagem-staging-cirl \
  -H "Content-Type: application/json" \
  -d '{"production_id":"test-001","intro_url":"<presigned>","slide_urls":["<presigned>","<presigned>"],"outro_url":"<presigned>"}'
```

### 3. Integrar com pipeline existente (fases 2-3 do ROADMAP)
- Conectar `orquestrador-cirl` → `gerador-avatar-staging-cirl` (passar intro/outro text do roteiro)
- Conectar `gerador-imagens-cirl` → `gerador-slides-staging-cirl` (scenes do Baserow)
- Substituir montagem atual → `montagem-staging-cirl`

### 4. Deploy na VPS
```bash
# Ajustes para VPS (portas sem offset):
# WEBHOOK_URL=http://186.202.209.88:5678/
# n8n porta: 5678 (sem mudar)
# MinIO porta: 9000 (sem mudar)
# renderer porta: 3001 (nova)
# montagem porta: 3002 (nova)
scp -r docker/ user@186.202.209.88:/opt/cirlene/
ssh 186.202.209.88 "cd /opt/cirlene/docker && docker compose up -d"
```

---

## Arquivos criados nesta sessão

```
slides-cientificos/
  src/
    tokens.ts               — design tokens brand
    types.ts                — tipos TypeScript dos 7 layouts
    index.ts                — registerRoot
    Root.tsx                — Composition registry
    Slide.tsx               — dispatcher de layouts
    components/
      Chip.tsx              — topic chip animado
      Divider.tsx           — barra laranja crescente
      Source.tsx            — rodapé com fonte científica
    layouts/
      StatCard.tsx
      CircleStat.tsx
      ComparisonBar.tsx
      StudyQuote.tsx
      BenefitsList.tsx
      TimelineProgress.tsx
      ScientificDefinition.tsx
  render.mjs                — CLI render (n8n integration)
  remotion.config.ts
  tsconfig.json
  package.json

docker/
  docker-compose.staging.yml
  .env.staging              — credenciais (gitignored)
  n8n/Dockerfile            — n8n padrão
  renderer/
    Dockerfile              — node:20-bookworm + chromium
    server.mjs              — HTTP wrapper para render.mjs
    package.json
  montagem/
    Dockerfile              — node:20-alpine + ffmpeg
    server.mjs              — /concat + /upload-from-url
    package.json
  minio-init/init.sh        — cria buckets no startup
  n8n-workflows/
    gerador-avatar-staging-cirl.json
    gerador-slides-staging-cirl.json
    montagem-staging-cirl.json
  setup-workflows.sh        — import via n8n CLI
```
