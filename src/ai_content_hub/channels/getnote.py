# Get笔记通道

from __future__ import annotations

import logging
from typing import AsyncIterator

import httpx

from ..core.base import BaseChannel
from ..core.models import Channel, ContentItem, ContentType

logger = logging.getLogger(__name__)


class GetNoteChannel(BaseChannel):
    """Get笔记同步通道

    功能：同步笔记（文本/链接/录音/图片）、语义搜索、知识库管理
    配置项：
        api_key: str - Get笔记API Key
        client_id: str - Get笔记Client ID
        sync_note_types: list - 同步的笔记类型（默认全部）
    """

    name = "getnote"
    display_name = "Get笔记"

    API_BASE = "https://openapi.biji.com/open/api/v1"

    NOTE_TYPE_MAP = {
        "plain_text": ContentType.NOTE,
        "link": ContentType.NOTE,
        "recorder_audio": ContentType.AUDIO,
        "img_text": ContentType.IMAGE,
    }

    NOTE_TYPE_LABELS = {
        "plain_text": "文本笔记",
        "link": "链接笔记",
        "recorder_audio": "录音笔记",
        "img_text": "图片笔记",
    }

    def validate_config(self) -> bool:
        return bool(self.config.get("api_key") and self.config.get("client_id"))

    def _get_headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.config.get('api_key', '')}",
            "X-Client-ID": self.config.get("client_id", ""),
        }

    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """同步Get笔记"""
        if not self.validate_config():
            logger.error("未配置Get笔记API Key或Client ID")
            return

        headers = self._get_headers()
        sync_types = self.config.get("sync_note_types", ["plain_text", "link", "recorder_audio", "img_text"])
        processed = set(self.config.get("_processed_ids", []))

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            cursor = 0
            while True:
                try:
                    resp = await client.get(
                        f"{self.API_BASE}/resource/note/list",
                        params={"since_id": cursor},
                        headers=headers,
                    )
                    if resp.status_code != 200:
                        break

                    data = resp.json()
                    if not data.get("success"):
                        break

                    notes = data.get("data", {}).get("notes", [])
                    if not notes:
                        break

                    for note in notes:
                        note_type = note.get("note_type", "")
                        if note_type not in sync_types:
                            continue

                        note_id = str(note.get("note_id", ""))
                        item_id = f"getnote_{note_id}"

                        if incremental and item_id in processed:
                            continue

                        title = note.get("title", "") or note.get("content", "")[:40].replace("\n", " ")
                        content = note.get("content", "")
                        created_at = note.get("created_at", "")

                        # 标签
                        tags = [t.get("name", "") for t in note.get("tags", []) if t.get("name")]

                        yield ContentItem(
                            id=item_id,
                            title=title,
                            content=content,
                            channel=Channel.GETNOTE,
                            content_type=self.NOTE_TYPE_MAP.get(note_type, ContentType.NOTE),
                            url="",
                            author="",
                            created_at=created_at,
                            tags=tags,
                            metadata={
                                "note_id": note_id,
                                "note_type": note_type,
                                "source": note.get("source", ""),
                            },
                        )

                    if not data.get("data", {}).get("has_more"):
                        break
                    cursor = data.get("data", {}).get("next_cursor", 0)

                except Exception as e:
                    logger.error(f"同步Get笔记失败: {e}")
                    break

    async def parse(self, url_or_id: str) -> ContentItem | None:
        """获取Get笔记详情"""
        if not self.validate_config():
            return None

        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                resp = await client.get(
                    f"{self.API_BASE}/resource/note/detail",
                    params={"id": url_or_id},
                    headers=headers,
                )
                if resp.status_code != 200:
                    return None

                data = resp.json()
                if not data.get("success"):
                    return None

                note = data.get("data", {}).get("note", {})
                note_id = str(note.get("note_id", ""))
                note_type = note.get("note_type", "")

                return ContentItem(
                    id=f"getnote_{note_id}",
                    title=note.get("title", ""),
                    content=note.get("content", ""),
                    channel=Channel.GETNOTE,
                    content_type=self.NOTE_TYPE_MAP.get(note_type, ContentType.NOTE),
                    created_at=note.get("created_at", ""),
                    metadata={"note_id": note_id, "note_type": note_type},
                )
        except Exception as e:
            logger.error(f"获取Get笔记详情失败: {e}")
            return None

    async def save_note(self, title: str, content: str, note_type: str = "plain_text",
                        topic_id: str = "") -> dict:
        """新建笔记（两步流程：先save再batch-add）"""
        headers = self._get_headers()

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            # Step 1: saveNote（不支持topic_ids！）
            resp = await client.post(
                f"{self.API_BASE}/resource/note/save",
                headers=headers,
                json={"note_type": note_type, "title": title, "content": content},
            )
            data = resp.json()

            if not data.get("success"):
                return data

            # Step 2: batchAddNotesToTopic（如果指定了知识库）
            if topic_id:
                note_id = str(data.get("data", {}).get("id", ""))
                if note_id:
                    await client.post(
                        f"{self.API_BASE}/resource/knowledge/note/batch-add",
                        headers=headers,
                        json={"topic_id": topic_id, "note_ids": [note_id]},
                    )

            return data

    async def search(self, query: str, top_k: int = 5) -> list[ContentItem]:
        """语义搜索笔记"""
        headers = self._get_headers()
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
                resp = await client.post(
                    f"{self.API_BASE}/resource/recall",
                    headers=headers,
                    json={"query": query, "top_k": top_k},
                )
                if resp.status_code != 200:
                    return []

                data = resp.json()
                results = data.get("data", {}).get("results", [])
                items = []
                for r in results:
                    items.append(ContentItem(
                        id=f"getnote_{r.get('note_id', '')}",
                        title=r.get("title", ""),
                        content=r.get("content", ""),
                        channel=Channel.GETNOTE,
                        content_type=ContentType.NOTE,
                        created_at=r.get("created_at", ""),
                    ))
                return items
        except Exception as e:
            logger.error(f"搜索Get笔记失败: {e}")
            return []

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "config_valid": self.validate_config(),
            "api_key_configured": bool(self.config.get("api_key")),
        }
