#!/usr/bin/env python3
"""
brand-catalog.py — 从 54 个 DESIGN.md 文提取品牌信息，生成 JSON 目录。

输出格式：紧凑 JSON 数组，每品牌包含：
  name, brand(dir), cat(category), style(描述), bg, ink, accent, font, img(截图URL)

用法：
  python3 brand-catalog.py           # 完整 JSON 目录
  python3 brand-catalog.py --list     # 仅品牌名列表
  python3 brand-catalog.py --names   # 仅品牌名（一行一个）
"""

import json
import re
import sys
from pathlib import Path

# ── 品牌分类映射 ──
CATEGORIES = {
    # AI & Machine Learning
    "claude": "AI & ML", "cohere": "AI & ML", "elevenlabs": "AI & ML",
    "minimax": "AI & ML", "mistral.ai": "AI & ML", "ollama": "AI & ML",
    "opencode.ai": "AI & ML", "replicate": "AI & ML", "runwayml": "AI & ML",
    "together.ai": "AI & ML", "voltagent": "AI & ML", "x.ai": "AI & ML",
    # Developer Tools & Platforms
    "cursor": "Developer", "expo": "Developer", "linear.app": "Developer",
    "lovable": "Developer", "mintlify": "Developer", "posthog": "Developer",
    "raycast": "Developer", "resend": "Developer", "sentry": "Developer",
    "supabase": "Developer", "superhuman": "Developer", "vercel": "Developer",
    "warp": "Developer", "zapier": "Developer",
    # Infrastructure & Cloud
    "clickhouse": "Infra", "composio": "Infra",
    "hashicorp": "Infra", "mongodb": "Infra", "sanity": "Infra",
    # Design & Productivity
    "airtable": "Design", "cal": "Design", "clay": "Design",
    "figma": "Design", "framer": "Design", "intercom": "Design",
    "miro": "Design", "notion": "Design", "pinterest": "Design",
    "webflow": "Design",
    # Fintech & Crypto
    "coinbase": "Fintech", "kraken": "Fintech",
    "revolut": "Fintech", "wise": "Fintech",
    # Enterprise & Consumer
    "airbnb": "Enterprise", "apple": "Enterprise", "bmw": "Enterprise",
    "ibm": "Enterprise", "nvidia": "Enterprise",
    "spacex": "Enterprise", "spotify": "Enterprise", "uber": "Enterprise",
    # Payments
    "stripe": "Payments",
}

# ── 品牌风格描述（取自 SKILL.md 别名表）──
STYLES = {
    "vercel": "白底黑字极简、Geist 字体、shadow-as-border",
    "stripe": "金融科技、紫色主色、蓝色阴影、weight-300 标题",
    "apple": "产品级摄影、SF Pro、黑白交替段落",
    "linear.app": "暗黑模式、Inter Variable 510、靛蓝点缀",
    "notion": "暖色极简、衬线标题、柔和表面",
    "spotify": "暗底亮绿、大胆排版、专辑封面驱动",
    "airbnb": "珊瑚色暖调、摄影驱动、圆润 UI",
    "uber": "黑白大胆、紧凑排版、都市能量",
    "figma": "多彩活力、专业而不失趣味",
    "framer": "黑蓝大胆、动效优先、设计导向",
    "raycast": "深色铬合金、渐变点缀",
    "supabase": "暗色翡翠、代码优先",
    "cursor": "深色渐变、AI 编辑器风格",
    "posthog": "俏刺猬品牌、开发者友好暗色 UI",
    "spacex": "纯黑电影级、全大写航空标注",
    "bmw": "深色高级表面、德国工程美学",
    "nvidia": "绿黑能量、技术力量感",
    "coinbase": "蓝色信任、机构级简洁",
    "revolut": "深色渐变卡片、金融科技精度",
    "wise": "亮绿清新、友好清晰",
    "miro": "黄色活力、无限画布",
    "intercom": "友好蓝色、对话式 UI",
    "webflow": "蓝色精修、营销网站美学",
    "mongodb": "绿叶品牌、开发者文档",
    "sentry": "暗色仪表板、粉紫点缀",
    "warp": "暗色 IDE、块式命令 UI",
    "cal": "中性简洁、开发者导向",
    "expo": "深色主题、紧凑字距、代码导向",
    "mintlify": "干净绿色、阅读优化",
    "lovable": "渐变趣味、友好开发者美学",
    "clickhouse": "黄色点缀、技术文档风格",
    "hashicorp": "企业级黑白",
    "ibm": "Carbon 设计系统、结构化蓝色",
    "pinterest": "红色点缀、瀑布流网格",
    "sanity": "红色点缀、内容优先",
    "airtable": "多彩友好、结构化数据",
    "zapier": "暖橙色、友好插图",
    "cohere": "渐变活力、数据丰富仪表板",
    "elevenlabs": "暗色电影、音频波形美学",
    "claude": "暖陶土点缀、干净编辑布局",
    "replicate": "白色画布、代码导向",
    "runwayml": "暗色电影、媒体丰富",
    "together.ai": "技术蓝图风格",
    "voltagent": "深黑画布、翡翠点缀",
    "x.ai": "极简单色、未来主义",
    "ollama": "终端优先、单色简洁",
    "opencode.ai": "开发者深色主题",
    "minimax": "大胆深色、霓虹点缀",
    "mistral.ai": "法式极简、紫色调",
    "kraken": "紫色暗色 UI、数据密集",
    "resend": "深色极简、等宽点缀",
    "clay": "有机形状、柔和渐变",
    "composio": "现代深色、多彩集成图标",
    "superhuman": "高级暗色 UI、键盘优先、紫色光晕",
}

# 截图 CDN 基础 URL
CDN_BASE = "https://pub-2e4ecbcbc9b24e7b93f1a6ab5b2bc71f.r2.dev/designs"

# ── 链接 get_brand_tokens.py 的提取逻辑（复用正则）──

# 语义匹配关键词 → token
SEMANTIC_MAP = {
    "CITY_BG":    ["background", "page bg", "canvas", "app bg", "main background"],
    "CITY_SURFACE": ["surface", "card bg", "elevated bg", "secondary bg"],
    "CITY_INK":     ["heading text", "primary text", "body text", "text", "text primary"],
    "CITY_MUTED":  ["body text", "secondary text", "description text", "muted", "secondary"],
    "CITY_ACCENT": ["cta", "primary brand", "link", "accent", "interactive", "brand"],
}


def extract_hex_from_line(line: str) -> list[str]:
    """从一行中提取所有 #hex 颜色值，返回列表。"""
    results = []
    # 格式: (`#hex`)
    for m in re.finditer(r"`(#[0-9a-fA-F]{3,8})`", line):
        results.append(m.group(1))
    # 格式: (`rgba(...)`)
    for m in re.finditer(r"`(rgba\([^)]+\))`", line):
        results.append(m.group(1))
    # 没有反引号包裹的 hex
    if not results:
        for m in re.finditer(r"(?:^|[\s:=])(#[0-9a-fA-F]{3,8})(?:$|[\s,;)])", line):
            results.append(m.group(1))
    return results


def extract_quick_colors(md_text: str) -> dict[str, str]:
    """从 Quick Color Reference section 提取颜色。"""
    result = {}
    lines = md_text.split("\n")

    in_qcr = False
    for i, line in enumerate(lines):
        if "Quick Color Reference" in line:
            in_qcr = True
            continue
        if in_qcr and line.startswith("##"):
            break
        if not in_qcr:
            continue

        line_stripped = line.strip()

        # 列表格式
        if line_stripped.startswith("-"):
            content = line_stripped.lstrip("- ").strip()
            colon_idx = content.find(":")
            if colon_idx > 0:
                desc_part = content[:colon_idx].strip().lower()
                colors = extract_hex_from_line(line_stripped)
                for token_name, keywords in SEMANTIC_MAP.items():
                    if token_name not in result:
                        for kw in keywords:
                            if kw in desc_part:
                                for c in colors:
                                    if c not in result.values():
                                        result[token_name] = c
                                        break
                                if token_name in result:
                                    break

        # 代码块格式
        elif re.match(r"^[A-Za-z]", line_stripped) and ":" in line_stripped:
            desc_part = line_stripped.split(":")[0].strip().lower()
            colors = extract_hex_from_line(line_stripped)
            for token_name, keywords in SEMANTIC_MAP.items():
                if token_name not in result:
                    for kw in keywords:
                        if kw in desc_part:
                            for c in colors:
                                if c not in result.values():
                                    result[token_name] = c
                                    break
                            if token_name in result:
                                break

    return result


def extract_font_family(md_text: str) -> str:
    """从 Section 3 Typography 提取主字体族名。"""
    lines = md_text.split("\n")
    in_typo = False
    for line in lines:
        if re.match(r"##\s*3\.", line):
            in_typo = True
            continue
        if in_typo and line.startswith("##"):
            break
        if not in_typo:
            continue
        # 匹配 "font-family: 'FontName'" 或 "Primary: FontName"
        m = re.search(r"(?:font-family|Primary|Display|Headline)[\s:]*['\"]?([A-Z][A-Za-z\s]+)['\"]?", line)
        if m:
            font = m.group(1).strip()
            if len(font) > 2 and font not in ("The", "Use", "For", "All"):
                return font
    return "system-ui"


def derive_missing_tokens(colors: dict[str, str]) -> dict[str, str]:
    """补全缺失的 token。"""
    bg = colors.get("CITY_BG", "#ffffff")
    ink = colors.get("CITY_INK")

    if "CITY_BG" not in colors:
        if ink:
            try:
                r, g, b = int(ink[1:3], 16), int(ink[3:5], 16), int(ink[5:7], 16)
                if (r * 299 + g * 587 + b * 114) / 1000 > 128:
                    colors["CITY_BG"] = "#000000"
                else:
                    colors["CITY_BG"] = "#ffffff"
            except (ValueError, IndexError):
                colors["CITY_BG"] = "#ffffff"
        else:
            colors["CITY_BG"] = "#ffffff"

    if "CITY_INK" not in colors:
        bg_val = colors.get("CITY_BG", "#ffffff")
        try:
            r, g, b = int(bg_val[1:3], 16), int(bg_val[3:5], 16), int(bg_val[5:7], 16)
            if (r * 299 + g * 587 + b * 114) / 1000 > 128:
                colors["CITY_INK"] = "#171717"
            else:
                colors["CITY_INK"] = "#f0f0f0"
        except (ValueError, IndexError):
            colors["CITY_INK"] = "#171717"

    if "CITY_SURFACE" not in colors:
        bg_val = colors.get("CITY_BG", "#ffffff")
        try:
            r, g, b = int(bg_val[1:3], 16), int(bg_val[3:5], 16), int(bg_val[5:7], 16)
            surface_r = min(255, r + 8)
            surface_g = min(255, g + 8)
            surface_b = min(255, b + 8)
            colors["CITY_SURFACE"] = f"#{surface_r:02x}{surface_g:02x}{surface_b:02x}"
        except (ValueError, IndexError):
            colors["CITY_SURFACE"] = bg_val

    if "CITY_MUTED" not in colors:
        ink_val = colors.get("CITY_INK", "#171717")
        bg_val = colors.get("CITY_BG", "#ffffff")
        colors["CITY_MUTED"] = "#888888"

    if "CITY_ACCENT" not in colors:
        colors["CITY_ACCENT"] = colors.get("CITY_INK", "#171717")

    return colors


def extract_brand_info(ref_dir: Path) -> dict | None:
    """从品牌目录提取完整信息。"""
    design_md = ref_dir / "DESIGN.md"
    if not design_md.exists():
        return None

    md_text = design_md.read_text(encoding="utf-8")
    dir_name = ref_dir.name

    # 提取颜色 token
    colors = extract_quick_colors(md_text)
    colors = derive_missing_tokens(colors)

    # 提取字体
    font = extract_font_family(md_text)

    # 截图 URL
    img = f"{CDN_BASE}/{dir_name}/preview-screenshot.png"

    return {
        "name": dir_name.replace(".app", "").replace(".ai", "").replace(".com", "").title(),
        "dir": dir_name,
        "cat": CATEGORIES.get(dir_name, "Other"),
        "style": STYLES.get(dir_name, ""),
        "bg": colors.get("CITY_BG", "#ffffff"),
        "ink": colors.get("CITY_INK", "#171717"),
        "accent": colors.get("CITY_ACCENT", "#0072f5"),
        "font": font,
        "img": img,
    }


def main():
    if "--list" in sys.argv:
        reference_dir = Path.home() / ".claude" / "skills" / "design-systems" / "reference"
        brands = []
        for d in sorted(reference_dir.iterdir()):
            if d.is_dir() and (d / "DESIGN.md").exists():
                brands.append(d.name)
        print(json.dumps(brands, ensure_ascii=False))
        return

    if "--names" in sys.argv:
        reference_dir = Path.home() / ".claude" / "skills" / "design-systems" / "reference"
        for d in sorted(reference_dir.iterdir()):
            if d.is_dir() and (d / "DESIGN.md").exists():
                print(d.name)
        return

    reference_dir = Path.home() / ".claude" / "skills" / "design-systems" / "reference"
    if not reference_dir.exists():
        print("[]", file=sys.stderr)
        sys.exit(1)

    brands = []
    for d in sorted(reference_dir.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "DESIGN.md").exists():
            continue
        info = extract_brand_info(d)
        if info:
            brands.append(info)

    print(json.dumps(brands, ensure_ascii=False))


if __name__ == "__main__":
    main()
