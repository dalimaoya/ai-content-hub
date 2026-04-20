<div align="center">

# 📡 AI Content Hub

**你的收藏不该积灰。**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

[English](#english) · 中文

</div>

---

## 😩 你是不是也这样？

> 在B站收藏了视频，想着「以后看」——**再也没打开过**
>
> 在微信看到好文章，转发到文件传输助手——**淹没在聊天记录里**
>
> 在知乎点了赞同，在小红书收藏了笔记——**想找的时候不记得在哪个平台**
>
> 偶尔记下灵感，随手丢到备忘录——**三天后就忘了备忘录在哪**
>
> 收藏越来越多，整理越来越少。**不是不想整理，是根本没时间。**

**AI Content Hub 就是解决这个问题的。**

它自动采集你散落在各平台的内容，统一入库、一键同步到你的知识库。你只管收藏，整理交给它。

## ✨ 它能做什么

| 🔄 自动采集 | 🔗 发链接即入库 | ✍️ 随时记录 |
|:---:|:---:|:---:|
| 定时扫描B站收藏、知识星球、Get笔记 | 发一个URL，自动识别平台、解析全文 | 灵感/纪要/待办，一句话自动分类入库 |
| 8个平台全覆盖 | 微信文章/知乎回答/小红书笔记 | 8种分类，AI自动推断 |
| | | 🔐 密码类加密存储，📎 临时转发7天过期 |

| 📤 统一输出 | 🤖 AI助手直连 |
|:---:|:---:|
| 本地Markdown / Obsidian | MCP Server，AI助手直接调用 |
| Notion Database | 发一条消息就能采集，说一句话就能记录 |
| 飞书知识库 + 群卡片 | |

## 🚀 安装

### 方式一：一句话让AI助手帮你装（推荐 ✨）

如果你在用任何支持 MCP 或 Skill 的 AI 助手，只需**复制下面这句话发给它**，它会自动帮你完成安装、配置、验证：

> 📋 **复制这条信息发给你的AI助手：**
>
> ```
> 帮我安装 ai-content-hub：pip install ai-content-hub[all]，然后运行 ai-content-hub init 引导我配置。项目文档在 https://github.com/dalimaoya/ai-content-hub
> ```

**支持这个安装方式的AI助手**（持续增加中）：

| AI 助手 | 安装方式 | 说明 |
|---------|---------|------|
| 🦞 **OpenClaw（小龙虾）** | 发消息 → 自动安装 | 开源AI Agent，6.8万⭐，ClawHub 1700+技能 |
| 🏛️ **Hermes Agent** | 发消息 → 自动安装 | 自进化AI Agent，4.7万⭐，自动生成Skill |
| 🐧 **QClaw（企鹅龙虾）** | 发消息 → 自动安装 | 腾讯出品，微信直连，零门槛 |
| 💼 **WorkBuddy** | 发消息 → 自动安装 | 腾讯桌面智能体，兼容龙虾Skills + MCP |
| 🤖 **Claude Desktop** | MCP模式 | Anthropic官方客户端，MCP原生支持 |
| 🔧 **Cursor** | MCP模式 | AI IDE，配置MCP Server后可用 |
| 🌊 **Windsurf** | MCP模式 | AI IDE，配置MCP Server后可用 |
| 📝 **Cline / Roo Code** | MCP模式 | VS Code插件，配置MCP Server后可用 |

> 💡 **原理**：这些AI助手都能理解自然语言指令，执行终端命令，读取项目文档并引导你完成配置。你只需要说一句话，剩下的交给它。

### 方式二：命令行安装

```bash
# 安装（按需选择通道）
pip install ai-content-hub[bilibili,wechat,zsxq,getnote]

# 初始化配置（交互式引导）
ai-content-hub init

# 快速模式（只启用免配置通道，30秒上手）
ai-content-hub init --quick

# 开始采集！
ai-content-hub scan
```

### 方式三：MCP 模式（给AI客户端装上采集能力）

适合 Claude Desktop、Cursor、Cline 等 MCP 客户端：

```bash
# 启动MCP Server
ai-content-hub mcp
```

然后在你的 AI 客户端配置中添加 MCP Server 地址，就能直接用自然语言控制采集了。

<details>
<summary>📖 Claude Desktop 配置示例</summary>

编辑 `~/Library/Application Support/Claude/claude_desktop_config.json`（macOS）或 `%APPDATA%\Claude\claude_desktop_config.json`（Windows）：

```json
{
  "mcpServers": {
    "ai-content-hub": {
      "command": "ai-content-hub",
      "args": ["mcp"]
    }
  }
}
```

</details>

<details>
<summary>📖 Cursor / Windsurf / Cline 配置示例</summary>

在设置中找到 MCP Server 配置项，添加：

```json
{
  "mcpServers": {
    "ai-content-hub": {
      "command": "ai-content-hub",
      "args": ["mcp"]
    }
  }
}
```

</details>

## 📡 支持的平台

| 平台 | 采集内容 | 认证方式 | 安装 |
|------|---------|---------|------|
| 📺 **B站** | 收藏视频、CC字幕 | 扫码登录 | `[bilibili]` |
| 📰 **微信文章** | 公众号全文 | 无需认证 | `[wechat]` |
| 🌐 **知识星球** | 主题、评论 | Cookie Token | `[zsxq]` |
| 📝 **Get笔记** | 笔记、录音转文字 | API Key | `[getnote]` |
| 💡 **知乎** | 收藏、赞同、想法 | Cookie | `[zhihu]` |
| 📕 **小红书** | 收藏笔记 | Cookie | `[xiaohongshu]` |
| 🎵 **抖音** | 收藏视频 | Cookie | `[douyin]` |
| 📺 **YouTube** | 订阅、字幕 | API Key | `[youtube]` |
| 📡 **RSS** | 博客、Newsletter | 无需认证 | `[rss]` |
| ✍️ **随笔记录** | 灵感/纪要/待办等 | 无需认证 | `[quicknote]` |
| 💬 **微信聊天** | 本地聊天记录 | 本地数据库 | `[wechat-chat]` |

> 💡 **不知道装哪个？** 先装 `[bilibili,wechat,quicknote]` 这三个最常用、免配置的。其他的等需要时再加。

## 🎬 使用示例

### 定时扫描（全自动，不用管它）

```bash
# 扫描所有已启用通道
ai-content-hub scan

# 只扫B站
ai-content-hub scan --channel bilibili

# 首次全量扫描
ai-content-hub scan --channel zsxq --full
```

### 发链接即入库

```bash
# 微信文章
ai-content-hub parse "https://mp.weixin.qq.com/s/xxxxx"

# 知乎回答
ai-content-hub parse "https://www.zhihu.com/question/123/answer/456"

# 小红书笔记
ai-content-hub parse "https://www.xiaohongshu.com/explore/abc123"
```

### 随手记录（AI自动分类）

```bash
# 不指定分类，AI自动推断
ai-content-hub note "突然想到可以用RAG做自动标签"    # → 💡 灵感
ai-content-hub note "会议决定了三件事：1. ... 2. ..."  # → 📋 纪要
ai-content-hub note "记得明天带U盘"                    # → ✅ 待办

# 指定分类
ai-content-hub note "JWT Token: eyJhbG..." --category credential
ai-content-hub note "https://example.com" --category forward
```

| 分类 | 说明 | 特殊处理 |
|------|------|---------|
| 💡 `idea` | 闪念、创意 | — |
| 📋 `meeting` | 会议纪要 | — |
| 🔐 `credential` | 密码、Token | **加密存储，不同步Obsidian** |
| 📎 `forward` | 临时转发 | **7天自动过期** |
| ✅ `todo` | 待办 | — |
| 🔖 `bookmark` | 稍后看 | — |
| 📔 `diary` | 日记 | — |
| 📖 `quote` | 金句 | — |

### 同步到知识库

```bash
# 同步到Obsidian（本地Markdown文件）
ai-content-hub sync --obsidian

# 同步到Notion
ai-content-hub sync --notion

# 同步到飞书
ai-content-hub sync --feishu
```

### 在AI助手中使用（MCP模式）

如果你的AI助手已配置MCP Server，直接用自然语言：

| 你说的话 | AI助手做的事 |
|---------|------------|
| "扫一下我的B站收藏" | 调用 `scan_channel` |
| "帮我存这篇文章" + URL | 调用 `parse_url` |
| "记一下：明天开会" | 调用 `quick_note` |
| "我之前收藏过关于RAG的内容吗" | 调用 `search_content` |
| "今天有什么新内容" | 调用 `get_daily_summary` |
| "目前收了多少内容" | 调用 `get_status` |

## 🏗️ 架构

```
你收藏的内容
    │
    ├── 📺 B站    ──┐
    ├── 📰 微信   ──┤
    ├── 🌐 星球   ──┤     ┌─────────────┐     ┌──────────────┐
    ├── 📝 Get笔记 ──┼────→│ AI Content  │────→│ 📁 Obsidian  │
    ├── 💡 知乎   ──┤     │    Hub      │     │ 📝 Notion    │
    ├── 📕 小红书 ──┤     │ 统一采集    │     │ 💬 飞书      │
    ├── ✍️ 随笔   ──┤     │ 统一格式    │     └──────────────┘
    └── 💬 微信聊天 ──┘     │ 自动去重    │
                          │  ┃ MCP     │
                          │  ┃ Server  │──→ AI助手直接调用
                          └─────────────┘
```

**核心设计**：

- **插件化** — 每个通道/输出都是独立插件，按需安装
- **统一数据模型** — `ContentItem` 是唯一格式，存/搜/输出只写一套
- **MCP原生** — 内置MCP Server，AI助手开箱即用
- **事件驱动** — 采集完成、新内容入库等事件交给你的AI助手处理
- **零侵入** — 通知走Agent原生通道，不强绑定任何IM

## 🔌 自定义通道

新增一个采集通道只需 ~100 行代码：

```python
from ai_content_hub.core.base import BaseChannel
from ai_content_hub.core.models import ContentItem, ContentType, Channel

class MyChannel(BaseChannel):
    name = "my-channel"
    display_name = "我的通道"

    def validate_config(self) -> list[str]:
        return [] if self.config.get("api_key") else ["API Key未配置"]

    async def scan(self, full: bool = False):
        async for item in self._fetch_items():
            yield item

    async def parse(self, url: str) -> ContentItem | None:
        return item
```

注册到 `pyproject.toml`：

```toml
[project.entry-points."ai_content_hub.channels"]
my-channel = "my_package:MyChannel"
```

详见 [CONTRIBUTING.md](CONTRIBUTING.md)。

## 🐳 Docker

```bash
docker build -t ai-content-hub .
docker run -v ./config:/app/config -v ./data:/app/data ai-content-hub

# 或用 docker-compose
docker compose up -d
```

## ⚠️ 注意事项

- **Cookie/Token 会过期** — B站、知乎、小红书的Cookie有效期有限，失效后需更新
- **反爬风控** — 小红书和知乎反爬较严，已内置2秒请求间隔
- **微信聊天记录** — 仅 Windows，需微信登录状态，首次需运行 [PyWxDump](https://github.com/xaoyaoo/PyWxDump) 解密
- **数据安全** — `credential` 分类的随笔加密存储，不同步到Obsidian
- **合规使用** — 仅采集你有合法访问权限的内容

## 🙏 致谢

- [OpenClaw](https://github.com/openclaw/openclaw) — 开源AI Agent框架
- [Hermes Agent](https://github.com/NousResearch/Hermes-Agent) — 自进化AI Agent
- [bilibili-api-python](https://github.com/Nemo2011/bilibili-api) — B站API SDK
- [PyWxDump](https://github.com/xaoyaoo/PyWxDump) — 微信数据库解密
- [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) — 多平台采集参考
- [readability-lxml](https://github.com/buriy/python-readability) — 网页正文提取
- [MCP](https://modelcontextprotocol.io) — Model Context Protocol

## 📄 License

[MIT](LICENSE)

---

<a id="english"></a>

# AI Content Hub

**Your bookmarks shouldn't gather dust.**

You bookmark videos on Bilibili, save articles on WeChat, upvote answers on Zhihu... but they're scattered everywhere, impossible to find when you need them.

AI Content Hub automatically collects content from all your platforms, unifies it into one place, and syncs to your knowledge base.

## Install

### Option 1: One Sentence to Your AI Assistant (Recommended ✨)

If you're using any AI assistant that supports MCP or Skills, just **send this message** — it will handle installation, configuration, and verification for you:

> 📋 **Copy and send to your AI assistant:**
>
> ```
> Install ai-content-hub for me: pip install ai-content-hub[all], then run ai-content-hub init to guide me through setup. Docs: https://github.com/dalimaoya/ai-content-hub
> ```

**Works with** (and growing):

| AI Assistant | How | Notes |
|-------------|-----|-------|
| 🦞 **OpenClaw** | Send message → auto install | Open-source AI Agent, 68k⭐, 1700+ skills |
| 🏛️ **Hermes Agent** | Send message → auto install | Self-improving AI Agent, 47k⭐ |
| 🐧 **QClaw** | Send message → auto install | By Tencent, WeChat integration |
| 💼 **WorkBuddy** | Send message → auto install | By Tencent, OpenClaw Skills + MCP compatible |
| 🤖 **Claude Desktop** | MCP mode | Anthropic's official client |
| 🔧 **Cursor** | MCP mode | AI IDE with MCP support |
| 🌊 **Windsurf** | MCP mode | AI IDE with MCP support |
| 📝 **Cline / Roo Code** | MCP mode | VS Code extensions with MCP |

### Option 2: Command Line

```bash
pip install ai-content-hub[bilibili,wechat,quicknote]
ai-content-hub init
ai-content-hub scan
```

### Option 3: MCP Mode

```bash
ai-content-hub mcp
```

Then add the MCP Server to your AI client's configuration.

## Supported Platforms

8 channels: Bilibili · WeChat · Zsxq · GetNote · Zhihu · Xiaohongshu · QuickNote · WeChatChat

3 outputs: Local Markdown (Obsidian) · Notion · Feishu

MCP Server with 6 tools for AI client integration.

## License

[MIT](LICENSE)
