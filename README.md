<div align="center">

# 📡 AI Content Hub

**个人知识采集中枢 — 把散落在各平台的内容，统一采集、整理、同步到你的知识库**

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP Compatible](https://img.shields.io/badge/MCP-Compatible-green.svg)](https://modelcontextprotocol.io)

</div>

---

## ✨ 这是什么

你在B站收藏了视频、在微信看到了好文章、在知乎点了赞同、在小红书收藏了笔记……但它们散落在各处，永远也找不回来。

**AI Content Hub** 解决这个问题：

- 🔄 **自动采集** — 定时扫描你的B站收藏、知识星球、Get笔记等
- 🔗 **链接触发** — 发一个URL，自动识别通道、解析入库
- ✍️ **随笔记录** — 随时记录灵感/纪要/待办，自动分类入库
- 📤 **统一输出** — 本地Markdown/Obsidian、Notion、飞书知识库
- 🤖 **MCP Server** — 任何AI客户端（Claude/ChatGPT/OpenClaw）都能直接调用

## 🚀 快速开始

### 安装

```bash
# 基础安装（只有核心引擎）
pip install ai-content-hub

# 按需安装通道
pip install ai-content-hub[bilibili,wechat]

# 全部通道
pip install ai-content-hub[all]
```

### 初始化

```bash
# 交互式配置向导
ai-content-hub init

# 或手动创建配置文件
cp config/config.example.yaml config/config.yaml
```

### 使用

```bash
# 扫描所有已启用通道
ai-content-hub scan

# 扫描指定通道
ai-content-hub scan --channel bilibili
ai-content-hub scan --channel zsxq --full  # 全量扫描

# 解析URL（自动识别通道）
ai-content-hub parse "https://mp.weixin.qq.com/s/xxxxx"
ai-content-hub parse "https://www.zhihu.com/question/123/answer/456"
ai-content-hub parse "https://www.xiaohongshu.com/explore/abc123"

# 随笔记录
ai-content-hub note "突然想到：用AI自动生成读书笔记的思维导图"
ai-content-hub note "明天给客户发方案" --category todo
ai-content-hub note "密码：admin123" --category credential --tags "服务器"

# 同步到输出目标
ai-content-hub sync --obsidian
ai-content-hub sync --notion --feishu

# 查看状态
ai-content-hub status

# 启动MCP Server（供AI客户端调用）
ai-content-hub mcp
```

## 📡 支持的平台

| 平台 | 采集内容 | 安装 | 认证方式 |
|------|---------|------|---------|
| 📺 **B站** | 收藏视频、CC字幕、Whisper转录 | `[bilibili]` | 扫码登录 |
| 📰 **微信文章** | 公众号文章解析 | `[wechat]` | 无需认证 |
| 🌐 **知识星球** | 主题、评论 | `[zsxq]` | Cookie Token |
| 📝 **Get笔记** | 笔记同步、录音转文字 | `[getnote]` | API Key |
| 💡 **知乎** | 收藏、赞同、想法 | `[zhihu]` | Cookie |
| 📕 **小红书** | 收藏笔记 | `[xiaohongshu]` | Cookie |
| 🎵 **抖音** | 收藏视频 | `[douyin]` | Cookie |
| 📺 **YouTube** | 订阅、字幕 | `[youtube]` | API Key |
| 📡 **RSS** | 博客、Newsletter | `[rss]` | 无需认证 |
| ✍️ **随笔记录** | 灵感/纪要/密码/待办/书签/日记/摘录/临时转发 | `[quicknote]` | 无需认证 |
| 💬 **微信聊天** | 本地聊天记录解析 | `[wechat-chat]` | 本地数据库 |

## 📤 输出目标

| 目标 | 说明 | 安装 |
|------|------|------|
| 📁 **本地 Markdown** | 内置，Obsidian友好目录结构 | — |
| 📝 **Notion** | 每通道一个Database | `[notion]` |
| 💬 **飞书知识库** | 文档 + 群卡片通知 | `[feishu]` |

## ✍️ 随笔记录 — 8种分类自动入库

```bash
# 不指定分类，AI自动推断
ai-content-hub note "突然想到可以用RAG做..."
# → 💡 灵感

ai-content-hub note "会议决定了三件事：1. ... 2. ... 3. ..."
# → 📋 纪要

ai-content-hub note "记得明天带U盘"
# → ✅ 待办

# 指定分类
ai-content-hub note "JWT Token: eyJhbG..." --category credential
ai-content-hub note "https://example.com/article" --category forward
ai-content-hub note "读《原则》有感：痛苦+反思=进步" --category diary
```

| 分类 | 场景 | 特殊处理 |
|------|------|---------|
| 💡 `idea` | 闪念、创意 | — |
| 📋 `meeting` | 会议、对话纪要 | — |
| 🔐 `credential` | 账号Token密码 | **加密存储** |
| 📎 `forward` | 临时转发链接 | **7天TTL自动过期** |
| ✅ `todo` | 待办事项 | — |
| 🔖 `bookmark` | 稍后看 | — |
| 📔 `diary` | 日记、心得 | — |
| 📖 `quote` | 金句、摘录 | — |

## 🤖 MCP Server

AI Content Hub 可以作为 MCP Server 运行，让任何 AI 客户端直接调用采集能力：

```bash
# 启动MCP Server
ai-content-hub mcp
```

**提供的工具：**

| 工具 | 说明 |
|------|------|
| `scan_channel` | 扫描指定通道的新内容 |
| `parse_url` | 解析URL，自动识别通道 |
| `quick_note` | 快速记录随笔 |
| `get_status` | 查看各通道状态 |
| `get_daily_summary` | 获取今日内容摘要 |
| `search_content` | 搜索已入库内容 |

**在 OpenClaw/Hermes/QClaw 中使用：**

只需将本项目 GitHub 地址提供给 Agent，Agent 会自动识别 SKILL.md 并安装。

## 🐳 Docker

```bash
# 构建镜像
docker build -t ai-content-hub .

# 运行MCP Server
docker run -v ./config:/app/config -v ./data:/app/data -p 8765:8765 ai-content-hub

# 使用docker-compose
docker compose up -d
```

## 🏗️ 架构

```
┌─────────────────────────────────────────────────┐
│                  AI Content Hub                  │
├─────────────────────────────────────────────────┤
│  采集层 (Channels)     │  输出层 (Outputs)       │
│  ┌─────────────┐      │  ┌─────────────┐       │
│  │ Bilibili    │      │  │ Local MD    │       │
│  │ WeChat      │      │  │ (Obsidian)  │       │
│  │ Zsxq        │──────│─→│ Notion      │       │
│  │ GetNote     │      │  │ Feishu      │       │
│  │ Zhihu       │      │  └─────────────┘       │
│  │ Xiaohongshu │      │                         │
│  │ QuickNote   │      │  事件层 (Events)        │
│  │ WechatChat  │      │  → HubEvent             │
│  │ ...         │      │  → 通知/摘要/日报       │
│  └─────────────┘      │                         │
├─────────────────────────────────────────────────┤
│  核心层: ContentItem + BaseChannel + BaseOutput  │
│  存储层: 统一JSON索引 + 去重 + Markdown文件      │
│  插件层: entry_points 自动发现                    │
└─────────────────────────────────────────────────┘
```

**核心设计原则：**

- **插件化** — 每个通道/输出都是独立插件，`pip install` 按需安装
- **统一数据模型** — `ContentItem` 是唯一数据格式，存储/搜索/输出只写一套
- **两步入库** — `scan()` 采集 + `parse()` 深解析，解耦速度和深度
- **事件驱动** — 采集完成、新内容入库等事件由 Agent 决定如何通知

## 🔌 自定义通道

新增一个采集通道只需 ~100 行代码：

```python
from ai_content_hub.core.base import BaseChannel
from ai_content_hub.core.models import ContentItem, ContentType

class MyChannel(BaseChannel):
    name = "my-channel"
    display_name = "我的通道"
    description = "采集XXX内容"

    def validate_config(self) -> list[str]:
        errors = []
        if not self.config.get("api_key"):
            errors.append("API Key未配置")
        return errors

    async def scan(self, full: bool = False):
        # 实现采集逻辑
        async for item in self._fetch_items():
            yield item

    async def parse(self, url: str) -> ContentItem | None:
        # 实现URL解析逻辑
        return item
```

然后在 `pyproject.toml` 注册：

```toml
[project.entry-points."ai_content_hub.channels"]
my-channel = "my_package:MyChannel"
```

## 📂 项目结构

```
ai-content-hub/
├── src/ai_content_hub/
│   ├── core/                   # 核心层
│   │   ├── models.py           # ContentItem + HubEvent
│   │   ├── base.py             # BaseChannel + BaseOutput
│   │   ├── registry.py         # 插件注册表
│   │   ├── config.py           # 配置管理
│   │   └── storage.py          # 统一存储
│   ├── channels/               # 采集通道
│   │   ├── bilibili.py
│   │   ├── wechat.py
│   │   ├── zsxq.py
│   │   ├── getnote.py
│   │   ├── quicknote.py
│   │   ├── zhihu.py
│   │   ├── xiaohongshu.py
│   │   └── wechat_chat.py
│   ├── outputs/                # 输出目标
│   │   ├── local_md.py
│   │   ├── notion_output.py
│   │   └── feishu_output.py
│   ├── mcp/
│   │   └── server.py           # MCP Server
│   └── cli.py                  # CLI入口
├── config/
│   └── config.example.yaml
├── tests/
├── Dockerfile
├── docker-compose.yml
└── pyproject.toml
```

## ⚠️ 注意事项

- **Cookie/Token 定期失效** — B站、知乎、小红书的Cookie有效期有限，需定期更新
- **反爬风控** — 小红书和知乎反爬较严，建议降低扫描频率（默认2秒间隔）
- **微信聊天记录** — 仅支持 Windows，且需要微信登录状态
- **数据安全** — `credential` 分类的随笔记录使用加密存储，不同步到Obsidian
- **合规使用** — 请仅采集自己拥有合法访问权限的内容

## 📄 License

[MIT](LICENSE)

## 🙏 致谢

- [bilibili-api-python](https://github.com/Nemo2011/bilibili-api) — B站API SDK
- [PyWxDump](https://github.com/xaoyaoo/PyWxDump) — 微信数据库解密
- [MediaCrawler](https://github.com/NanmiCoder/MediaCrawler) — 多平台采集参考
- [readability-lxml](https://github.com/buriy/python-readability) — 网页正文提取
- [MCP](https://modelcontextprotocol.io) — Model Context Protocol
