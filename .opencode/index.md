# astrbot-t2i-service OpenCode 索引

本目录记录 `astrbot-t2i-service` 服务端专属的开发、排障和协作经验。

---

## 文档

- [`playwright-render-timeout-runbook.md`](./playwright-render-timeout-runbook.md)：Playwright HTML 转图片超时排障经验。

---

## 跨项目引用

- AstrBot 工作区总览：`../../../.opencode/t2i-rendering-troubleshooting.md`
- 群分析插件调用方排障：`../../../Plugins/astrbot_plugin_qq_group_daily_analysis/.opencode/t2i-rendering-caller-runbook.md`

---

## 维护原则

- 服务端 `.opencode/` 记录 HTTP API、Playwright、容器网络、截图参数和错误响应经验。
- 插件调用方日志、配置和降级提示放在对应插件仓库。
- 跨多个插件或服务复用的排障流程提炼到 AstrBot 工作区 `.opencode/`。
