# 随笔记录通道

from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import AsyncIterator

from ..core.base import BaseChannel
from ..core.models import Channel, ContentItem, ContentType, QuickNoteCategory

logger = logging.getLogger(__name__)

# 自动分类规则
AUTO_CLASSIFY_RULES: list[tuple[str, list[str]]] = [
    ("credential", [r"密码", r"账号", r"token", r"api.?key", r"secret", r"凭证"]),
    ("idea", [r"想法", r"灵感", r"创意", r"做一个", r"如果.*能", r"突然想到"]),
    ("todo", [r"待办", r"记得", r"别忘了", r"TODO", r"要做", r"需要做"]),
    ("meeting", [r"会议", r"讨论", r"纪要", r"决定", r"确认"]),
    ("bookmark", [r"http", r"链接", r"收藏", r"看看"]),
    ("quote", [r"摘录", r"金句", r"引用", r"说.*好"]),
    ("forward", [r"转发", r"稍后", r"待处理"]),
    ("diary", [r"今天", r"心情", r"感觉", r"开心", r"难过"]),
]


class QuickNoteChannel(BaseChannel):
    """随笔记录通道

    功能：快速记录随笔，自动分类入库
    8种分类：灵感/纪要/密码/临时转发/待办/书签/日记/摘录
    """

    name = "quick_note"
    display_name = "随笔记录"

    def validate_config(self) -> bool:
        """随笔记录无需额外配置"""
        return True

    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """扫描过期的临时转发，标记为expired"""
        # 随笔记录没有定时扫描需求，但可以扫描过期内容
        return
        yield  # make it an async generator

    async def parse(self, url_or_id: str) -> ContentItem | None:
        """随笔记录不支持URL解析"""
        return None

    async def create(
        self,
        content: str,
        category: str = "",
        tags: list[str] | None = None,
        ttl_days: int = 0,
    ) -> ContentItem:
        """创建随笔记录

        Args:
            content: 记录内容
            category: 分类（为空则自动推断）
            tags: 标签列表
            ttl_days: 过期天数（0=永久）

        Returns:
            ContentItem
        """
        # 自动分类
        if not category:
            category = self._auto_classify(content)

        # 验证分类
        valid_categories = [c.value for c in QuickNoteCategory]
        if category not in valid_categories:
            category = "idea"  # 默认归为灵感

        now = datetime.now()

        # 生成ID
        from hashlib import md5
        item_id = f"qn_{md5((content + now.isoformat()).encode()).hexdigest()[:12]}"

        # 敏感内容标记
        is_sensitive = category in ("credential", "forward")
        is_encrypted = category == "credential"

        # 标题：取内容第一行
        title = content.split("\n")[0][:60] if content else "随笔"

        return ContentItem(
            id=item_id,
            title=title,
            content=content,
            channel=Channel.QUICK_NOTE,
            content_type=ContentType.NOTE,
            created_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            collected_at=now.strftime("%Y-%m-%d %H:%M:%S"),
            tags=tags or [],
            category=category,
            ttl_days=ttl_days,
            is_encrypted=is_encrypted,
            is_sensitive=is_sensitive,
            metadata={
                "category": category,
                "ttl_days": ttl_days,
            },
        )

    @staticmethod
    def _auto_classify(content: str) -> str:
        """基于内容特征自动推断分类"""
        content_lower = content.lower()
        for category, patterns in AUTO_CLASSIFY_RULES:
            for pattern in patterns:
                if re.search(pattern, content_lower):
                    return category
        return "idea"  # 默认归为灵感

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "config_valid": True,
            "categories": [c.value for c in QuickNoteCategory],
        }
