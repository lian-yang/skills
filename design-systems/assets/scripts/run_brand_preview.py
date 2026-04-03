#!/usr/bin/env python3
"""
run_brand_preview.py — 启动品牌设计风格浏览器预览。

流程：
  1. 调用 brand-catalog.py 生成 JSON 目录
  2. 将 JSON 写入临时文件
  3. 读取模板，替换占位符
  4. 启动浏览器预览

用法：
  python3 run_brand_preview.py --template TEMPLATE --output OUTPUT [--port PORT] [--timeout SEC] "LANG=zh" "BRANDS_JSON=auto"
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent
DESIGN_SYSTEMS_DIR = SCRIPT_DIR.parent.parent  # ~/.claude/skills/design-systems


def main():
    parser = argparse.ArgumentParser(description="品牌设计风格浏览器预览")
    parser.add_argument("--template", required=True, help="模板 HTML 文件路径")
    parser.add_argument("--output", required=True, help="输出 HTML 文件路径")
    parser.add_argument("--port", type=int, default=17435, help="HTTP 端口 (默认 17435)")
    parser.add_argument("--timeout", type=int, default=300, help="超时秒数 (默认 300)")
    parser.add_argument("vars", nargs="*", help="变量替换 KEY=VALUE 对")
    args = parser.parse_args()

    # 1. 生成品牌 JSON 目录
    catalog_script = SCRIPT_DIR / "brand-catalog.py"
    result = subprocess.run(
        [sys.executable, str(catalog_script)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print(f"品牌目录生成失败: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    brands_json = result.stdout.strip()

    # 2. 解析用户变量
    subs = {}
    for var in args.vars:
        key, _, value = var.partition("=")
        subs[key.strip()] = value.strip()

    lang = subs.get("LANG", "zh")
    receiver_port = str(args.port)

    # 3. 替换模板占位符
    template_text = Path(args.template).read_text(encoding="utf-8")

    # 转义 JSON 中的单引号（因为模板用单引号包裹 JSON）
    safe_json = brands_json.replace("\\", "\\\\").replace("'", "\\'")

    template_text = template_text.replace("__LANG__", lang)
    template_text = template_text.replace("__RECEIVER_PORT__", receiver_port)
    template_text = template_text.replace("'__BRANDS_JSON__'", f"'{safe_json}'")

    Path(args.output).write_text(template_text, encoding="utf-8")

    # 4. 打开浏览器预览
    import webbrowser
    webbrowser.open(f"file://{Path(args.output).resolve()}")
    print("✓ 品牌预览已在浏览器中打开")
    print("选择品牌后请复制 JSON 结果粘贴给 Agent")


if __name__ == "__main__":
    main()
