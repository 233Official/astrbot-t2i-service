# AstrBot Text2Image Service

[中文](README_zh-CN.md) | [English](README.md) | 日本語

## 機能

HTMLやテンプレートを画像に変換するシンプルなWebサービスで、画像のライフサイクル管理をサポートしています。

## 環境変数設定

- `PORT`: サービスポート、デフォルトは8999
- `IMAGE_LIFETIME_HOURS`: 画像の保持時間（時間単位）、デフォルトは24時間。この時間を超えた画像ファイルは自動的にクリーンアップされます
- `T2I_RENDER_WAIT_UNTIL`: Playwright のナビゲーション待機状態。デフォルトは `domcontentloaded`。有効な値: `commit`, `domcontentloaded`, `load`, `networkidle`
- `T2I_SKIP_FONT_READY`: スクリーンショット前の Playwright 内部 `document.fonts.ready` 待機をスキップするかどうか。デフォルトは `true`。遅い、またはブロックされたリモートフォント向けのレンダリング安定性フォールバックです
- `RATE_LIMIT_MAX_REQUESTS`: レート制限ウィンドウ内の最大リクエスト数。デフォルトでは無効
- `RATE_LIMIT_WINDOW_SECONDS`: レート制限ウィンドウの秒数。デフォルトでは無効

## スモークテスト

Playwright ブラウザをインストールした後、ローカルの中国語 / Emoji レンダリングスモークテストを実行できます：

```bash
python scripts/render_smoke.py
```

リモートフォント URL に到達できない場合の fallback 動作を確認するには：

```bash
python scripts/render_smoke.py --remote-font-probe
```

期待する Noto CJK / Emoji フォントが fontconfig から見えない場合に失敗させるには：

```bash
python scripts/render_smoke.py --require-fonts
```

このスモークテストはレンダリング経路が完了することを確認し、`--require-fonts` 使用時に期待するフォントがインストールされているかを確認します。ピクセル単位のグリフ品質検証は行いません。

## API エンドポイント

### POST /text2img/generate

HTMLを画像に変換

> htmlとtmplのいずれかを選択してください。tmplとtmpldataは一緒に提供してください。

- `str` html: HTMLテキスト
- `str` tmpl: Jinja2 HTMLテンプレート
- `dict` tmpldata: Jinja2テンプレートデータ
- `bool` json: JSON形式で返すかどうか（idを返します）
- `dict` `optional` options
  - timeout (float, optional): スクリーンショットのタイムアウト時間。
  - type (Literal["jpeg", "png"], optional): スクリーンショットの画像タイプ。
  - quality (int, optional): スクリーンショットの品質、JPEG形式のみ適用されます。
  - omit_background (bool, optional): デフォルトの白い背景を非表示にするかどうか。これにより透明なスクリーンショットが可能になります（PNG形式のみ）。
  - full_page (bool, optional): ビューポートサイズだけでなく、ページ全体をキャプチャするかどうか、デフォルトはTrue。
  - clip (FloatRect, optional): スクリーンショット後にクリップする領域、xyは開始点です。
  - animations: (Literal["allow", "disabled"], optional): CSSアニメーションを許可するかどうか。
  - caret: (Literal["hide", "initial"], optional): `hide`に設定すると、スクリーンショット時にテキストキャレットが非表示になります。デフォルトは`hide`。
  - scale: (Literal["css", "device"], optional): ページのスケール設定。`css`に設定すると、デバイス解像度とCSSピクセルが1:1で対応し、高解像度画面ではスクリーンショットが小さくなります。`device`に設定すると、デバイスの画面スケール設定または現在のPlaywright Page/Contextのdevice_scale_factorパラメータに従ってスケールされます。
  - viewport_width (int, optional): スクリーンショットの幅を制御するカスタムビューポート幅。優先順位順：
    1. リクエストオプションで明示的に指定
    2. HTMLの`<meta name="viewport" content="width=...">` から自動解析
    3. 幅と高さの両方が得られない場合は Playwright コンテキストのデフォルトビューポートを使用
  - viewport_height (int, optional): スクリーンショットの高さを制御するカスタムビューポート高さ。優先順位順：
    1. リクエストオプションで明示的に指定
    2. HTMLの`<meta name="viewport" content="height=...">` から自動解析
    3. 幅と高さの両方が得られない場合は Playwright コンテキストのデフォルトビューポートを使用
  - device_scale_factor_level (Literal["normal", "high", "ultra"], optional): デバイスピクセル比レベル、デフォルトは"normal"。異なるレベルは独立したブラウザコンテキストプールを使用し、より良いパフォーマンスとリソース分離を提供します。
    - `normal`: デバイスピクセル比 1.0（デフォルト）
    - `high`: デバイスピクセル比 1.3
    - `ultra`: デバイスピクセル比 1.8
  - wait_until (Literal["commit", "domcontentloaded", "load", "networkidle"], optional): Playwright のナビゲーション待機状態。省略時は `T2I_RENDER_WAIT_UNTIL` を使用します

### GET /text2img/data/{id}

idに対応する画像を返します。
