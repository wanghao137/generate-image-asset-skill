<div align="center">
  <img src="docs/images/hero.png" alt="Image Asset Pipeline" width="880">
</div>

# Image Asset Pipeline

> *「一次生成，三件产出。原图不丢，4K 精确，验证可审。」*

<div align="center">

[![License: MIT](https://img.shields.io/badge/license-MIT-yellow.svg?style=flat-square)](LICENSE)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-Standard-green.svg?style=flat-square)](https://github.com/vercel-labs/skills)
[![skills.sh](https://img.shields.io/badge/skills.sh-Compatible-blue.svg?style=flat-square)](https://skills.sh)
[![Runtime](https://img.shields.io/badge/Runtime-Claude%20·%20Codex%20·%20Cursor%20·%20MCP-blueviolet.svg?style=flat-square)](#-安装)
[![Node](https://img.shields.io/badge/Node.js-%E2%89%A522-339933.svg?style=flat-square&logo=node.js&logoColor=white)](https://nodejs.org)
[![gpt-image-2](https://img.shields.io/badge/gpt--image--2-supported-FF6B6B.svg?style=flat-square&logo=openai&logoColor=white)](#-两种模型模式)

</div>

<div align="center">
<sub>自带 Provider · BYOK —— 不内置任何密钥。</sub>
</div>

---

**面向 AI Agent 的生产级图像资产流水线。** 不是又一个图片生成脚本——
它是 Agent 时代的图像导出管线：你给一句提示词，它吐回三样东西：

| 输出 | 是什么 |
|---|---|
| 🖼 **原始源图** | 规范画布，精确比例，放大前的原始资产 |
| 🖼 **精确 4K 成品** | 像素精确匹配你的目标尺寸，Lanczos3 放大 |
| 📋 **验证报告** | 尺寸、SHA-256、manifest、路由，全部可审计 |

**[看效果](#-效果演示)** · **[安装](#-安装)** · **[工作原理](#-工作原理)** · **[English](#english)**

---

## 🎯 它解决了什么

直接调图像 API 有三个老问题。这个流水线全修了：

| 问题 | 直接调 API | 本流水线 |
|---|---|---|
| **比例变形** | API 返回的画布比例对不上目标 → 拉伸变形 | 强制精确整数像素比匹配，**绝不拉伸** |
| **尺寸不对** | 你要 4K，API 给 1K，放大就糊 | 从比例匹配的源画布做 Lanczos3 放大 |
| **透明黑边** | `contain` 模式留空边 | 用 `cover` 几何裁切——**无黑边，满版** |
| **无可审计链路** | 只得到一个 blob，无出处 | 源图 + 成品 + manifest + SHA-256，**每次都有** |

---

## ✨ 效果演示

> **你：** *"生成一张电影感产品图。"*

**Agent（运行此流水线）：**

```
→ image_job_create
    prompt: "cinematic product image"
    ratio: 3:4
    dimensions: 2160x2880
    model: gpt-image-2

✓ 源图资产生成   (asset_7ffd…, 1086×1448, 3:4)
✓ 4K 生产资产生成 (asset_6b2a…, 2160×2880, 精确)
✓ 验证完成
    · 尺寸: 2160x2880 ✓
    · 比例不变量: 1086×2880 == 2160×1448 ✓
    · SHA-256: 9f3a…e21c 匹配 manifest ✓
```

### 双资产输出

一个提示词 → 两个资产，比例互相锁定。

<table align="center">
  <tr>
    <td align="center" width="50%">
      <img src="docs/images/dual-output-source.png" width="280" alt="源图"><br>
      <sub><b>源图</b> · 1086×1448 · 3:4</sub><br>
      <sub>原始画布，放大前</sub>
    </td>
    <td align="center" width="50%">
      <img src="docs/images/dual-output-final.png" width="280" alt="成品"><br>
      <sub><b>成品</b> · 2160×2880 · 3:4</sub><br>
      <sub>精确目标像素，Lanczos3</sub>
    </td>
  </tr>
</table>

<div align="center">
<sub>同一提示词，同一比例。成品恰好是源图的 2 倍——不重新生成，比例零漂移。</sub>
</div>

---

## 🚀 安装

两种方式，按你的目标选。

### 方式一：装 Skill（让 AI 助手出图）

最简单。装完 Skill，你的 Agent 就能用它**自带的图像工具**出图，不需要起引擎。

```bash
npx skills add wanghao137/image-asset-pipeline
```

这会把 Skill（`SKILL.md` + `scripts/run_image_job.py`）装进 Agent 的 skills 目录，自动检测已装的 runtime。想指定 runtime：

```bash
# Claude Code
npx skills add wanghao137/image-asset-pipeline -a claude-code

# Codex
npx skills add wanghao137/image-asset-pipeline -a codex

# Cursor
npx skills add wanghao137/image-asset-pipeline -a cursor
```

支持 runtime：**Claude Code · Codex · Cursor · OpenCode · Gemini CLI · OpenClaw**，通过 [`npx skills`](https://github.com/vercel-labs/skills) 共 70+。

> 装完 Skill，Agent 用 `built-in` 后端调它自带的图像工具出图，然后 Skill 本地做比例校验、cover 裁切、Lanczos3 放大、SHA-256 验证。**不需要引擎也能出 4K。** 引擎（方式二）是可选升级，给需要批量/自动化/服务端的场景用。

### 方式二：本地引擎（批量 4K，或用 MCP）

适合：脚本自动化、批量出图、或想让 Cursor/Claude 通过 MCP 驱动引擎。

```bash
git clone https://github.com/wanghao137/image-asset-pipeline.git
cd image-asset-pipeline/generate-image-asset
npm install
```

> **关于 `sharp`：** 引擎用 [`sharp`](https://sharp.pixelplumbing.com/) 做图像缩放——原生库，首次 `npm install` 会编译（约 30-60 秒）。这是唯一的"重型"依赖。需要 Node.js 22+。

配置一次——在仓库根目录创建 `.env.local`（**永不分享或提交**）：

```dotenv
IMAGE_TASK_API_TOKEN=随便填一串长随机字符串
IMAGE_TASK_API_PORT=9789
IMAGE_TASK_PROVIDER_BASE_URL=https://你的-api-endpoint/v1
IMAGE_TASK_PROVIDER_API_KEY=你的-secret-key
IMAGE_TASK_PROVIDER_MODEL=gpt-image-2
```

启动引擎：

```bash
npm run engine
# → TaoStudio Image Task API listening at http://127.0.0.1:9789
```

生成你的第一个验证资产：

```bash
# Windows
set IMAGE_TASK_API_TOKEN=你上面填的-token
py -3 scripts\run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 ^
  --prompt "一只橘猫趴在木制门廊上，午后阳光，照片级真实" ^
  --model gpt-image-2 --api-mode images --provider configured ^
  --size 2160x3840 --quality high --out my-image.png

# macOS / Linux
export IMAGE_TASK_API_TOKEN=你上面填的-token
python3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 \
  --prompt "一只橘猫趴在木制门廊上，午后阳光，照片级真实" \
  --model gpt-image-2 --api-mode images --provider configured \
  --size 2160x3840 --quality high --out my-image.png
```

产出**三个文件**——流水线核心的双资产输出：

| 文件 | 它是什么 |
|---|---|
| `my-image-source.png` | **原始源图** —— 规范画布，精确比例，放大前 |
| `my-image.png` | **精确 4K 成品** —— 最终像素精确匹配 `--size` |
| `my-image.report.json` | **验证报告** —— 尺寸、SHA-256、manifest、路由 |

---

## 🏗 工作原理

<img src="docs/images/architecture.png" alt="架构流水线图" width="880">

**流水线不变量：** 比例只在生成阶段选一次。源画布是唯一真相源；4K 成品永远只是源图的 Lanczos3 重缩放——不重新提示词、不拉伸、不透明补边。

### 验证流程

三个硬校验门控每个成功的任务。任一失败，任务即失败——**绝无静默损坏**。

<img src="docs/images/verification.png" alt="验证流程图" width="640">

只有当三者都成立，任务才标记 `succeeded`：

1. **尺寸精确** —— 成品像素精确匹配请求的 `--size`
2. **比例锁定** —— 源图与成品交叉乘积相等（`srcW×finalH == finalW×srcH`）
3. **SHA-256 校验** —— 下载文件哈希等于服务端 manifest

---

## ✨ 核心能力

<table>
  <tr>
    <td width="50%" align="center" valign="top">
      <h3>🎯 精确比例引擎</h3>
      <p><b>无拉伸。无变形。</b></p>
      <p>源图与成品共享严格一致的整数像素比。</p>
    </td>
    <td width="50%" align="center" valign="top">
      <h3>🖼 双资产输出</h3>
      <p><b>源图 + 4K。</b></p>
      <p>每个任务都产出原始画布<em>和</em>放大后成品。</p>
    </td>
  </tr>
  <tr>
    <td width="50%" align="center" valign="top">
      <h3>🔍 验证层</h3>
      <p><b>SHA-256 验证资产。</b></p>
      <p>下载字节校对 manifest。尺寸精确断言。</p>
    </td>
    <td width="50%" align="center" valign="top">
      <h3>🤖 Agent 原生</h3>
      <p><b>Claude · Codex · Cursor · MCP。</b></p>
      <p>Skill 规范 + MCP 服务器。6 个类型化工具。</p>
    </td>
  </tr>
</table>

---

## 🤖 通过 AI 助手使用（MCP）

完成[方式二](#方式二本地引擎批量-4k或用-mcp)后，把这段加进 AI 工具的 MCP 配置：

```json
{
  "command": "node",
  "args": ["/你的路径/generate-image-asset/engine/mcp-server.mjs"],
  "env": {
    "IMAGE_TASK_API_URL": "http://127.0.0.1:9789",
    "IMAGE_TASK_API_TOKEN": "你-env-local-里的-token"
  }
}
```

助手获得**六个类型化工具**：

| 工具 | 用途 |
|---|---|
| `image_asset_upload(path)` | 上传本地 PNG，返回资产 ID + manifest |
| `image_job_create(...)` | 创建幂等生成任务 |
| `image_job_get(jobId)` | 读取状态 + 事件 |
| `image_job_wait(jobId, timeoutMs)` | 最多等待 30 分钟 |
| `image_job_cancel(jobId)` | 取消排队中或进行中的任务 |
| `image_asset_download(assetId, outputPath)` | 独占写入下载（绝不静默覆盖） |

---

## 🔀 两种模型模式

| 模型类型 | `--model` | `--api-mode` | 示例 |
|---|---|---|---|
| 图像模型 | `gpt-image-2` 等 | `images` | 专用图像模型（最常见） |
| 文本模型 | `gpt-5.6-sol` 等 | `responses` | 通过 Responses API 输出图像的对话模型 |

**关键：** 模型和 api-mode 必须匹配。图像模型用 `images`，文本模型用 `responses`。不匹配报错（如 *"requires an image model"*）。

---

## 📋 常用参数

| 参数 | 默认值 | 说明 |
|---|---|---|
| `--backend` | `built-in` | `built-in`（Agent 自带工具）/ `task-api`（本仓库引擎） |
| `--prompt-file` | — | 提示词文本文件路径（长提示词用） |
| `--size` | `2160x3840` | 最终尺寸，同时决定比例 |
| `--model` | `gpt-image-2` | 模型名 |
| `--api-mode` | `images` | `images` 或 `responses` |
| `--provider` | `mock` | `configured`（用 `.env.local` 真实配置） |
| `--quality` | `high` | 图像质量 |
| `--content-class` | `photo` | `photo` / `illustration` / `text` / `logo` / `ui` |
| `--enhancement` | `auto` | 放大算法，`lanczos3` 最常用 |
| `--max-attempts` | `3` | 失败重试次数（1-5） |
| `--out` | `output/.../output.png` | 输出路径 |
| `--force` | 关 | 覆盖已存在文件（不加此标记会拒绝） |

**支持比例：** `1:1` · `3:2` · `2:3` · `16:9` · `9:16` · `4:3` · `3:4` · `21:9`

---

## ✅ 验证安装

```bash
npm test
```

预期：**20 个测试通过**（用 mock provider，不需要真实 API key）。这是确认引擎、契约、验证逻辑在你机器上正常的最快方式。

---

## ❓ 常见问题

**`npm install` 失败 / sharp 编译不过？**
确保 Node.js 22+。Windows 装 Visual Studio Build Tools，macOS 装 Xcode Command Line Tools。详见 [sharp 安装文档](https://sharp.pixelplumbing.com/install)。

**"generation base size conflicts with the requested composition ratio"？**
请求了不支持的比例（如 `4:5`）。用上面列出的支持比例。`--size` 宽高比必须能约分为支持的比例。

**"requires an image model" 错误？**
文本模型（如 `gpt-5.6-sol`）配了 `--api-mode images`。改成 `--api-mode responses`。

**方式一装完 Skill 还需要引擎吗？**
不需要。Skill 默认用 `built-in` 后端，直接调 Agent 自带的图像工具出图，然后本地做比例校验和放大。引擎是可选的批量/自动化升级。

---

## 📁 项目结构

```
generate-image-asset/
├── engine/                          # 生成引擎（Task API）
│   ├── service.mjs                  # 核心：任务调度、比例校验、缩放
│   ├── cli.mjs                      # 入口（npm run engine）
│   ├── mcp-server.mjs               # MCP 服务器（npm run mcp）
│   └── service.test.mjs             # 引擎测试（npm test）
├── scripts/
│   ├── run_image_job.py             # Skill CLI 入口
│   └── image_core_cli.mjs           # 几何计算 CLI
├── vendor/image-job-core/           # 共享契约实现（比例、尺寸、验证）
├── SKILL.md                         # Agent Skill 规范
├── package.json
└── .env.local                       # 你的密钥（gitignored）
```

---

## 🔗 相关

引擎是 [TaoStudio Image Lab](https://github.com/wanghao137/taostudio-image-lab) Task API 的可发布镜像，共享同一份 Image Job Contract v1。通过同步脚本保持一致。

---

## English

**Production-grade AI image asset pipeline for Agents.** Generate once, receive: original source image + exact 4K production asset + verification report.

**Install:** `npx skills add wanghao137/image-asset-pipeline` (Skill only, uses your agent's built-in image tool), or `git clone` + `npm install` + `npm run engine` for the local engine + MCP.

**Two model modes:** `--api-mode images` for image models (gpt-image-2), `--api-mode responses` for text models that emit images (gpt-5.6-sol).

**Verified outputs:** every job is gated by three hard checks — exact dimensions, ratio invariant (`srcW×finalH == finalW×srcH`), and SHA-256 checksum against the server manifest. Run `npm test` to verify (20 tests, mock provider, no key needed).

See the Chinese sections above for full parameter reference, MCP config, and FAQ.

---

<div align="center">

一次生成，三件产出。
原图不丢，4K 精确，验证可审。

</div>

---

## 📜 许可证

[MIT](./LICENSE) —— 可商用，保留版权声明即可。
