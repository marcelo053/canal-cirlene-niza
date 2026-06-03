# Canal Cirlene Niza — Design System

Canal de nutrição e saúde da influencer Cirlene Niza. Conteúdo short-form 9:16 para TikTok, YouTube Shorts e Instagram Reels. Visual científico mas acessível — credibilidade sem frieza.

---

## Colors

| Role | Hex | Usage |
|------|-----|-------|
| Background | `#FFF5ED` | Fundo principal de todos os slides |
| Primary | `#E07B39` | Terracota/laranja — cor de marca, CTAs, destaques, arcos SVG |
| Dark | `#1C1C1E` | Textos principais, títulos, números grandes |
| Medium | `#636366` | Textos secundários, fontes, citações, metadados |
| Light | `#FDECD8` | Fundos de cards, badges, chips de tópico |
| White | `#FFFFFF` | Texto sobre primary, ícones sobre fundo escuro |
| Dark Background | `#2C1810` | Variante dark — logo badge, thumbnails escuros |
| Dark Background Alt | `#4A2C2A` | Segundo tom do gradiente dark |
| Light Alt | `#FAF6F1` | Variante light — thumbnails claros |

**Accent dominante:** `#E07B39` (terracota quente) — deve aparecer em todo slide como cor âncora.

---

## Typography

**Primary font:** `Inter` (sans-serif)
**Logo / display:** `Georgia` (serif) — apenas em badges CN e créditos de autor

### Scale (para 1080×1920)

| Role | Size | Weight | Notes |
|------|------|--------|-------|
| Stat hero | 220px | 900 | Números impactantes (StatCard, CircleStat) |
| Term | 96px | 900 | Termos científicos (ScientificDefinition) |
| Title | 60px | 800 | Títulos de seção |
| Subtitle / quote | 52px | 500 | Citações, descrições de stat |
| Body | 44–46px | 500–600 | Texto de lista, definições |
| Label | 28–32px | 700 | Tópico chip, fonte científica, metadata |
| Micro | 26–28px | 400–700 | Fonte em itálico, notas |

**Tracking:** `-6px` em hero stats, `-2px` em terms, `3px` em labels uppercase.
**Leading:** `1.3–1.5` em corpo de texto, `1.0–1.1` em hero numbers.
**Numeric:** `font-variant-numeric: tabular-nums` em contadores e stats.

---

## Corners

| Element | Radius |
|---------|--------|
| Topic chip / badge | `100px` (pílula) |
| Item icon box | `24px` |
| Analogy card | `24px` |
| Progress bars | `16px` |
| Divider lines | `2px` |
| Circle (avatar, milestone) | `50%` |

---

## Spacing & Density

Canvas: **1080 × 1920px**, padding interno: **100px vertical / 80px horizontal**.

| Gap | Value |
|-----|-------|
| Entre seções principais | `60–100px` |
| Entre itens de lista | `40px` |
| Entre label e conteúdo | `16–24px` |
| Icon box → texto | `36px` |

Layout base: `flex-direction: column`, `justify-content: center`, `box-sizing: border-box`.

---

## Motion

**Filosofia:** entrances com spring médio — confiante, não saltitante. Sem exits (exceto fade final).

### Easing signatures

| Tipo | GSAP ease | Uso |
|------|-----------|-----|
| Hero number / stat | `elastic.out(1, 0.5)` | scale 0→1 em números grandes |
| Text reveal | `power3.out` | translateY + opacity |
| Item stagger | `power2.out` | translateX(-60→0) + opacity |
| Divider grow | `power2.inOut` | width 0→100% |
| Background fade | `none` (linear) | opacity 0→1 nos primeiros 0.3s |
| Arc progress | `power1.inOut` | strokeDashoffset em SVG |

### Timing patterns (30fps = 1s)

| Evento | Timing |
|--------|--------|
| BG fade in | `0 → 0.3s` |
| Topic chip | `0.2 → 0.5s` |
| Title entrance | `0s, duration 0.7s` |
| Hero stat / term | `0.3s, duration 0.7s (spring)` |
| Divider grow | `0.8 → 1.7s` |
| Description reveal | `0.9 → 1.5s` |
| List item 1 | `0.8s` |
| List stagger | `+0.6s por item` |
| Source fade | `1.7 → 2.2s` |
| Arc SVG progress | `0.5 → 2.5s` |

**Durations padrão por layout:**

| Layout | Duração |
|--------|---------|
| StatCard | 4s (120 frames) |
| ComparisonBar | 5s (150 frames) |
| StudyQuote | 4s (120 frames) |
| BenefitsList | 5.3s (160 frames) |
| TimelineProgress | 5s (150 frames) |
| CircleStat | 5s (150 frames) |
| ScientificDefinition | 5s (150 frames) |

---

## Depth

**Flat com acento suave.** Sem `box-shadow` nos elementos principais.

Exceção permitida: `ScientificDefinition` analogy card tem `border-left: 6px solid #E07B39` como único elemento de profundidade.

---

## Brand Elements

### Topic chip
```
background: #FDECD8
color: #E07B39
font-size: 28–32px, weight 700
padding: 10–14px 32–40px
border-radius: 100px
letter-spacing: 3px
text-transform: uppercase
```

### Source line (rodapé)
```
font-size: 26–28px
color: #636366
font-style: italic
display: flex + gap: 16px
flanqueado por linhas: width 40–50px, height 2px, background #E07B39
```

### Divider bar
```
height: 3–4px
background: #E07B39
border-radius: 2px
cresce de 0 → 100% via GSAP
```

---

## Layouts disponíveis

| ID | Variáveis | Uso |
|----|-----------|-----|
| `StatCard` | `stat, description, source, topic?` | Número/percentual impactante |
| `CircleStat` | `value, unit?, description, source, topic?` | Percentual em arco circular |
| `ComparisonBar` | `title, before{label,value}, after{label,value}, unit, source` | Comparativo antes/depois |
| `StudyQuote` | `quote, highlight, study, year, topic?` | Citação direta de estudo |
| `BenefitsList` | `title, items[{icon,text}], source?, topic?` | Lista de benefícios com emoji |
| `TimelineProgress` | `title, milestones[{label,value,description}], source?, topic?` | Progresso ao longo do tempo |
| `ScientificDefinition` | `term, pronunciation?, definition, analogy, topic?` | Definição de termo científico |

---

## Do's and Don'ts

### ✅ Fazer
- Sempre incluir cor `#E07B39` visível em todo slide (chip, divider, ou arco)
- Topic chip em ALL CAPS com letter-spacing
- Source em itálico com linhas flanqueando
- Hero numbers em weight 900, tracking negativo
- Background sempre `#FFF5ED` (nunca branco puro ou cinza)

### ❌ Não fazer
- `box-shadow` nos elementos principais
- Gradientes de fundo (causa banding em H.264)
- Cores inventadas fora da paleta
- Font weight < 500 em textos de vídeo
- Animations com `repeat: -1`
- Exit animations (exceto último slide)
- `Math.random()` ou `Date.now()` — composições devem ser determinísticas
