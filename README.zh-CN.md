[English](./README.md) | **[简体中文](./README.zh-CN.md)**

<p align="center">
  <img src="docs/images/hero.png" alt="Generate Image Asset" width="720">
</p>

<h1 align="center">Generate Image Asset</h1>

<p align="center">
  <em>一句话提示词 → 比例精确、可校验的高清 PNG。<br>自包含工具包：命令行 Skill + MCP 服务 + 生图引擎。</em>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg?style=flat-square" alt="License: MIT"></a>
  <img src="https://img.shields.io/badge/Node.js-22+-339933.svg?style=flat-square&logo=node.js&logoColor=white" alt="Node">
  <img src="https://img.shields.io/badge/Python-3.10+-3776AB.svg?style=flat-square&logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/gpt--image--2-支持-FF6B6B.svg?style=flat-square" alt="gpt-image-2">
  <img src="https://img.shields.io/badge/MCP-兼容-1e1e2e.svg?style=flat-square" alt="MCP">
  <img src="https://img.shields.io/badge/平台-跨平台-lightgrey.svg?style=flat-square" alt="Platform">
</p>

---

<p align="center">
  <img src="docs/images/gallery-photo.png" width="190" alt="写实示例">
  &nbsp;
  <img src="docs/images/gallery-product.png" width="150" alt="产品示例">
  &nbsp;
  <img src="docs/images/gallery-illustration.png" width="240" alt="插画示例">
  &nbsp;
  <img src="docs/images/gallery-text.png" width="150" alt="文字海报示例">
</p>

<p align="center"><sub>以上图廊均由本工具通过 <code>gpt-image-2</code> 生成。</sub></p>

---

## ✨ 这是什么

一个命令行图像生成工具包，把一句提示词变成一张经过校验的 PNG——**精确目标尺寸、严格继承比例、SHA-256 可校验**。一个仓库包含全部组件，无需额外安装引擎。

**三个组件，一次 clone 搞定：**

| 组件 | 给谁用 | 入口 |
|---|---|---|
| 🖥️ **Skill（命令行）** | 开发者、脚本、自动化 | `scripts/run_image_job.py` |
| 🤖 **MCP 服务** | Cursor / Claude 等 AI 助手 | `engine/mcp-server.mjs` |
| ⚙️ **引擎（Task API）** | 真正负责生成图片的后端 | `npm run engine` |

## 🎯 为什么用它

直接调图像 API 有三个常见坑，本工具全部解决：

| 问题 | 直接调 API | 本工具 |
|---|---|---|
| **比例变形** | API 返回的画布比例和目标不一致 → 强行拉伸就变形 | 强制整数像素比例精确匹配，绝不拉伸 |
| **尺寸不对** | 要 4K，API 只给 1K，自己放大又模糊 | 从比例匹配的源图做 Lanczos3 放大 |
| **透明黑边** | `contain` 模式产生留白边 | 用 `cover` 几何——满幅无黑边 |

**工作原理：**

```
提示词 + 目标尺寸
  → 调 Provider 生成原始画布
  → 用 cover 裁切成精确整数比例的"源图"PNG
  → 用 Lanczos3 放大到目标尺寸（保持比例，不重选）
  → 输出 source + final + 校验报告
```

每个产物都有保证：源图和成品图比例完全相同（`源图宽 × 成品高 == 成品宽 × 源图高`），成品像素精确匹配请求，下载文件的 SHA-256 与 manifest 一致。

## 🚀 快速开始

### 环境要求

- [Node.js](https://nodejs.org/) 22+
- [Python](https://python.org/) 3.10+
- 一个 OpenAI 兼容的图像生成 API（自备地址和密钥）

> **关于 sharp：** 引擎用 sharp 做图像缩放，它是 native 库，首次 `npm install` 会编译（约 30-60 秒）。这是唯一的"重"依赖。

### 安装

```bash
git clone https://github.com/wanghao137/generate-image-asset-skill.git
cd generate-image-asset-skill/generate-image-asset
npm install
```

### 配置（只需一次）

在仓库根目录创建 `.env.local` 文件（**这个文件不要分享、不要上传，里面有密钥**）：

```dotenv
IMAGE_TASK_API_TOKEN=你自己随便编一串长字符当令牌
IMAGE_TASK_API_PORT=9789
IMAGE_TASK_PROVIDER_BASE_URL=https://你的API地址/v1
IMAGE_TASK_PROVIDER_API_KEY=你的密钥
IMAGE_TASK_PROVIDER_MODEL=gpt-image-2
```

### 启动引擎

```bash
npm run engine
```

看到 `TaoStudio Image Task API listening at http://127.0.0.1:9789` 就说明引擎就绪。**这个窗口要一直开着。**

### 生成第一张图

新开一个终端：

```bash
# Windows
set IMAGE_TASK_API_TOKEN=你在上一步设的令牌
py -3 scripts\run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt "一只橘色猫咪在木缘侧上,午后阳光,写实摄影" --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png

# macOS / Linux
export IMAGE_TASK_API_TOKEN=你在上一步设的令牌
python3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt "一只橘色猫咪在木缘侧上,午后阳光,写实摄影" --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png
```

成功后会生成：
- `my-image.png`：最终的高清大图（精确目标尺寸）
- `my-image-source.png`：源图画布（原始比例，放大前）
- `my-image.report.json`：生成报告（尺寸、SHA-256、manifest）

## 🤖 通过 AI 助手使用（MCP）

如果你用 Cursor、Claude Desktop 等支持 MCP 的 AI 工具，可以让 AI 直接帮你生图。按上面的步骤装好并启动引擎后，在你的 AI 工具的 MCP 配置里加：

```json
{
  "command": "node",
  "args": ["/你的路径/generate-image-asset/engine/mcp-server.mjs"],
  "env": {
    "IMAGE_TASK_API_URL": "http://127.0.0.1:9789",
    "IMAGE_TASK_API_TOKEN": "你在.env.local里设的令牌"
  }
}
```

AI 助手会获得 6 个能力：上传图片、创建任务、查询状态、等待完成、取消任务、下载图片（不会静默覆盖已有文件）。

## 🔀 两种模型模式

| 模型类型 | `--model` | `--api-mode` | 例子 |
|---|---|---|---|
| 图像模型 | `gpt-image-2` 等 | `images` | 专门的生图模型（最常见） |
| 文本模型 | `gpt-5.6-sol` 等 | `responses` | 能出图的对话模型 |

**关键**：模型和 api-mode 必须配套。图像模型用 `images`，文本模型用 `responses`，选错会报错。

文本模型生图示例：

```bash
python3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 \
  --prompt "极简科技品牌横幅插画" \
  --model gpt-5.6-sol --api-mode responses --provider configured \
  --size 2880x2880 --quality high --out my-image.png
```

## 📋 常用参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--backend` | `built-in` | `task-api`（推荐，用本仓库引擎） |
| `--prompt-file` | — | 提示词文件路径（长提示词用这个） |
| `--prompt` | — | 直接传提示词 |
| `--size` | `2160x3840` | 最终尺寸，同时决定比例 |
| `--model` | `gpt-image-2` | 模型名 |
| `--api-mode` | `images` | `images` 或 `responses` |
| `--provider` | `mock` | `configured`（用 .env.local 里的真实配置） |
| `--quality` | `high` | 画质 |
| `--content-class` | `photo` | `photo`/`illustration`/`text`/`logo`/`ui` |
| `--enhancement` | `auto` | 放大算法，`lanczos3` 最常用 |
| `--max-attempts` | `3` | 失败重试次数（1-5） |
| `--out` | `output/.../output.png` | 输出路径 |
| `--force` | 关 | 覆盖已有同名文件（不加则拒绝覆盖） |

## ✅ 验证安装

跑测试确认引擎工作正常（用 mock，不需要真实 API key）：

```bash
npm test
```

预期：20 个测试全部通过。

## ❓ 常见问题

**`npm install` 报错 / sharp 编译失败？**
sharp 是 native 库。确保 Node 22+。Windows 需装 Visual Studio Build Tools，macOS 需 Xcode Command Line Tools。详见 [sharp 安装文档](https://sharp.pixelplumbing.com/install)。

**"requires an image model" 错误？**
你用文本模型（如 `gpt-5.6-sol`）却选了 `--api-mode images`。改成 `--api-mode responses`。

**"connection refused" 错误？**
引擎没启动，或地址/端口不对。确认 `npm run engine` 在跑，`--api-url` 地址和 `.env.local` 里的端口一致。

**"output exists; pass --force" 提示？**
输出文件已存在，工具拒绝覆盖。换个文件名，或加 `--force` 确认覆盖。

**令牌怎么传？**
用环境变量 `IMAGE_TASK_API_TOKEN`，不要写进命令行参数（会留在命令历史里）。`.env.local` 已被 `.gitignore` 排除。

## 📁 项目结构

```
generate-image-asset/
├── engine/                          # 生图引擎（Task API）
│   ├── service.mjs                  # 引擎核心：任务调度、比例校验、缩放
│   ├── cli.mjs                      # 启动入口（npm run engine）
│   ├── mcp-server.mjs               # MCP 服务（npm run mcp）
│   └── service.test.mjs             # 引擎测试（npm test）
├── scripts/
│   ├── run_image_job.py             # Skill 命令行入口
│   └── image_core_cli.mjs           # 几何计算 CLI
├── vendor/image-job-core/           # 共享契约实现（比例、尺寸、校验）
├── references/adversarial-review.md
├── agents/openai.yaml
├── package.json
└── .env.local                       # 你的密钥（已 gitignore）
```

## 🔗 相关

本仓库的引擎是 [TaoStudio Image Lab](https://github.com/wanghao137/taostudio-image-lab) 中 Task API 的可发布镜像，复用同一套 Image Job Contract。TaoStudio Image Lab 是完整的网页应用；本仓库抽取了其中的生图引擎和工具，让外部用户无需拉取整个网页项目。

引擎代码通过同步脚本保持与主仓库一致。

## 📜 许可证

[MIT](./LICENSE) — 免费、可商用，保留版权声明即可。
