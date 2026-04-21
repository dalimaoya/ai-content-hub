# AI Content Hub 数据模型

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Channel(str, Enum):
    """采集通道枚举"""
    BILIBILI = "bilibili"
    WECHAT = "wechat"
    ZSXQ = "zsxq"
    GETNOTE = "getnote"
    ZHIHU = "zhihu"
    XIAOHONGSHU = "xiaohongshu"
    DOUYIN = "douyin"
    YOUTUBE = "youtube"
    RSS = "rss"
    QUICK_NOTE = "quick_note"
    WECHAT_CHAT = "wechat_chat"


class ContentType(str, Enum):
    """内容类型枚举"""
    VIDEO = "video"
    ARTICLE = "article"
    NOTE = "note"
    TOPIC = "topic"
    AUDIO = "audio"
    IMAGE = "image"
    CHAT = "chat"
    ANSWER = "answer"       # 知乎回答
    PIN = "pin"             # 知乎想法
    POST = "post"           # 小红书笔记


class QuickNoteCategory(str, Enum):
    """随笔记录分类"""
    IDEA = "idea"               # 💡 灵感
    MEETING = "meeting"         # 📋 纪要
    CREDENTIAL = "credential"   # 🔐 密码
    FORWARD = "forward"         # 📎 临时转发
    TODO = "todo"               # ✅ 待办
    BOOKMARK = "bookmark"       # 🔖 书签
    DIARY = "diary"             # 📔 日记
    QUOTE = "quote"             # 📖 摘录


@dataclass
class ContentItem:
    """统一内容数据模型 — 所有通道的输出都是这个格式"""
    # 必填
    id: str                                     # 唯一标识（如 "bilibili_BV1xx"）
    title: str                                  # 标题
    content: str                                # 正文/摘要/转写文本
    channel: Channel                            # 来源通道
    content_type: ContentType                   # 内容类型

    # 可选
    url: str = ""                               # 原始链接
    author: str = ""                            # 作者/UP主
    created_at: str = ""                        # 内容创建时间
    collected_at: str = ""                      # 采集时间
    tags: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)  # 通道特有字段

    # 随笔记录扩展字段（仅 quick_note 通道使用）
    category: str = ""                          # QuickNoteCategory 值
    ttl_days: int = 0                           # 过期天数（0=永久）
    is_encrypted: bool = False                  # 是否加密存储
    is_sensitive: bool = False                  # 是否敏感（不同步Obsidian）

    def to_dict(self) -> dict[str, Any]:
        """转为字典"""
        return {
            "id": self.id,
            "title": self.title,
            "content": self.content,
            "channel": self.channel.value,
            "content_type": self.content_type.value,
            "url": self.url,
            "author": self.author,
            "created_at": self.created_at,
            "collected_at": self.collected_at,
            "tags": self.tags,
            "metadata": self.metadata,
            "category": self.category,
            "ttl_days": self.ttl_days,
            "is_encrypted": self.is_encrypted,
            "is_sensitive": self.is_sensitive,
        }

    @staticmethod
    def _format_iso(iso_str: str) -> str:
        """将ISO时间格式转为人类可读格式
        
        2026-03-31T18:50:53.396+0800 → 2026-03-31 18:50:53
        2026-04-17T21:29:54Z → 2026-04-17 21:29:54
        2026-04-20 23:14:43 → 2026-04-20 23:14:43 (已可读，直接返回)
        """
        if not iso_str or "T" not in iso_str:
            return iso_str
        try:
            parts = iso_str.split("T")
            date_part = parts[0]
            time_part = parts[1].split(".")[0].split("+")[0].rstrip("Z")
            return f"{date_part} {time_part}"
        except Exception:
            return iso_str

    def to_markdown(self) -> str:
        """转为Markdown格式"""
        from datetime import datetime

        lines = []
        lines.append(f"# {self.title}")
        lines.append("")

        # 元信息
        meta_parts = [
            f"通道: {self.channel.value}",
            f"类型: {self.content_type.value}",
        ]
        if self.author:
            meta_parts.append(f"作者: {self.author}")
        if self.created_at:
            meta_parts.append(f"创建: {self._format_iso(self.created_at)}")
        if self.url:
            meta_parts.append(f"[原文链接]({self.url})")

        lines.append(f"> {' | '.join(meta_parts)}")
        lines.append("")

        # 标签
        if self.tags:
            lines.append(f"标签: {', '.join(self.tags)}")
            lines.append("")

        lines.append("---")
        lines.append("")

        # 正文
        if self.content:
            lines.append(self.content)

        lines.append("")
        lines.append("---")
        lines.append(f"*由AI Content Hub从{self.channel.value}采集*")

        return "\n".join(lines)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ContentItem:
        """从字典创建"""
        channel = data.pop("channel", Channel.BILIBILI)
        content_type = data.pop("content_type", ContentType.ARTICLE)
        if isinstance(channel, str):
            channel = Channel(channel)
        if isinstance(content_type, str):
            content_type = ContentType(content_type)
        return cls(channel=channel, content_type=content_type, **data)


@dataclass
class HubEvent:
    """Content Hub 产出的事件"""
    type: str               # scan_complete | new_content | daily_summary | error
    channel: str            # 通道名
    summary: str            # 事件摘要（人可读）
    data: dict[str, Any] = field(default_factory=dict)  # 结构化数据
    level: str = "info"     # info | warn | error
    timestamp: str = ""     # ISO格式时间戳

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.type,
            "channel": self.channel,
            "summary": self.summary,
            "data": self.data,
            "level": self.level,
            "timestamp": self.timestamp,
        }
