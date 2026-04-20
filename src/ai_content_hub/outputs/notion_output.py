# Notion输出插件

from __future__ import annotations

import logging
from typing import Any

from ..core.base import BaseOutput
from ..core.models import ContentItem

logger = logging.getLogger(__name__)


class NotionOutput(BaseOutput):
    """Notion输出 — 每通道一个Database，每条内容一个Page

    配置项：
        api_key: str - Notion Integration Token
        databases: dict - 通道到Database ID的映射（空=自动创建）
        parent_page_id: str - 父页面ID（新建Database的位置）
    """

    name = "notion"
    display_name = "Notion"

    def validate_config(self) -> bool:
        return bool(self.config.get("api_key"))

    async def write(self, items: list[ContentItem]) -> int:
        """写入内容到Notion"""
        try:
            from notion_client import AsyncClient
        except ImportError:
            raise ImportError("请安装: pip install ai-content-hub[notion]")

        api_key = self.config.get("api_key", "")
        if not api_key:
            logger.error("未配置Notion API Key")
            return 0

        async with AsyncClient(auth=api_key) as client:
            count = 0
            for item in items:
                try:
                    db_id = await self._get_or_create_db(client, item.channel.value)
                    await self._create_page(client, db_id, item)
                    count += 1
                except Exception as e:
                    logger.error(f"写入Notion {item.id} 失败: {e}")
            return count

    async def setup(self) -> dict:
        """初始化Notion Databases"""
        try:
            from notion_client import AsyncClient
        except ImportError:
            return {"name": self.name, "status": "error", "error": "notion-client未安装"}

        api_key = self.config.get("api_key", "")
        parent_page_id = self.config.get("parent_page_id", "")

        async with AsyncClient(auth=api_key) as client:
            created = {}
            for channel_name in ["bilibili", "wechat", "zsxq", "getnote", "quick_note"]:
                db_id = await self._get_or_create_db(client, channel_name, parent_page_id)
                created[channel_name] = db_id

        return {"name": self.name, "status": "ready", "databases": created}

    async def _get_or_create_db(self, client, channel_name: str, parent_page_id: str = "") -> str:
        """获取或创建Database"""
        databases = self.config.get("databases", {})
        if channel_name in databases and databases[channel_name]:
            return databases[channel_name]

        # 创建新Database
        channel_display = {
            "bilibili": "📺 B站收藏",
            "wechat": "📰 微信文章",
            "zsxq": "🌐 知识星球",
            "getnote": "📝 Get笔记",
            "quick_note": "✍️ 随笔记录",
        }

        parent = parent_page_id or self.config.get("parent_page_id", "")
        if not parent:
            raise ValueError("未配置Notion parent_page_id，无法创建Database")

        db = await client.databases.create(
            parent={"page_id": parent},
            title=[{"type": "text", "text": {"content": channel_display.get(channel_name, channel_name)}}],
            properties={
                "标题": {"title": {}},
                "通道": {"select": {"options": []}},
                "类型": {"select": {"options": []}},
                "作者": {"rich_text": {}},
                "标签": {"multi_select": {"options": []}},
                "创建时间": {"date": {}},
                "URL": {"url": {}},
            },
        )
        return db["id"]

    async def _create_page(self, client, db_id: str, item: ContentItem) -> None:
        """创建Notion Page"""
        properties = {
            "标题": {"title": [{"text": {"content": item.title[:100]}}]},
            "通道": {"select": {"name": item.channel.value}},
            "类型": {"select": {"name": item.content_type.value}},
        }
        if item.author:
            properties["作者"] = {"rich_text": [{"text": {"content": item.author}}]}
        if item.url:
            properties["URL"] = {"url": item.url}
        if item.tags:
            properties["标签"] = {"multi_select": [{"name": t} for t in item.tags[:5]]}

        # 内容作为Page Body
        children = []
        if item.content:
            # Notion block有2000字限制，分段处理
            for i in range(0, len(item.content), 2000):
                children.append({
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {"rich_text": [{"text": {"content": item.content[i:i+2000]}}]},
                })

        await client.pages.create(
            parent={"database_id": db_id},
            properties=properties,
            children=children[:100],  # Notion限制100个block
        )
