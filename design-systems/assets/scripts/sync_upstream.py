#!/usr/bin/env python3
"""
sync_upstream.py — 从 VoltAgent/awesome-design-md 同步新增设计系统到本地。

流程：
  1. 定位/克隆上游仓库
  2. 对比上游 design-md/ 与本地 reference/ 目录差异
  3. 复制新品牌的 4 个文件（DESIGN.md, README.md, preview.html, preview-dark.html）
  4. 从上游 README 提取分类和风格描述
  5. 更新 brands-config.json

用法：
  python3 sync_upstream.py                    # 完整同步
  python3 sync_upstream.py --dry-run          # 预览，不修改
  python3 sync_upstream.py --offline          # 仅用本地缓存
  python3 sync_upstream.py --update-existing  # 同时更新已有品牌文件
  python3 sync_upstream.py --status           # 查看当前同步状态
"""

import hashlib
import json
import re
import shutil
import sys
from datetime import datetime, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
ASSETS_DIR = SCRIPT_DIR.parent
SKILL_DIR = ASSETS_DIR.parent
REFERENCE_DIR = SKILL_DIR / "reference"
CONFIG_PATH = ASSETS_DIR / "brands-config.json"

UPSTREAM_REPO = "VoltAgent/awesome-design-md"
UPSTREAM_BRANCH = "main"
CACHE_DIR = Path.home() / ".cache" / "design-systems" / "awesome-design-md"

BRAND_FILES = ["DESIGN.md", "README.md", "preview.html", "preview-dark.html"]


# ── Git 操作 ──

def locate_or_clone_upstream(offline: bool = False) -> Path:
    """返回上游仓库 design-md/ 路径。"""
    if CACHE_DIR.exists():
        if not offline:
            print(f"  → git pull ({CACHE_DIR})")
            import subprocess
            subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=CACHE_DIR,
                capture_output=True,
                text=True,
            )
        return CACHE_DIR / "design-md"

    if offline:
        print(
            f"Error: 本地缓存不存在 ({CACHE_DIR})，去掉 --offline 后重试",
            file=sys.stderr,
        )
        sys.exit(1)

    import subprocess

    print(f"  → git clone {UPSTREAM_REPO}")
    CACHE_DIR.parent.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        ["git", "clone", "--depth", "1", f"https://github.com/{UPSTREAM_REPO}.git", str(CACHE_DIR)],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(f"Error: git clone 失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    return CACHE_DIR / "design-md"


# ── 上游 README 解析 ──

def parse_upstream_readme(readme_path: Path) -> dict[str, dict]:
    """解析上游 README.md，提取品牌分类和风格描述。

    返回: {dir_name: {"category": str, "style": str, "display_name": str}}
    """
    if not readme_path.exists():
        return {}

    text = readme_path.read_text(encoding="utf-8")
    result: dict[str, dict] = {}
    current_category = ""

    for line in text.split("\n"):
        stripped = line.strip()

        cat_m = re.match(r"^###\s+(.+)$", stripped)
        if cat_m:
            current_category = cat_m.group(1).strip()
            continue

        # - **Vercel** - Frontend deployment platform. Black and white precision
        # - [**Vercel**](.../design-md/vercel/) - Description
        brand_m = re.match(
            r"-\s+(?:\[)?\*\*(.+?)\*\*(?:\])?"
            r"(?:\([^)]*?/design-md/([^/]+)/?\))?"
            r"\s*[-\u2013\u2014]\s*(.+)",
            stripped,
        )
        if not brand_m:
            continue

        display_name = brand_m.group(1).strip()
        dir_name = brand_m.group(2) or display_name.lower().replace(" ", "-")
        description = brand_m.group(3).strip()

        # 句号后为风格描述
        parts = description.split(".", 1)
        style = parts[1].strip() if len(parts) > 1 and parts[1].strip() else description

        result[dir_name] = {
            "category": current_category,
            "style": style,
            "display_name": display_name,
        }

    return result


# ── 配置操作 ──

def load_config() -> dict:
    """读取 brands-config.json。"""
    if CONFIG_PATH.exists():
        try:
            return json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            pass
    return {"_meta": {"version": 1}, "category_mapping": {}, "brands": {}}


def save_config(config: dict) -> None:
    """原子写入 brands-config.json。"""
    tmp = CONFIG_PATH.with_suffix(".tmp")
    tmp.write_text(json.dumps(config, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    tmp.rename(CONFIG_PATH)


def resolve_category(upstream_cat: str, dir_name: str, config: dict) -> str:
    """上游分类 → 本地分类名。"""
    brands = config.get("brands", {})
    brand = brands.get(dir_name, {})

    # 1. 本地 override
    override = brand.get("category_override") or brand.get("category")
    if override:
        return override

    # 2. category_mapping
    mapping = config.get("category_mapping", {})
    if upstream_cat in mapping:
        return mapping[upstream_cat]

    return upstream_cat or "Other"


def resolve_style(dir_name: str, upstream_info: dict, config: dict) -> str:
    """获取品牌风格描述。"""
    brand = config.get("brands", {}).get(dir_name, {})
    override = brand.get("style_override") or brand.get("style")
    if override:
        return override
    return upstream_info.get("style", "")


# ── 文件操作 ──

def file_hash(path: Path) -> str:
    """文件内容 SHA256 前 16 位。"""
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def copy_brand_files(src_dir: Path, dest_dir: Path) -> list[str]:
    """复制品牌 4 个文件。返回复制的文件名列表。"""
    copied: list[str] = []
    dest_dir.mkdir(parents=True, exist_ok=True)
    for fname in BRAND_FILES:
        src = src_dir / fname
        if src.exists():
            shutil.copy2(src, dest_dir / fname)
            copied.append(fname)
    return copied


# ── 同步逻辑 ──

def do_sync(dry_run: bool, offline: bool, update_existing: bool) -> None:
    upstream_dir = locate_or_clone_upstream(offline)
    readme_path = CACHE_DIR / "README.md"

    if not upstream_dir.exists():
        print(f"Error: 上游 design-md/ 不存在: {upstream_dir}", file=sys.stderr)
        sys.exit(1)

    upstream_info = parse_upstream_readme(readme_path)
    print(f"  上游 README 解析到 {len(upstream_info)} 个品牌")

    upstream_dirs = {d.name for d in upstream_dir.iterdir() if d.is_dir() and (d / "DESIGN.md").exists()}
    local_dirs = (
        {d.name for d in REFERENCE_DIR.iterdir() if d.is_dir() and (d / "DESIGN.md").exists()}
        if REFERENCE_DIR.exists()
        else set()
    )

    new_dirs = sorted(upstream_dirs - local_dirs)
    existing_dirs = sorted(upstream_dirs & local_dirs)
    local_only = sorted(local_dirs - upstream_dirs)

    config = load_config()
    brands_config = config.get("brands", {})

    # NEW 品牌
    if new_dirs:
        print(f"\n✨ 发现 {len(new_dirs)} 个新品牌:")
        for dir_name in new_dirs:
            info = upstream_info.get(dir_name, {})
            cat = resolve_category(info.get("category", ""), dir_name, config)
            style = resolve_style(dir_name, info, config)

            display = info.get("display_name", dir_name)
            print(f"  + {dir_name}  [{cat}]  {display} — {style}")

            if not dry_run:
                copied = copy_brand_files(upstream_dir / dir_name, REFERENCE_DIR / dir_name)
                print(f"    复制了 {len(copied)} 个文件")

                base_name = dir_name.replace(".app", "").replace(".ai", "").replace(".com", "")
                brands_config[dir_name] = {
                    "category": cat,
                    "style": style,
                    "aliases": [base_name],
                }
    else:
        print("\n  无新品牌")

    # EXISTING 更新
    if update_existing and existing_dirs:
        updated: list[tuple[str, list[str]]] = []
        for dir_name in existing_dirs:
            changed: list[str] = []
            for fname in BRAND_FILES:
                src = upstream_dir / dir_name / fname
                dst = REFERENCE_DIR / dir_name / fname
                if src.exists() and dst.exists() and file_hash(src) != file_hash(dst):
                    changed.append(fname)
            if changed:
                updated.append((dir_name, changed))
                if not dry_run:
                    for fname in changed:
                        shutil.copy2(upstream_dir / dir_name / fname, REFERENCE_DIR / dir_name / fname)

        if updated:
            print(f"\n📝 更新了 {len(updated)} 个品牌:")
            for dn, ch in updated:
                print(f"  ~ {dn}: {', '.join(ch)}")
        else:
            print("\n  所有已有品牌均为最新")

    # LOCAL_ONLY 报告
    if local_only:
        print(f"\n⚠️  {len(local_only)} 个本地独有品牌（上游已移除或本地新增）:")
        for dn in local_only:
            print(f"  ? {dn}")

    # 写回 config
    if not dry_run and (new_dirs or (update_existing and existing_dirs)):
        config["brands"] = brands_config
        config["_meta"]["last_synced"] = datetime.now(timezone.utc).isoformat()
        config["_meta"]["total_brands"] = len(brands_config)
        save_config(config)
        print(f"\n✅ brands-config.json 已更新 ({len(brands_config)} 个品牌)")
    elif new_dirs:
        print("\n  [DRY RUN] 未修改任何文件")


def do_status() -> None:
    config = load_config()
    meta = config.get("_meta", {})

    print("Design Systems 同步状态")
    print("━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"  本地品牌数: {meta.get('total_brands', 'unknown')}")
    print(f"  上游仓库: {meta.get('upstream_repo', UPSTREAM_REPO)}")
    print(f"  上游分支: {meta.get('upstream_branch', UPSTREAM_BRANCH)}")
    print(f"  上次同步: {meta.get('last_synced', '从未同步')}")

    if REFERENCE_DIR.exists():
        count = sum(1 for d in REFERENCE_DIR.iterdir() if d.is_dir() and (d / "DESIGN.md").exists())
        print(f"  reference/ 实际: {count} 个品牌")

    if CACHE_DIR.exists():
        print(f"  缓存目录: {CACHE_DIR} ✓")
    else:
        print("  缓存目录: 未克隆")


def main() -> None:
    args = set(sys.argv[1:])

    if "--status" in args:
        do_status()
        return

    dry_run = "--dry-run" in args
    offline = "--offline" in args
    update_existing = "--update-existing" in args

    print(f"🔄 同步上游 {UPSTREAM_REPO}" + (" [DRY RUN]" if dry_run else ""))
    do_sync(dry_run=dry_run, offline=offline, update_existing=update_existing)


if __name__ == "__main__":
    main()
