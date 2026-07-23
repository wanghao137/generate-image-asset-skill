**[English](./README.md)** | [简体中文](./README.zh-CN.md)

<p align="center">
  <img src="docs/images/hero.png" alt="Generate Image Asset" width="720">
</p>

<h1 align="center">Generate Image Asset</h1>

<p align="center">
  <em>Turn one line of text into a pixel-perfect, verifiable, high-resolution PNG.<br>Self-contained toolkit: CLI Skill + MCP server + generation engine.</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Node.js-22+-339933.svg?style=flat-square&logo=node.js&logoColor=white" alt="Node">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/gpt--image--2-supported-FF6B6B.svg?style=flat-square" alt="gpt-image-2">
  <img src="https://img.shields.io/badge/MCP-compatible-1e1e2e.svg?style=flat-square" alt="MCP">
  <img src="https://img.shields.io/badge/platform-cross--platform-lightgrey.svg?style=flat-square" alt="Platform">
</p>

---

<p align="center">
  <img src="docs/images/gallery-photo.png" width="190" alt="Photoreal example">
  &nbsp;
  <img src="docs/images/gallery-product.png" width="150" alt="Product example">
  &nbsp;
  <img src="docs/images/gallery-illustration.png" width="240" alt="Illustration example">
  &nbsp;
  <img src="docs/images/gallery-text.png" width="150" alt="Text poster example">
</p>

<p align="center"><sub>All gallery images generated with <code>gpt-image-2</code> via this toolkit.</sub></p>

---

## ✨ What it is

A command-line image generation toolkit that turns a prompt into a verified PNG with **exact target dimensions, strict aspect-ratio inheritance, and SHA-256 checksums**. It bundles everything you need in one repo — no separate engine install required.

**Three components, one clone:**

| Component | For who | Entry |
|---|---|---|
| 🖥️ **Skill (CLI)** | Developers, scripts, automation | `scripts/run_image_job.py` |
| 🤖 **MCP server** | Cursor / Claude / AI assistants | `engine/mcp-server.mjs` |
| ⚙️ **Engine (Task API)** | The backend that actually generates images | `npm run engine` |

## 🎯 Why use this

Calling an image API directly has three common pitfalls. This toolkit fixes all of them:

| Problem | Direct API call | This toolkit |
|---|---|---|
| **Distorted ratio** | API returns a canvas that doesn't match your target → stretching distorts it | Forces exact integer-pixel ratio match, never stretches |
| **Wrong size** | You want 4K, API gives 1K, upscaling is blurry | Lanczos3 upscale from a ratio-matched source canvas |
| **Transparent edges** | `contain` mode adds empty borders | Uses `cover` geometry — no letterboxing, full bleed |

**How it works:**

```
prompt + target size
  → provider generates a raw canvas
  → cover-crop to an exact integer-ratio "source" PNG
  → Lanczos3 upscale to target size (ratio preserved, no re-selecting)
  → output source + final + verification report
```

Every output is guaranteed: source and final share an identical ratio (`sourceW × finalH == finalW × sourceH`), final pixels exactly match the request, and the downloaded file's SHA-256 matches the manifest.

## 🚀 Quick Start

### Requirements

- [Node.js](https://nodejs.org/) 22+
- [Python](https://python.org/) 3.10+
- An OpenAI-compatible image generation API (bring your own URL + key)

> **Note on `sharp`:** the engine uses sharp for image scaling — it's a native library, so the first `npm install` compiles it (~30-60s). This is the only "heavy" dependency.

### Install

```bash
git clone https://github.com/wanghao137/generate-image-asset-skill.git
cd generate-image-asset-skill/generate-image-asset
npm install
```

### Configure (once)

Create `.env.local` in the repo root (**never share or commit this file**):

```dotenv
IMAGE_TASK_API_TOKEN=make-up-a-long-random-string-here
IMAGE_TASK_API_PORT=9789
IMAGE_TASK_PROVIDER_BASE_URL=https://your-api-endpoint/v1
IMAGE_TASK_PROVIDER_API_KEY=your-secret-key
IMAGE_TASK_PROVIDER_MODEL=gpt-image-2
```

### Start the engine

```bash
npm run engine
```

You should see `TaoStudio Image Task API listening at http://127.0.0.1:9789`. Keep this terminal open.

### Generate your first image

In a new terminal:

```bash
# Windows
set IMAGE_TASK_API_TOKEN=your-token-from-step-above
py -3 scripts\run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt "a ginger cat on a wooden porch, afternoon light, photoreal" --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png

# macOS / Linux
export IMAGE_TASK_API_TOKEN=your-token-from-step-above
python3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt "a ginger cat on a wooden porch, afternoon light, photoreal" --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png
```

This produces:
- `my-image.png` — the final high-resolution image (exact target size)
- `my-image-source.png` — the source canvas (original ratio, pre-upscale)
- `my-image.report.json` — generation report (dimensions, SHA-256, manifest)

## 🤖 Use via AI assistant (MCP)

If you use Cursor, Claude Desktop, or any MCP-compatible AI tool, it can generate images for you. After installing and starting the engine (above), add this to your AI tool's MCP config:

```json
{
  "command": "node",
  "args": ["/your/path/generate-image-asset/engine/mcp-server.mjs"],
  "env": {
    "IMAGE_TASK_API_URL": "http://127.0.0.1:9789",
    "IMAGE_TASK_API_TOKEN": "your-token-from-env-local"
  }
}
```

The AI assistant gains 6 capabilities: upload image, create job, query status, wait for completion, cancel, download (never silently overwrites existing files).

## 🔀 Two model modes

| Model type | `--model` | `--api-mode` | Example |
|---|---|---|---|
| Image model | `gpt-image-2` etc. | `images` | Dedicated image models (most common) |
| Text model | `gpt-5.6-sol` etc. | `responses` | Chat models that output images |

**Key:** model and api-mode must match. Image models use `images`, text models use `responses`. Mismatching causes an error.

Text-model example:

```bash
python3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 \
  --prompt "minimalist tech brand banner illustration" \
  --model gpt-5.6-sol --api-mode responses --provider configured \
  --size 2880x2880 --quality high --out my-image.png
```

## 📋 Common parameters

| Parameter | Default | Description |
|---|---|---|
| `--backend` | `built-in` | `task-api` (recommended, uses this repo's engine) |
| `--prompt-file` | — | Path to a prompt text file (use for long prompts) |
| `--prompt` | — | Pass prompt inline |
| `--size` | `2160x3840` | Final dimensions, also determines the ratio |
| `--model` | `gpt-image-2` | Model name |
| `--api-mode` | `images` | `images` or `responses` |
| `--provider` | `mock` | `configured` (uses `.env.local` real config) |
| `--quality` | `high` | Image quality |
| `--content-class` | `photo` | `photo` / `illustration` / `text` / `logo` / `ui` |
| `--enhancement` | `auto` | Upscale algorithm, `lanczos3` most common |
| `--max-attempts` | `3` | Retry count on failure (1-5) |
| `--out` | `output/.../output.png` | Output path |
| `--force` | off | Overwrite existing file (refuses without this flag) |

## ✅ Verify your install

Run the test suite (uses mock provider, no real API key needed):

```bash
npm test
```

Expected: 20 tests passing.

## ❓ FAQ

**`npm install` fails / sharp won't compile?**
sharp is native. Ensure Node 22+. On Windows install Visual Studio Build Tools; on macOS install Xcode Command Line Tools. See [sharp install docs](https://sharp.pixelplumbing.com/install).

**"requires an image model" error?**
You used a text model (e.g. `gpt-5.6-sol`) with `--api-mode images`. Change to `--api-mode responses`.

**"connection refused"?**
The engine isn't running, or the address/port is wrong. Confirm `npm run engine` is running and `--api-url` matches the port in `.env.local`.

**"output exists; pass --force"?**
The output file already exists and the tool refuses to overwrite it. Use a different name, or add `--force`.

**How to pass the token?**
Use the `IMAGE_TASK_API_TOKEN` environment variable — never as a command-line argument (it would stay in shell history). `.env.local` is gitignored.

## 📁 Project structure

```
generate-image-asset/
├── engine/                          # Generation engine (Task API)
│   ├── service.mjs                  # Core: job scheduling, ratio verification, scaling
│   ├── cli.mjs                      # Entry point (npm run engine)
│   ├── mcp-server.mjs               # MCP server (npm run mcp)
│   └── service.test.mjs             # Engine tests (npm test)
├── scripts/
│   ├── run_image_job.py             # Skill CLI entry
│   └── image_core_cli.mjs           # Geometry calculation CLI
├── vendor/image-job-core/           # Shared contract impl (ratio, sizing, verification)
├── references/adversarial-review.md
├── agents/openai.yaml
├── package.json
└── .env.local                       # Your keys (gitignored)
```

## 🔗 Related

The engine in this repo is a publishable mirror of the [TaoStudio Image Lab](https://github.com/wanghao137/taostudio-image-lab) Task API, sharing the same Image Job Contract. TaoStudio Image Lab is the full web app; this repo extracts just the generation engine and tools so external users needn't clone the entire web project.

Engine code stays in sync with the main repo via a sync script.

## 📜 License

[MIT](./LICENSE) — free for commercial use, just keep the copyright notice.
