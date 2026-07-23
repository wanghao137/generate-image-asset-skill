# Generate Image Asset

一个**自包含**的图像生成工具包：一句话提示词 → 比例精确、可校验的高清 PNG。

本仓库集成了生成图片所需的全部组件，**只需 clone 这一个仓库**：

| 组件 | 给谁用 | 入口 |
|---|---|---|
| **Skill（命令行）** | 喜欢敲命令行、写脚本的人 | `scripts/run_image_job.py` |
| **MCP server** | Cursor / Claude 等 AI 助手 | `engine/mcp-server.mjs` |
| **引擎（Task API）** | 上面两个都靠它干活 | `engine/cli.mjs`（`npm run engine`） |

支持两种生成模型：
- **图像模型**（如 `gpt-image-2`）→ Images API
- **文本模型**（如 `gpt-5.6-sol`）→ Responses API（通过 `image_generation` 工具出图）

无论哪种模型，最终产物都满足同一套硬性约束：源图与成品图严格同比例、精确目标尺寸、SHA-256 可校验、无透明黑边、绝不拉伸。

---

## 快速开始

### 环境要求

- [Node.js](https://nodejs.org/) 22+（引擎用到了内置的实验性 SQLite）
- [Python](https://python.org/) 3.10+（Skill 命令行工具）
- 一个 OpenAI 兼容的图像生成 API（自备地址和密钥）

> **关于 sharp**：引擎用 sharp 做图像缩放，它是 native 库，首次 `npm install` 会编译（约 30-60 秒，需要系统有基本构建工具）。这是本仓库唯一的"重"依赖。

### 第 1 步：获取并安装

```bash
git clone https://github.com/wanghao137/generate-image-asset-skill.git
cd generate-image-asset-skill/generate-image-asset
npm install
```

### 第 2 步：配置（只需一次）

在仓库根目录创建 `.env.local` 文件（**这个文件不要分享、不要上传，里面有密钥**）：

```dotenv
# 本地服务的访问令牌（你自己随便编一串长字符）
IMAGE_TASK_API_TOKEN=把这里换成一串随机字符

# 生图引擎监听端口
IMAGE_TASK_API_PORT=9789

# 你的图像生成 API 配置
IMAGE_TASK_PROVIDER_BASE_URL=https://你的API地址/v1
IMAGE_TASK_PROVIDER_API_KEY=你的密钥
IMAGE_TASK_PROVIDER_MODEL=gpt-image-2
```

### 第 3 步：启动引擎

```bash
npm run engine
```

看到 `TaoStudio Image Task API listening at http://127.0.0.1:9789` 就说明引擎就绪。**这个窗口要一直开着**——关了就不能生图了。

### 第 4 步：生成第一张图

新开一个终端，进入仓库目录：

```bash
# Windows
set IMAGE_TASK_API_TOKEN=你在第2步设的令牌
py -3 scripts\run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt "一只橘色猫咪在京都町家,午后阳光,写实摄影" --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png
```

```bash
# macOS / Linux
export IMAGE_TASK_API_TOKEN=你在第2步设的令牌
python3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 --prompt "一只橘色猫咪在京都町家,午后阳光,写实摄影" --model gpt-image-2 --api-mode images --provider configured --size 2160x3840 --quality high --out my-image.png
```

成功后会生成：
- `my-image.png`：最终的高清大图（精确目标尺寸）
- `my-image-source.png`：原始比例的源图
- `my-image.report.json`：生成报告（尺寸、SHA-256、manifest）

---

## 用法二：通过 AI 助手（MCP）

如果你用 Cursor、Claude Desktop 等支持 MCP 的 AI 工具，可以让 AI 直接帮你生图。

先按上面的步骤 1-3 装好并启动引擎，然后在你的 AI 工具的 MCP 配置里填：

```json
{
  "command": "node",
  "args": ["/你clone的路径/generate-image-asset/engine/mcp-server.mjs"],
  "env": {
    "IMAGE_TASK_API_URL": "http://127.0.0.1:9789",
    "IMAGE_TASK_API_TOKEN": "你在第2步设的令牌"
  }
}
```

配好后，AI 助手会获得 6 个能力：上传图片、创建任务、查询状态、等待完成、取消任务、下载图片（不会偷偷覆盖已有文件）。

---

## 两种模型怎么选

| 模型类型 | `--model` | `--api-mode` | 例子 |
|---|---|---|---|
| 图像模型 | `gpt-image-2` 等 | `images` | 专门的生图模型（最常见） |
| 文本模型 | `gpt-5.6-sol` 等 | `responses` | 能出图的对话模型 |

**关键**：模型和 api-mode 必须配套。图像模型用 `images`，文本模型用 `responses`，选错会报错。

文本模型生图示例：

```bash
py -3 scripts/run_image_job.py --backend task-api --api-url http://127.0.0.1:9789 \
  --prompt "极简科技品牌横幅插画" \
  --model gpt-5.6-sol --api-mode responses --provider configured \
  --size 2880x2880 --quality high --out my-image.png
```

---

## 常用参数

| 参数 | 默认 | 说明 |
|---|---|---|
| `--backend` | `built-in` | `task-api`（推荐，用本仓库引擎） |
| `--prompt-file` | - | 提示词文件路径（长提示词用这个） |
| `--prompt` | - | 直接传提示词 |
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

---

## 验证安装

跑测试确认引擎工作正常（不需要真实 API key，用 mock）：

```bash
npm test
```

预期：20 个测试全部通过。

---

## 常见问题

**`npm install` 报错 / sharp 编译失败？**
sharp 是 native 库。确保 Node 22+，Windows 需装 Visual Studio Build Tools，macOS 需 Xcode Command Line Tools。详见 [sharp 安装文档](https://sharp.pixelplumbing.com/install)。

**生成失败提示 "requires an image model"？**
你用文本模型（如 `gpt-5.6-sol`）却选了 `--api-mode images`。改成 `--api-mode responses`。

**生成失败提示 "connection refused"？**
引擎没启动，或地址/端口不对。先确认 `npm run engine` 在跑，`--api-url` 地址和 `.env.local` 里的端口一致。

**提示 "output exists; pass --force"？**
输出文件已存在，工具拒绝覆盖。换个文件名，或加 `--force` 确认覆盖。

**令牌怎么传？**
用环境变量 `IMAGE_TASK_API_TOKEN`，不要写进命令行参数（会留在命令历史里）。`.env.local` 已被 `.gitignore` 排除。

**图变形/有黑边？**
不会的。引擎强制保证源图和成品图严格同比例，绝不拉伸或补黑边。这是核心设计。

---

## 项目结构

```
generate-image-asset/
├── engine/                          # 生图引擎（Task API）
│   ├── service.mjs                  # 引擎核心：任务调度、比例校验、缩放
│   ├── cli.mjs                      # 启动入口（npm run engine）
│   ├── mcp-server.mjs               # MCP server（npm run mcp）
│   └── service.test.mjs             # 引擎测试（npm test）
├── scripts/
│   ├── run_image_job.py             # Skill 命令行入口
│   └── image_core_cli.mjs           # 几何计算 CLI
├── vendor/image-job-core/           # 共享契约实现（比例、尺寸、校验）
├── references/adversarial-review.md
├── agents/openai.yaml
├── package.json
└── .env.local                       # 你的密钥（不上传）
```

---

## 与 TaoStudio Image Lab 的关系

本仓库的引擎是 [TaoStudio Image Lab](https://github.com/wanghao137/taostudio-image-lab) 中 Task API 的可发布镜像，复用同一套 Image Job Contract。TaoStudio Image Lab 是完整的网页应用（含前端），本仓库抽取了其中的生图引擎和工具，让外部用户无需拉取整个网页项目即可使用。

引擎代码通过同步脚本保持与主仓库一致。

---

## 许可证

[MIT](./LICENSE) — 免费、可商用，保留版权声明即可。
