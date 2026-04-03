---
name: design-systems
description: >-
  Apply world-class design systems (Vercel, Stripe, Apple, Linear, etc.) to UI code generation.
  50+ curated DESIGN.md files extracted from real websites, covering color, typography, components,
  shadows, spacing, and agent-ready prompt guides. Use when: user says "像 Vercel 风格", "Stripe 风格",
  "make it look like Apple/Linear/Notion", "apply design system", "use design-md", "design system",
  "设计系统", "配色方案", "设计风格". Triggers on brand names: vercel, stripe, apple, linear, notion,
  spotify, airbnb, uber, figma, framer, raycast, supabase, cursor, posthog, spacex, bmw, nvidia,
  coinbase, revolut, wise, miro, intercom, webflow, mongodb, sentry, warp, cal, expo, mintlify,
  lovable, clickhouse, hashicorp, ibm, pinterest, sanity, airtable, zapier, cohere, elevenlabs,
  claude, replicate, runwayml, together.ai, voltagent, xai, ollama, opencode, minimax, mistral,
  kraken, resend, clay, composio, superhuman, spotify.
---

# Design Systems Reference

## Philosophy

This skill applies **brand-faithful design tokens** — not generic CSS. Every output should feel like the target brand's own design team built it:

- **Token 级精度** — Colors are hex-exact, typography matches the brand's actual font stack and weight system, shadows reproduce the brand's elevation model exactly.
- **Do's and Don'ts 是护栏** — Each DESIGN.md 的 Do/Don't 部分是红线。违反 = 不像目标品牌。没有例外。
- **交互式选择优先** — 50+ 个品牌不是一个静态列表。用浏览器交互预览让用户"看到"风格再决定，不是盲选。
- **混合时保持品牌灵魂** — Blend 多个设计系统时，每个系统的核心识别元素（字体、主色、阴影模式）至少保留一个。

---

## Bundled Assets (USE THESE — do not reinvent)

| File | What's in it | When to use |
|------|-------------|-------------|
| `reference/{brand}/DESIGN.md` | 9-section 完整设计规范 | Step 4: 读取目标品牌的全量设计 token |
| `reference/{brand}/preview.html` | 亮色模式组件可视化目录 | Step 3: 用户想看完整组件库时打开 |
| `reference/{brand}/preview-dark.html` | 暗色模式组件可视化目录 | Step 3: 暗色项目打开此文件 |
| `assets/brand-preview-template.html` | 50+ 品牌交互式选择卡片 | Step 2: 品牌选择浏览器预览 |
| `assets/scripts/brand-catalog.py` | 从 DESIGN.md 提取品牌 JSON 目录 | Step 2: 生成品牌预览的数据源 |
| `assets/scripts/run_brand_preview.py` | 启动品牌选择浏览器预览 | Step 2: 打开交互式预览 |

**The quality guarantee of this skill comes from using these assets.** DESIGN.md 文件包含从真实网站提取的精确设计 token。不要凭记忆猜测品牌颜色——总是从文件读取。

---

## The Workflow

### Step 1: Understand the Project

Use `AskUserQuestion` to ask:

> "告诉我你的项目是关于什么的——产品/项目名称，以及一句话描述你想要的视觉风格感觉。比如'给开发者用的命令行工具，想要极简科技感'或'面向设计师的作品展示，想要大胆有冲击力'。如果你已经知道要用哪个品牌风格，直接告诉我品牌名就行。"

Wait for the answer before proceeding.

**If the user already specified a brand name** (e.g., "用 Vercel 风格", "make it look like Stripe"): skip to Step 4 directly, using the Brand Name Alias Map below to resolve the directory name.

**If the user gave a description but no brand**: proceed to Step 2.

### Step 2: Brand Selection Preview

Open the interactive 50+-brand browser preview. This is the primary flow — not a fallback.

```bash
_SKILL_DIR=$(ls -d ~/.agents/skills/design-systems 2>/dev/null || ls -d ~/.claude/skills/design-systems 2>/dev/null)
PYTHON=$(command -v python3 2>/dev/null || command -v python 2>/dev/null || echo "")
if [ -n "$PYTHON" ]; then
  "$PYTHON" "$_SKILL_DIR/assets/scripts/run_brand_preview.py" \
    --template "$_SKILL_DIR/assets/brand-preview-template.html" \
    --output   ./brand-preview.html \
    --port     17435 \
    --timeout  300 \
    "LANG=zh"
else
  CATALOG=$("$PYTHON" "$_SKILL_DIR/assets/scripts/brand-catalog.py")
  sed "s/__LANG__/zh/g; s/__RECEIVER_PORT__/17435/g; s/'__BRANDS_JSON__'/'$CATALOG'/g" \
    "$_SKILL_DIR/assets/brand-preview-template.html" > ./brand-preview.html
  open ./brand-preview.html 2>/dev/null || xdg-open ./brand-preview.html 2>/dev/null
  echo "Python not found — 无实时桥接。点击卡片后用复制按钮粘贴结果。"
fi
```

Tell the user: "我在浏览器里打开了 50+ 种品牌设计风格的预览卡片——从 Vercel 的极简黑白到 Spotify 的大胆暗色，从 Stripe 的金融科技到 SpaceX 的电影级纯黑。每张卡片都展示了真实的组件截图和配色方案。可以用顶部的类别筛选（AI & ML / Developer / Fintech 等），选好之后直接点卡片再点底部的「告诉 Agent →」按钮。如果不确定选什么，也可以告诉我你的项目类型，我帮你推荐。"

**2a — 用户选择后**

脚本打印 JSON（如 `{"brand":"Stripe","dir":"stripe"}`），或用户粘贴 JSON/品牌名。继续到 Step 4 读取该品牌的 DESIGN.md。

**2b — "让 AI 来选" 选项**

当用户说"你帮我选"、"不确定"、"推荐一个"、"你看着办"、"AI choose"时：

1. 根据用户在 Step 1 描述的项目类型、目标受众、行业，匹配最合适的品牌
2. 参考 Design System Categories 做行业匹配
3. 用 2-3 句话解释推荐理由
4. 确认："我为你推荐 [品牌]——[理由]。可以打开预览确认，或者直接继续？"
5. 如果用户确认，继续到 Step 3

**AI 推荐决策矩阵：**

| 项目类型 | 推荐品牌 | 理由 |
|----------|----------|------|
| 开发者工具/SaaS | Vercel, Linear.app, Raycast | 暗色科技、极简、开发者信任 |
| 金融科技/支付 | Stripe, Coinbase, Revolut | 机构级信任感、精准阴影系统 |
| AI/ML 产品 | Claude, Cursor, Together.ai | 前沿科技感、深色主题 |
| 内容/文档 | Notion, Mintlify, Sanity | 阅读优化、暖色友好 |
| 设计/创意工具 | Figma, Framer, Clay | 活力多彩、专业趣味 |
| 企业/B2B | IBM, HashiCorp, Webflow | 结构化、可信、专业 |
| C2C/共享经济 | Airbnb, Uber, Spotify | 大胆情感、摄影驱动 |
| 数据密集/分析 | ClickHouse, PostHog, Sentry | 暗色仪表板、数据优先 |
| 通信/消息 | Intercom, Resend, Superhuman | 干净高效、键盘优先 |
| 基础设施/云 | Supabase, MongoDB, Expo | 代码导向、文档级精度 |

### Step 3: Brand Detail Preview (Optional)

用户想看某个品牌的完整组件目录时，打开其 preview.html：

```bash
open "$_SKILL_DIR/reference/{dir}/preview.html"
```

Tell the user: "已打开 {brand} 的完整组件目录——包含颜色、字体、按钮、卡片、输入框等所有设计 token 的可视化预览。你可以对照确认风格。"

如果项目需要暗色模式，打开 `preview-dark.html`：
```bash
open "$_SKILL_DIR/reference/{dir}/preview-dark.html"
```

### Step 4: Read the DESIGN.md

```
Read: ~/.claude/skills/design-systems/reference/{directory}/DESIGN.md
```

Read the full DESIGN.md file to get the complete design specification including:
1. Visual Theme & Atmosphere — 情绪、密度、设计哲学
2. Color Palette & Roles — 语义颜色名 + hex + 功能角色
3. Typography Rules — 字体族、完整层级表
4. Component Stylings — 按钮、卡片、输入框、导航及状态
5. Layout Principles — 间距系统、网格、留白哲学
6. Depth & Elevation — 阴影系统、表面层级
7. Do's and Don'ts — 设计护栏和反模式
8. Responsive Behavior — 断点、触控目标、折叠策略
9. Agent Prompt Guide — 快速颜色参考、现成提示词

### Step 5: Apply the Design System

When generating code based on a DESIGN.md:

1. **提取关键设计 token** — 颜色 hex 值、字体栈、间距值、圆角值
2. **遵循 Do's and Don'ts** — 这是最关键的护栏，违反 = 不像目标品牌
3. **使用 Agent Prompt Guide** — 直接复制 Example Component Prompts 作为代码模板
4. **严格遵循字体规则** — 字体族 + 字重 + 字距是品牌识别的灵魂
5. **深度系统** — 阴影/边框处理方式决定了视觉品质感

---

## Brand Name Alias Map

When the user mentions a brand name or design style, map it to the correct directory:

| Alias | Directory | Style Category |
|-------|-----------|----------------|
| vercel | vercel | 白底黑字极简、Geist 字体、shadow-as-border |
| stripe | stripe | 金融科技、紫色主色、蓝色阴影、weight-300 标题 |
| apple | apple | 产品级摄影、SF Pro、黑白交替段落 |
| linear, linear.app | linear.app | 暗黑模式、Inter Variable 510、靛蓝点缀 |
| notion | notion | 暖色极简、衬线标题、柔和表面 |
| spotify | spotify | 暗底亮绿、大胆排版、专辑封面驱动 |
| airbnb | airbnb | 珊瑚色暖调、摄影驱动、圆润 UI |
| uber | uber | 黑白大胆、紧凑排版、都市能量 |
| figma | figma | 多彩活力、专业而不失趣味 |
| framer | framer | 黑蓝大胆、动效优先、设计导向 |
| raycast | raycast | 深色铬合金、渐变点缀 |
| supabase | supabase | 暗色翡翠、代码优先 |
| cursor | cursor | 深色渐变、AI 编辑器风格 |
| posthog | posthog | 俏刺猬品牌、开发者友好暗色 UI |
| spacex | spacex | 纯黑电影级、全大写航空标注 |
| bmw | bmw | 深色高级表面、德国工程美学 |
| nvidia | nvidia | 绿黑能量、技术力量感 |
| coinbase | coinbase | 蓝色信任、机构级简洁 |
| revolut | revolut | 深色渐变卡片、金融科技精度 |
| wise | wise | 亮绿清新、友好清晰 |
| miro | miro | 黄色活力、无限画布 |
| intercom | intercom | 友好蓝色、对话式 UI |
| webflow | webflow | 蓝色精修、营销网站美学 |
| mongodb | mongodb | 绿叶品牌、开发者文档 |
| sentry | sentry | 暗色仪表板、粉紫点缀 |
| warp | warp | 暗色 IDE、块式命令 UI |
| cal, cal.com | cal | 中性简洁、开发者导向 |
| expo | expo | 深色主题、紧凑字距、代码导向 |
| mintlify | mintlify | 干净绿色、阅读优化 |
| lovable | lovable | 渐变趣味、友好开发者美学 |
| clickhouse | clickhouse | 黄色点缀、技术文档风格 |
| hashicorp | hashicorp | 企业级黑白 |
| ibm | ibm | Carbon 设计系统、结构化蓝色 |
| pinterest | pinterest | 红色点缀、瀑布流网格 |
| sanity | sanity | 红色点缀、内容优先 |
| airtable | airtable | 多彩友好、结构化数据 |
| zapier | zapier | 暖橙色、友好插图 |
| cohere | cohere | 渐变活力、数据丰富仪表板 |
| elevenlabs | elevenlabs | 暗色电影、音频波形美学 |
| claude, anthropic | claude | 暖陶土点缀、干净编辑布局 |
| replicate | replicate | 白色画布、代码导向 |
| runwayml | runwayml | 暗色电影、媒体丰富 |
| together.ai | together.ai | 技术蓝图风格 |
| voltagent | voltagent | 深黑画布、翡翠点缀 |
| xai, x.ai, grok | x.ai | 极简单色、未来主义 |
| ollama | ollama | 终端优先、单色简洁 |
| opencode, opencode.ai | opencode.ai | 开发者深色主题 |
| minimax | minimax | 大胆深色、霓虹点缀 |
| mistral, mistral.ai | mistral.ai | 法式极简、紫色调 |
| kraken | kraken | 紫色暗色 UI、数据密集 |
| resend | resend | 深色极简、等宽点缀 |
| clay | clay | 有机形状、柔和渐变 |
| composio | composio | 现代深色、多彩集成图标 |
| superhuman | superhuman | 高级暗色 UI、键盘优先、紫色光晕 |

---

## Design System Categories

### AI & Machine Learning
claude, cohere, elevenlabs, minimax, mistral.ai, ollama, opencode.ai, replicate, runwayml, together.ai, voltagent, x.ai

### Developer Tools & Platforms
cursor, expo, linear.app, lovable, mintlify, posthog, raycast, resend, sentry, supabase, superhuman, vercel, warp, zapier

### Infrastructure & Cloud
clickhouse, composio, hashicorp, mongodb, sanity

### Design & Productivity
airtable, cal, clay, figma, framer, intercom, miro, notion, pinterest, webflow

### Fintech & Crypto
coinbase, kraken, revolut, wise

### Enterprise & Consumer
airbnb, apple, bmw, ibm, nvidia, spacex, spotify, uber

### Payments
stripe

---

## Design Laws (Never Break These)

1. **永远从 DESIGN.md 读取 token。** 不要凭记忆猜测品牌颜色。每个品牌有精确的 hex 值、字体栈和阴影系统——它们是品牌识别的 DNA。
2. **Do's and Don'ts 是红线。** 每个 DESIGN.md 的第 7 节是设计护栏。违反 = 不像目标品牌。没有例外。
3. **字体是品牌灵魂。** 字体族 + 字重 + 字距的组合定义了品牌的视觉声音。Inter Variable 在 weight 510 跟 400 完全是两个品牌。
4. **阴影系统决定品质感。** Vercel 的 shadow-as-border、Stripe 的蓝色多层阴影、Linear 的半透明边框——每个品牌的深度系统都有独特签名。
5. **不混合互斥的设计 DNA。** 如果两个品牌的核心识别冲突（比如 Vercel 的极简白底 vs SpaceX 的纯黑电影级），blend 时只保留一个作为底色系统，另一个贡献点缀元素。
6. **不使用 placeholder 文案。** 应用设计系统时生成的 UI 必须有真实内容——不是 Lorem ipsum，不是 "Your text here"。内容要匹配品牌的调性。
7. **暗色/亮色模式必须完整。** 如果目标品牌有 dark mode 设计 token，应用时必须完整实现——不只是反转颜色，而是使用该品牌特定的暗色色板和对比度系统。

---

## Syncing from Upstream

上游仓库 [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md) 持续新增品牌。同步到本地：

```bash
_SKILL_DIR=$(ls -d ~/.claude/skills/design-systems 2>/dev/null || ls -d ~/.agents/skills/design-systems 2>/dev/null || echo ".")

# 预览变更（不修改文件）
python3 "$_SKILL_DIR/assets/scripts/sync_upstream.py" --dry-run

# 执行同步
python3 "$_SKILL_DIR/assets/scripts/sync_upstream.py"

# 同时更新已有品牌的文件（上游有更新时）
python3 "$_SKILL_DIR/assets/scripts/sync_upstream.py" --update-existing

# 查看当前同步状态
python3 "$_SKILL_DIR/assets/scripts/sync_upstream.py" --status
```

同步后：
1. 新品牌的 4 个文件（DESIGN.md / README.md / preview.html / preview-dark.html）已复制到 `reference/`
2. `brands-config.json` 已自动更新（分类、风格、别名）
3. `brand-catalog.py` 下次运行自动读取新数据，无需改代码
4. 需手动更新本文件的 Design System Categories 列表和 Brand Name Alias Map

---

## Multi-System Blending

When the user wants to blend multiple design systems (e.g., "Vercel 的排版 + Stripe 的配色"):

1. Read both DESIGN.md files
2. 从第一个系统取排版和布局 token
3. 从第二个系统取颜色和组件 token
4. **Never violate Do's and Don'ts from either system**
5. Document the blend decision in code comments

---

## Quick Reference: Common Patterns

### Shadow-as-Border (Vercel Pattern)
```css
border: none;
box-shadow: rgba(0, 0, 0, 0.08) 0px 0px 0px 1px;
```

### Blue-Tinted Multi-Layer Shadow (Stripe Pattern)
```css
box-shadow:
  rgba(50,50,93,0.25) 0px 30px 45px -30px,
  rgba(0,0,0,0.1) 0px 18px 36px -18px;
```

### Semi-Transparent Dark Borders (Linear Pattern)
```css
border: 1px solid rgba(255,255,255,0.08);
background: rgba(255,255,255,0.02);
```

### Aggressive Negative Letter-Spacing (Vercel/Linear Pattern)
```css
/* Display 48px */
letter-spacing: -2.4px;
/* Heading 32px */
letter-spacing: -1.28px;
/* Body 16px */
letter-spacing: normal;
```

### Light-Weight Headlines (Stripe Pattern)
```css
/* Weight 300 at display sizes — whisper authority */
font-weight: 300;
```

---

## Citycraft Integration

Citycraft 落地页工作流可直接使用 design-systems 的品牌 token。运行：

```bash
python3 ~/.claude/skills/citycraft/assets/scripts/get_brand_tokens.py <brand-name>
```

输出 Citycraft 兼容的 5 个颜色 token（`CITY_BG`, `CITY_SURFACE`, `CITY_INK`, `CITY_MUTED`, `CITY_ACCENT`），与城市风格的输出格式完全一致。支持 `--dark` 提取暗色模式 token，`--list` 列出所有可用品牌。

当用户说"用 Vercel/Stripe/Apple 风格做个落地页"时，Citycraft 会自动检测品牌名、提取 token、跳过城市选择直接进入布局选项。详见 `~/.claude/skills/citycraft/SKILL.md` Step 1.5。
