# Design Systems Skill

从真实生产网站提取的 54 份设计系统文档，用于 AI agent 生成像素级精准的 UI 代码。

## 数据来源

上游仓库: [VoltAgent/awesome-design-md](https://github.com/VoltAgent/awesome-design-md)

每份设计系统遵循标准化 9 节格式:

| # | Section | 内容 |
|---|---------|------|
| 1 | Visual Theme & Atmosphere | 情绪、密度、设计哲学 |
| 2 | Color Palette & Roles | 语义颜色名 + hex + 功能角色 |
| 3 | Typography Rules | 字体族、完整层级表 |
| 4 | Component Stylings | 按钮、卡片、输入框、导航及状态 |
| 5 | Layout Principles | 间距系统、网格、留白哲学 |
| 6 | Depth & Elevation | 阴影系统、表面层级 |
| 7 | Do's and Don'ts | 设计护栏和反模式 |
| 8 | Responsive Behavior | 断点、触控目标、折叠策略 |
| 9 | Agent Prompt Guide | 快速颜色参考、现成提示词 |

## 目录结构

```
design-systems/
├── SKILL.md                        # 技能定义和工作流
├── README.md                       # 本文件
├── assets/
│   ├── brands-config.json          # 品牌元数据（分类/风格/别名）
│   ├── brand-preview-template.html # 交互式品牌选择 UI
│   └── scripts/
│       ├── brand-catalog.py        # 从 DESIGN.md 提取品牌 JSON 目录
│       ├── run_brand_preview.py    # 启动浏览器预览
│       └── sync_upstream.py        # 上游同步脚本
└── reference/                      # 54 个品牌目录
    ├── vercel/
    │   ├── DESIGN.md               # 设计系统规范
    │   ├── README.md               # 品牌元信息
    │   ├── preview.html            # 亮色模式组件预览
    │   └── preview-dark.html       # 暗色模式组件预览
    ├── stripe/
    ├── apple/
    └── ...
```

## 收录品牌

### Developer Tools (14)
Cursor, Expo, Linear, Lovable, Mintlify, PostHog, Raycast, Resend, Sentry, Supabase, Superhuman, Vercel, Warp, Zapier

### AI & Machine Learning (12)
Claude, Cohere, ElevenLabs, Minimax, Mistral AI, Ollama, OpenCode AI, Replicate, RunwayML, Together AI, VoltAgent, xAI

### Design & Productivity (10)
Airtable, Cal, Clay, Figma, Framer, Intercom, Miro, Notion, Pinterest, Webflow

### Enterprise & Consumer (8)
Airbnb, Apple, BMW, IBM, NVIDIA, SpaceX, Spotify, Uber

### Infrastructure & Cloud (5)
ClickHouse, Composio, HashiCorp, MongoDB, Sanity

### Fintech & Crypto (4)
Coinbase, Kraken, Revolut, Wise

### Payments (1)
Stripe

## 从上游同步新增品牌

```bash
# 预览变更
python3 assets/scripts/sync_upstream.py --dry-run

# 执行同步
python3 assets/scripts/sync_upstream.py

# 查看状态
python3 assets/scripts/sync_upstream.py --status
```

同步脚本会自动:
1. clone/pull 上游仓库到 `~/.cache/design-systems/`
2. 对比上游 `design-md/` 与本地 `reference/` 的差异
3. 复制新品牌的 4 个文件到 `reference/`
4. 从上游 README 解析分类和风格描述
5. 更新 `brands-config.json`

## 快速参考

```bash
# 生成品牌 JSON 目录
python3 assets/scripts/brand-catalog.py

# 列出所有品牌名
python3 assets/scripts/brand-catalog.py --names
```
