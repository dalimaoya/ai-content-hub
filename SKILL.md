---
name: ai-content-hub
version: 0.1.0
description: |
  个人知识采集中枢。自动采集B站收藏、微信文章、知识星球、Get笔记、知乎、小红书等多平台内容，统一入库并同步到Obsidian/Notion/飞书。
  支持随笔记录（灵感/纪要/密码/待办等8种分类自动入库）。
  当用户发送微信文章链接、B站视频链接、知乎链接、小红书链接时自动触发解析入库。
  当用户说"扫B站收藏"/"扫描知识星球"/"记一下"/"收藏这篇文章"等时触发。
  触发词：微信文章、公众号文章、解析文章、收藏文章、B站收藏、B站视频、视频字幕、
  知识星球、Get笔记、录音笔记、已保存文章、知乎、小红书、随笔、灵感、纪要、待办、
  记一下、收藏、采集、scan、parse、note、内容中心、AI Content Hub
---

# AI Content Hub Skill

> 你的收藏不该积灰。自动采集散落在各平台的内容，统一入库、一键同步。

## 安装

### 首次安装（必须执行）

```bash
pip install ai-content-hub[all]
```

如果只需要部分通道：

```bash
pip install ai-content-hub[bilibili,wechat,zsxq,getnote,quicknote]
```

### 初始化配置（首次安装后必须执行）

```bash
ai-content-hub init
```

这会交互式引导用户配置：
1. 数据存储路径
2. 启用哪些采集通道
3. 配置各通道的认证信息（Cookie/Token/API Key）
4. 配置输出目标（Obsidian/Notion/飞书）

**重要：init 命令会逐项询问配置，请引导用户完成。**

### 验证安装

```bash
ai-content-hub status
```

如果显示各通道状态表格，说明安装成功。

## 使用方式

### 1. 链接触发（用户发链接时自动解析）

当用户发送以下类型的链接时，自动识别并解析入库：

| URL模式 | 通道 | 命令 |
|---------|------|------|
| `mp.weixin.qq.com` | 微信文章 | `ai-content-hub parse "URL"` |
| `bilibili.com/video/` | B站视频 | `ai-content-hub parse "URL"` |
| `BVxxxxxx` | B站视频 | `ai-content-hub parse "URL"` |
| `zhihu.com` | 知乎 | `ai-content-hub parse "URL"` |
| `xiaohongshu.com` | 小红书 | `ai-content-hub parse "URL"` |

**示例**：用户说 "帮我收藏这篇微信文章 https://mp.weixin.qq.com/s/xxx"
→ 执行 `ai-content-hub parse "https://mp.weixin.qq.com/s/xxx"`

### 2. 定时扫描

```bash
# 扫描所有已启用通道
ai-content-hub scan

# 扫描指定通道
ai-content-hub scan --channel bilibili
ai-content-hub scan --channel zsxq --full    # 全量扫描
ai-content-hub scan --channel getnote
```

### 3. 随笔记录

```bash
# AI自动分类
ai-content-hub note "突然想到一个点子"          # → 💡 灵感
ai-content-hub note "会议决定了三件事..."        # → 📋 纪要
ai-content-hub note "记得明天带U盘"              # → ✅ 待办

# 指定分类
ai-content-hub note "密码：admin123" --category credential
ai-content-hub note "https://example.com" --category forward
```

8种分类：`idea` 灵感 | `meeting` 纪要 | `credential` 密码(加密) | `forward` 临时转发(7天过期) | `todo` 待办 | `bookmark` 书签 | `diary` 日记 | `quote` 摘录

### 4. 同步到知识库

```bash
ai-content-hub sync --obsidian    # 同步到Obsidian
ai-content-hub sync --notion      # 同步到Notion
ai-content-hub sync --feishu      # 同步到飞书
```

### 5. 查看状态

```bash
ai-content-hub status
```

## 通道配置说明

### 📺 B站（需扫码登录）

首次使用需要扫码登录获取凭证：

```bash
# 启动扫码登录（会弹出二维码）
python -c "from ai_content_hub.channels.bilibili import BilibiliChannel; ..."
```

配置项：
- `credential_path`: bilibili_api凭证JSON文件路径
- `uid`: B站用户UID

### 📰 微信文章（无需配置）

直接发链接即可，`ai-content-hub parse "URL"` 自动解析。

### 🌐 知识星球

配置项：
- `access_token`: 知识星球Cookie中的zsxq_access_token

获取方式：浏览器登录知识星球 → F12 → Application → Cookies → 复制 zsxq_access_token

### 📝 Get笔记

配置项：
- `api_key`: Get笔记开放平台API Key
- `client_id`: Get笔记Client ID

获取方式：https://www.biji.com/openapi

### 💡 知乎 / 📕 小红书

配置项：
- `cookie`: 浏览器登录后的Cookie

获取方式：浏览器登录 → F12 → Network → 任意请求 → 复制Cookie

## 定时任务建议

| 通道 | 建议频率 |
|------|---------|
| B站 | 每4小时 |
| 知识星球 | 每2小时 |
| Get笔记 | 每2小时 |
| RSS | 每6小时 |

## 故障排查

- **Cookie过期**：重新获取Cookie/Token，更新config.yaml
- **B站扫码失败**：确认bilibili-api-python已安装 `pip install bilibili-api-python`
- **微信文章解析失败**：确认readability-lxml已安装 `pip install readability-lxml`
- **小红书风控**：增大请求间隔 `channels.xiaohongshu.delay: 5`
- **知识星球返回空**：检查access_token是否过期

## 项目地址

https://github.com/dalimaoya/ai-content-hub
