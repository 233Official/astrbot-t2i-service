#!/usr/bin/env python3
from __future__ import annotations

import argparse
import asyncio
import os
import shutil
import subprocess
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


PNG_MAGIC = b"\x89PNG\r\n\x1a\n"
JPEG_MAGIC = b"\xff\xd8\xff"
FONT_CHECKS = {
    "Noto CJK": "Noto Sans CJK SC",
    "Noto Color Emoji": "Noto Color Emoji",
}


def check_fonts(require_fonts: bool) -> None:
    fc_match = shutil.which("fc-match")
    if not fc_match:
        message = "fc-match is not available; skipping installed font checks."
        if require_fonts:
            raise RuntimeError(message)
        print(message, file=sys.stderr)
        return

    missing: list[str] = []
    for label, query in FONT_CHECKS.items():
        completed = subprocess.run(
            [fc_match, query],
            check=False,
            capture_output=True,
            text=True,
        )
        output = f"{completed.stdout}\n{completed.stderr}"
        print(f"Font check: {label}: {completed.stdout.strip()}")
        if completed.returncode != 0 or "Noto" not in output:
            missing.append(f"{label} ({query})")

    if missing:
        message = "Missing expected fonts: " + ", ".join(missing)
        if require_fonts:
            raise RuntimeError(message)
        print(message, file=sys.stderr)


def build_smoke_html(remote_font_probe: bool) -> str:
    remote_font_css = ""
    if remote_font_probe:
        remote_font_css = """
        @font-face {
            font-family: "BlockedRemoteSmokeFont";
            src: url("https://example.invalid/blocked-smoke-font.woff2") format("woff2");
            font-display: swap;
        }
        """

    return f"""
<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=960, height=720">
  <style>
    {remote_font_css}
    :root {{
      color-scheme: light;
      --font-cjk: "BlockedRemoteSmokeFont", "Noto Sans CJK SC", "Noto Sans CJK", "Noto Sans SC", "Noto Color Emoji", sans-serif;
      --font-serif: "Noto Serif CJK SC", "Noto Serif SC", "Noto Serif CJK TC", serif;
    }}
    body {{
      margin: 0;
      background: linear-gradient(135deg, #f8fbff, #fff4e6);
      color: #172033;
      font-family: var(--font-cjk);
    }}
    main {{
      width: 840px;
      margin: 42px auto;
      padding: 36px;
      border-radius: 28px;
      background: rgba(255, 255, 255, 0.92);
      box-shadow: 0 18px 60px rgba(27, 40, 77, 0.16);
    }}
    h1 {{
      margin: 0 0 18px;
      font-size: 42px;
      line-height: 1.18;
      font-weight: 800;
    }}
    .serif {{
      font-family: var(--font-serif);
      font-size: 25px;
      line-height: 1.72;
    }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(3, 1fr);
      gap: 14px;
      margin-top: 24px;
    }}
    .card {{
      padding: 18px;
      border-radius: 18px;
      background: #f4f7ff;
      font-size: 19px;
      line-height: 1.5;
    }}
    code {{
      font-family: "Noto Sans Mono CJK SC", ui-monospace, SFMono-Regular, Menlo, monospace;
    }}
  </style>
</head>
<body>
  <main>
    <h1>中文 / Emoji 渲染烟测 🧪🎨✅</h1>
    <p class="serif">简体中文：群分析报告应稳定渲染为图片，不应被远程字体加载拖死。</p>
    <p class="serif">繁體中文：服務端截圖應優先使用容器內建字體，並在外部字體不可用時正常降級。</p>
    <div class="grid">
      <div class="card">表情：😀 😺 🚀 ✨ 🧧</div>
      <div class="card">粗体：<strong>活跃成员排行</strong></div>
      <div class="card">等宽：<code>wait_until=domcontentloaded</code></div>
    </div>
  </main>
</body>
</html>
"""


async def render_smoke(args: argparse.Namespace) -> Path:
    from src.render import ScreenshotOptions, Text2ImgRender

    renderer = Text2ImgRender()
    try:
        _, abs_path = await renderer.from_html(
            build_smoke_html(remote_font_probe=args.remote_font_probe)
        )
        result = await renderer.html2pic(
            abs_path,
            ScreenshotOptions(
                type=args.type,
                full_page=True,
                timeout=args.timeout,
                wait_until=args.wait_until,
                device_scale_factor_level=args.device_scale_factor_level,
            ),
        )
    finally:
        await renderer.terminate()

    result_path = Path(result)
    data = result_path.read_bytes()
    if args.type == "png" and not data.startswith(PNG_MAGIC):
        raise RuntimeError(f"Expected PNG output, got magic bytes {data[:8]!r}")
    if args.type == "jpeg" and not data.startswith(JPEG_MAGIC):
        raise RuntimeError(f"Expected JPEG output, got magic bytes {data[:8]!r}")
    if result_path.stat().st_size <= 0:
        raise RuntimeError(f"Rendered file is empty: {result_path}")

    return result_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render a Chinese/Emoji smoke-test HTML through Playwright."
    )
    parser.add_argument("--type", choices=("png", "jpeg"), default="png")
    parser.add_argument("--timeout", type=float, default=30_000)
    parser.add_argument(
        "--wait-until",
        choices=("commit", "domcontentloaded", "load", "networkidle"),
        default=None,
    )
    parser.add_argument(
        "--device-scale-factor-level",
        choices=("normal", "high", "ultra"),
        default="normal",
    )
    parser.add_argument(
        "--remote-font-probe",
        action="store_true",
        help="Include an intentionally unreachable @font-face URL to exercise font fallback behavior.",
    )
    parser.add_argument(
        "--require-fonts",
        action="store_true",
        help="Fail if expected Noto CJK / Emoji fonts are not visible to fontconfig.",
    )
    return parser.parse_args()


def main() -> None:
    os.environ.setdefault("T2I_RENDER_WAIT_UNTIL", "domcontentloaded")
    os.environ.setdefault("T2I_SKIP_FONT_READY", "true")

    try:
        args = parse_args()
        check_fonts(require_fonts=args.require_fonts)
        result_path = asyncio.run(render_smoke(args))
    except Exception as e:
        if "Executable doesn't exist" in str(e) or "playwright install" in str(e):
            print(
                "Smoke render failed because Playwright browsers are not installed. "
                "Run `playwright install chromium` or use the Docker image, which installs Chromium during build.",
                file=sys.stderr,
            )
        raise
    print(f"Smoke render succeeded: {result_path} ({result_path.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
