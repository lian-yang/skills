#!/usr/bin/env python3
"""
brand-catalog.py — 从 DESIGN.md 提取品牌信息，生成 JSON 目录。

数据源：
  - 品牌元数据（分类/风格/别名）：assets/brands-config.json
  - 设计 token（颜色/字体）：reference/{brand}/DESIGN.md

输出格式：紧凑 JSON 数组，每品牌包含：
  name, dir, cat, style, bg, ink, accent, font, img

用法：
  python3 brand-catalog.py           # 完整 JSON 目录
  python3 brand-catalog.py --list     # 仅品牌名 JSON 数组
  python3 brand-catalog.py --names   # 仅品牌名（一行一个）
"""

import json
import re
import sys
from pathlib import Path

# ── 路径解析 ──

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent
SKILL_DIR = ASSETS_DIR.parent  # design-systems/

# reference/ 目录：技能根目录 > .claude/skills > .agents/skills
_REFERENCE_CANDIDATES = [
    SKILL_DIR / "reference",
    Path.home() / ".claude" / "skills" / "design-systems" / "reference",
    Path.home() / ".agents" / "skills" / "design-systems" / "reference",
]


def _find_reference_dir() -> Path | None:
    for p in _REFERENCE_CANDIDATES:
        if p.exists() and p.is_dir():
            return p
    return None


# ── 配置加载 ──

def load_config() -> dict:
    """读取 brands-config.json，不存在则返回空配置。"""
    config_path = ASSETS_DIR / "brands-config.json"
    if config_path.exists():
        try:
            return json.loads(config_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"category_mapping": {}, "brands": {}}


def resolve_category(dir_name: str, config: dict) -> str:
    """从 config 解析品牌分类，fallback "Other"。"""
    brand = config.get("brands", {}).get(dir_name, {})
    cat = brand.get("category")
    if cat:
        return cat
    return "Other"


def resolve_style(dir_name: str, config: dict) -> str:
    """从 config 解析品牌风格描述，fallback ""。"""
    brand = config.get("brands", {}).get(dir_name, {})
    style = brand.get("style")
    if style:
        return style
    return ""


# ── 颜色提取 ──

CDN_BASE = "https://pub-2e4ecbcbc9b24e7b93f1a6ab5b2bc71f.r2.dev/designs"

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
    for m in re.finditer(r"`(#[0-9a-fA-F]{3,8})`", line):
        results.append(m.group(1))
    for m in re.finditer(r"`(rgba\([^)]+\))`", line):
        results.append(m.group(1))
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
        m = re.search(r"(?:font-family|Primary|Display|Headline)[\s:]*['\"]?([A-Z][A-Za-z\s]+)['\"]?", line)
        if m:
            font = m.group(1).strip()
            if len(font) > 2 and font not in ("The", "Use", "For", "All"):
                return font
    return "system-ui"


def derive_missing_tokens(colors: dict[str, str]) -> dict[str, str]:
    """补全缺失的 token。"""
    if "CITY_BG" not in colors:
        ink = colors.get("CITY_INK")
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
            colors["CITY_SURFACE"] = f"#{min(255,r+8):02x}{min(255,g+8):02x}{min(255,b+8):02x}"
        except (ValueError, IndexError):
            colors["CITY_SURFACE"] = bg_val

    if "CITY_MUTED" not in colors:
        colors["CITY_MUTED"] = "#888888"

    if "CITY_ACCENT" not in colors:
        colors["CITY_ACCENT"] = colors.get("CITY_INK", "#171717")

    return colors


# ── 品牌信息提取 ──

def extract_brand_info(ref_dir: Path, config: dict) -> dict | None:
    """从品牌目录提取完整信息。"""
    design_md = ref_dir / "DESIGN.md"
    if not design_md.exists():
        return None

    md_text = design_md.read_text(encoding="utf-8")
    dir_name = ref_dir.name

    colors = extract_quick_colors(md_text)
    colors = derive_missing_tokens(colors)

    font = extract_font_family(md_text)
    img = f"{CDN_BASE}/{dir_name}/preview-screenshot.png"

    return {
        "name": dir_name.replace(".app", "").replace(".ai", "").replace(".com", "").title(),
        "dir": dir_name,
        "cat": resolve_category(dir_name, config),
        "style": resolve_style(dir_name, config),
        "bg": colors.get("CITY_BG", "#ffffff"),
        "ink": colors.get("CITY_INK", "#171717"),
        "accent": colors.get("CITY_ACCENT", "#0072f5"),
        "font": font,
        "img": img,
    }


# ── 主入口 ──

def main():
    reference_dir = _find_reference_dir()
    if not reference_dir:
        print("[]", file=sys.stderr)
        print("Error: reference/ directory not found", file=sys.stderr)
        sys.exit(1)

    config = load_config()

    if "--list" in sys.argv:
        brands = []
        for d in sorted(reference_dir.iterdir()):
            if d.is_dir() and (d / "DESIGN.md").exists():
                brands.append(d.name)
        print(json.dumps(brands, ensure_ascii=False))
        return

    if "--names" in sys.argv:
        for d in sorted(reference_dir.iterdir()):
            if d.is_dir() and (d / "DESIGN.md").exists():
                print(d.name)
        return

    brands = []
    for d in sorted(reference_dir.iterdir()):
        if not d.is_dir():
            continue
        if not (d / "DESIGN.md").exists():
            continue
        info = extract_brand_info(d, config)
        if info:
            brands.append(info)

    print(json.dumps(brands, ensure_ascii=False))


if __name__ == "__main__":
    main()
