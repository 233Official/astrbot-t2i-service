---
name: playwright-html2pic-timeout-debug
description: Use when astrbot-t2i-service /text2img/generate returns 500, or logs mention Playwright Page.goto Timeout, waiting until load, rendered_xxx.html, html2pic, or HTML-to-image screenshot failures.
---

# Playwright HTML2PIC Timeout Debug

Use this skill to diagnose and fix `astrbot-t2i-service` HTML-to-image failures caused by Playwright navigation or screenshot timeouts.

---

## Recognize the known failure

Look for logs like:

```text
POST /text2img/generate HTTP/1.1" 500 Internal Server Error
playwright._impl._errors.TimeoutError: Page.goto: Timeout ... exceeded.
- navigating to "file:///app/data/rendered_xxx.html", waiting until "load"
```

This means the service wrote the HTML file but timed out while waiting for the page `load` event. If logs only show `/text2img/generate` 500 near the configured timeout, also inspect `page.screenshot()` timeout, oversized full-page screenshots, and browser context errors.

---

## Likely causes

- Remote fonts, images, backgrounds, avatars, or CDN resources.
- Slow or blocked Docker container networking.
- Large DOM or long full-page report.
- Heavy screenshot options: PNG, high/ultra device scale, full page.
- Strict `wait_until="load"` behavior.
- Screenshot timeout or memory pressure from oversized full-page screenshots.

---

## Fix targets

- Consider `wait_until="domcontentloaded"` for `page.goto()`.
- Add a timeout fallback that attempts screenshot with the current DOM.
- Return structured JSON errors instead of naked 500 text.
- Log failed resource requests and 4xx/5xx resource responses.
- Include timeout, wait_until, output type, quality, scale, and HTML path in logs.

---

## Do not misattribute

If `/text2img/generate` returned 500, the root issue is service-side rendering. Message adapter or OneBot image sending is a later stage and should not be the first suspect.
