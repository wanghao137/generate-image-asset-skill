# Generate Image Asset Skill

一个命令行图像生成工具：把一句提示词变成一张比例精确、可校验的高清 PNG。

支持两种生成后端：
- **图像模型**（如 `gpt-image-2`）→ Images API
- **文本模型**（如 `gpt-5.6-sol`）→ Responses API（通过 `image_generation` 工具出图）

无论哪种模型，最终产物都满足同一套硬性约束：源图与成品图严格同比例、精确目标尺寸、SHA-256 可校验、无透明黑边、绝不拉伸。

> 本工具是 [TaoStudio Image Lab](https://github.com/wanghao137/taostudio-image-lab) 的独立可发布子集，复用同一套 Image Job Contract，可脱离网页单独运行。

---

## 它解决什么问题

直接调图像 API 常遇到三个坑：
1. **比例变形**：API 返回的画布比例和你想要的不完全一致，强行拉伸就变形。
2. **尺寸不对**：要 4K（3840×2160），API 只给 1K，自己放大又模糊。
3. **黑边/留白**：用 contain 模式缩放会产生透明边。

本工具的流程保证规避这三点：

```
提示词 + 目标尺寸
  → 调 Provider 生成原始画布
  → 用 cover 裁切成精确整数比例的"规范源图"
  → 用 Lanczos3 放大到目标尺寸（只缩放，不重选比例）
  → 输出 source + final + 校验报告
```

---

## 安装

### 环境要求

- [Node.js](https://nodejs.org/) 18+
- [Python](https://python.org/) 3.10+
- 一个 OpenAI 兼容的图像生成 API（自备地址和密钥）

### 获取代码

```bash
git clone https://github.com/wanghao137/generate-image-asset-skill.git
cd generate-image-asset-skill/generate-image-asset
```

无需安装依赖——`run_image_job.py` 只用 Python 标准库，几何计算由内置的 `vendor/image-job-core`（纯 JS，无原生依赖）提供。

---

## 使用

### 第 1 步：启动 Task API（生图引擎）

本工具需要一个运行中的 [Task API](https://github.com/wanghao137/taostudio-image-lab) 作为后端。在 TaoStudio Image Lab 仓库里：

```bash
# 配置（在 .env.local 里，这个文件不要分享）
IMAGE_TASK_API_TOKEN=随便编一串长字符当令牌
IMAGE_TASK_API_PORT=9789
IMAGE_TASK_PROVIDER_BASE_URL=https://你的API地址/v1
IMAGE_TASK_PROVIDER_API_KEY=你的密钥
IMAGE_TASK_PROVIDER_MODEL=gpt-image-2

# 启动
npm run task-api
```

看到 `listening at http://127.0.0.1:9789` 就说明引擎就绪。

### 第 2 步：写提示词

把想要的内容存成 UTF-8 文本文件，比如 `prompt.txt`：
```
一只橘色猫咪蜷缩在京都町家木缘侧上，午后阳光，写实摄影
```

### 第 3 步：生成

```bash
# Windows
set IMAGE_TASK_API_TOKEN=你在上一步设的令牌
py -3 scripts\run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt-file prompt.txt --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png
```

```bash
# macOS / Linux
export IMAGE_TASK_API_TOKEN=你在上一步设的令牌
python3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt-file prompt.txt --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png
```

> 令牌通过环境变量 `IMAGE_TASK_API_TOKEN` 传入，**不要**用命令行参数传，避免泄露在命令历史里。

### 两种模型的写法

| 模型类型 | `--model` | `--api-mode` | 例子 |
|---|---|---|---|
| 图像模型 | `gpt-image-2` 等 | `images` | 专门的生图模型 |
| 文本模型 | `gpt-5.6-sol` 等 | `responses` | 能出图的对话模型 |

**关键**：模型和 api-mode 必须配套。图像模型用 `images`，文本模型用 `responses`，选错会报错。

---

## 输出文件

每次成功生成会产出（以 `--out my-image.png` 为例）：

| 文件 | 说明 |
|---|---|
| `my-image.png` | 最终的高清大图（精确目标尺寸） |
| `my-image-source.png` | 规范源图（原始比例，未经放大） |
| `my-image.report.json` | 生成报告：模型、尺寸、SHA-256、manifest |

报告里包含完整的校验信息，可用于追溯和验证图片未被篡改。

---

## 常用参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--backend` | `built-in` | `task-api`（推荐）或 `built-in`（仅 Codex 环境） |
| `--prompt-file` | - | 提示词文件路径（长提示词用这个） |
| `--prompt` | - | 直接传提示词（短的可以用） |
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

完整参数说明见 [`SKILL.md`](./SKILL.md)。

---

## 常见问题

**生成失败提示 "requires an image model"？**
你用文本模型（如 `gpt-5.6-sol`）却选了 `--api-mode images`。改成 `--api-mode responses`。

**生成失败提示 "connection refused"？**
Task API 没启动，或地址/端口不对。先确认 `npm run task-api` 在跑，地址和 `--api-url` 一致。

**提示 "output exists; pass --force"？**
输出文件已存在，工具拒绝覆盖（防止误删）。换个文件名，或加 `--force` 确认覆盖。

**令牌怎么传？**
用环境变量 `IMAGE_TASK_API_TOKEN`，不要写进命令行参数。`.env.local` 已被 `.gitignore` 排除。

---

## 项目结构

```
generate-image-asset/
├── SKILL.md                          # 完整能力说明（给 AI 助手读的）
├── scripts/
│   ├── run_image_job.py              # 主程序入口
│   └── image_core_cli.mjs            # 几何计算 CLI
├── vendor/image-job-core/            # 便携契约实现（与 Task API 同源）
│   ├── index.mjs
│   └── schemas/                      # 契约 schema
├── references/
│   └── adversarial-review.md         # 自检清单
└── agents/
    └── openai.yaml                   # Agent 集成配置
```

---

## 许可证

[MIT](./LICENSE) — 免费、可商用，保留版权声明即可。
