# AstrBot Text2Image Service

[中文](README_zh-CN.md) | English | [日本語](README_ja.md)

## Features

A simple web service that converts HTML/templates to images, with image lifecycle management support.

## Environment Variables

- `PORT`: Service port, default is 8999
- `IMAGE_LIFETIME_HOURS`: Image lifetime in hours, default is 24 hours. Images older than this will be automatically cleaned up
- `T2I_RENDER_WAIT_UNTIL`: Playwright navigation wait state, default is `domcontentloaded`. Valid values: `commit`, `domcontentloaded`, `load`, `networkidle`
- `T2I_SKIP_FONT_READY`: Whether to skip Playwright's internal `document.fonts.ready` wait before screenshots, default is `true`. This is a rendering stability fallback for slow or blocked remote fonts
- `RATE_LIMIT_MAX_REQUESTS`: Maximum requests allowed in each rate-limit window, disabled by default
- `RATE_LIMIT_WINDOW_SECONDS`: Rate-limit window size in seconds, disabled by default

## Smoke Test

After installing Playwright browsers, run a local Chinese/Emoji render smoke test:

```bash
python scripts/render_smoke.py
```

To exercise fallback behavior when a remote font URL is unreachable:

```bash
python scripts/render_smoke.py --remote-font-probe
```

To fail when the expected Noto CJK / Emoji fonts are not visible to fontconfig, use:

```bash
python scripts/render_smoke.py --require-fonts
```

The smoke test verifies that the rendering path completes and that expected fonts are installed when `--require-fonts` is used. It does not perform pixel-level glyph quality checks.

## API Endpoints

### POST /text2img/generate

Convert HTML to image

> Choose either html or tmpl. Provide tmpl and tmpldata together.

- `str` html: HTML text
- `str` tmpl: Jinja2 HTML template
- `dict` tmpldata: Jinja2 template data
- `bool` json: Whether to return JSON format (returns an id)
- `dict` `optional` options
  - timeout (float, optional): Screenshot timeout.
  - type (Literal["jpeg", "png"], optional): Screenshot image type.
  - quality (int, optional): Screenshot quality, only applicable to JPEG format.
  - omit_background (bool, optional): Whether to hide the default white background, allowing transparent screenshots (PNG only).
  - full_page (bool, optional): Whether to capture the entire page instead of just the viewport, default is True.
  - clip (FloatRect, optional): Area to clip after screenshot, xy is the starting point.
  - animations: (Literal["allow", "disabled"], optional): Whether to allow CSS animations.
  - caret: (Literal["hide", "initial"], optional): When set to `hide`, the text caret will be hidden during screenshot, default is `hide`.
  - scale: (Literal["css", "device"], optional): Page scaling settings. When set to `css`, device resolution maps 1:1 with CSS pixels, making screenshots smaller on high-DPI screens. When set to `device`, scales according to device screen scaling or the device_scale_factor parameter in the current Playwright Page/Context.
  - viewport_width (int, optional): Custom viewport width to control screenshot width. Resolved in priority order:
    1. Explicitly set in request options
    2. Auto-parsed from `<meta name="viewport" content="width=...">` in HTML
    3. Uses Playwright's context default viewport if width and height are not both available
  - viewport_height (int, optional): Custom viewport height to control screenshot height. Resolved in priority order:
    1. Explicitly set in request options
    2. Auto-parsed from `<meta name="viewport" content="height=...">` in HTML
    3. Uses Playwright's context default viewport if width and height are not both available
  - device_scale_factor_level (Literal["normal", "high", "ultra"], optional): Device pixel ratio level, default is "normal". Different levels use independent browser context pools for better performance and resource isolation.
    - `normal`: Device pixel ratio 1.0 (default)
    - `high`: Device pixel ratio 1.3
    - `ultra`: Device pixel ratio 1.8
  - wait_until (Literal["commit", "domcontentloaded", "load", "networkidle"], optional): Playwright navigation wait state. Defaults to `T2I_RENDER_WAIT_UNTIL` when omitted

### GET /text2img/data/{id}

Returns the corresponding image by id.
