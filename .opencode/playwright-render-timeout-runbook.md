# Playwright HTML 转图片超时排障经验

本文记录 `astrbot-t2i-service` 在处理 `/text2img/generate` 请求时，Playwright 加载本地 HTML 超时导致 500 的服务端排障经验。

---

## 已知失败现象

服务端日志可能出现：

```text
POST /text2img/generate HTTP/1.1" 500 Internal Server Error
Exception in ASGI application
playwright._impl._errors.TimeoutError: Page.goto: Timeout 100000ms exceeded.
Call log:
- navigating to "file:///app/data/rendered_xxx.html", waiting until "load"
```

这说明服务已经收到请求并写入 HTML 文件，但 Playwright 在 `page.goto()` 阶段等待页面 `load` 事件超时，截图尚未执行。若日志只显示 `/text2img/generate` 500 且耗时贴近 timeout，也需要同时排查 `page.screenshot()` 超时、full-page 截图过重或浏览器上下文异常。

---

## 服务端调用链

```text
POST /text2img/generate
→ api.py:text2img()
→ render.html2pic(abs_path, options)
→ page.goto(file:///app/data/rendered_xxx.html, timeout=options.timeout)
→ 默认等待 load
→ page.goto TimeoutError 或后续 page.screenshot TimeoutError
→ FastAPI 返回 500 Internal Server Error
```

关键位置通常包括：

- `src/api.py`：`text2img` 路由。
- `src/render.py`：`html2pic` 渲染函数。
- Playwright `page.goto()` 和 `page.screenshot()` 调用。

---

## 为什么 `file://` 本地 HTML 也会超时

`file:///app/data/rendered_xxx.html` 只是 HTML 文件本身在本地。页面内部仍可能引用外部资源：

- 远程字体。
- 背景图。
- 头像图片。
- CDN 脚本或样式。
- webp/png/svg 等静态资源。

如果 `page.goto()` 等待条件是 `load`，浏览器会等待这些外部资源完成。容器网络慢、DNS 慢、资源被阻塞、连接悬挂时，`load` 事件可能迟迟不触发。

---

## 常见触发条件

- HTML 报告体积很大，例如数十万字符。
- 使用复杂主题，包含多个远程字体和背景图。
- `full_page=true`，页面高度大。
- 图片格式为 `png`，输出体积和截图压力更高。
- `device_scale_factor_level=high/ultra`。
- Docker 容器 CPU、内存或网络资源不足。

---

## 推荐服务端修复

### 放宽等待条件

优先考虑将 `page.goto()` 的等待条件从 `load` 改为 `domcontentloaded`，或做成配置项。

```python
await page.goto(
    f"file://{html_file_path}",
    wait_until="domcontentloaded",
    timeout=screenshot_options.timeout,
)
```

### 超时后截图兜底

如果仍希望优先等待完整 `load`，可以在超时后保留页面并尝试截图当前状态，而不是直接返回 500。

```python
try:
    await page.goto(
        f"file://{html_file_path}",
        wait_until="load",
        timeout=screenshot_options.timeout,
    )
except TimeoutError:
    logger.warning("page.goto load timeout; trying screenshot with current DOM")
```

实际实现时需确认 Playwright 超时后页面状态是否可截图，并根据服务质量要求决定是否继续。

### 结构化错误响应

不要只返回裸 `Internal Server Error`。建议返回 JSON，包含：

- `error_type`。
- `message`。
- `html_file_path`。
- `timeout`。
- `wait_until`。
- `options`。

这样调用方可以准确识别 T2I 服务端失败，而不是把错误文本当图片处理。

### 记录资源加载失败

建议监听页面事件：

- `requestfailed`。
- `response` 中的 4xx/5xx。
- `console`。
- `pageerror`。

用于定位是哪个字体、背景图或头像拖住了 `load`。

---

## 临时缓解

- 降低调用方 `device_scale_factor_level` 到 `normal`。
- 优先使用 `jpeg`。
- 使用 simple 主题复现。
- 减少远程字体、背景图和头像。
- 在容器内测试访问模板引用的资源域名。
- 增加容器 CPU/内存限制。

---

## 与调用方的关系

调用方插件应识别非图片响应并给出清晰日志；服务端应修复 Playwright 超时和 500 错误响应。

调用方经验见：

```text
Plugins/astrbot_plugin_qq_group_daily_analysis/.opencode/t2i-rendering-caller-runbook.md
```
