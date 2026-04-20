# 飞书输出插件（知识库文档 + 消息卡片）

from __future__ import annotations

import json
import logging
import time
from typing import Any

import httpx

from ..core.base import BaseOutput
from ..core.models import ContentItem, HubEvent

logger = logging.getLogger(__name__)


class FeishuOutput(BaseOutput):
    """飞书输出 — 知识库文档 + 群消息卡片

    配置项：
        app_id: str - 飞书App ID
        app_secret: str - 飞书App Secret
        chat_id: str - 群聊ID（发消息卡片）
        wiki_space_id: str - 知识库空间ID（发文档）
        daily_card: bool - 是否启用日报卡片（默认True）
    """

    name = "feishu"
    display_name = "飞书"

    API_BASE = "https://open.feishu.cn/open-apis"

    def validate_config(self) -> bool:
        return bool(self.config.get("app_id") and self.config.get("app_secret"))

    async def write(self, items: list[ContentItem]) -> int:
        """写入内容到飞书知识库"""
        wiki_space_id = self.config.get("wiki_space_id", "")
        if not wiki_space_id:
            logger.warning("未配置飞书知识库空间ID，跳过知识库写入")
            return 0

        token = await self._get_token()
        count = 0

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            for item in items:
                try:
                    await self._create_wiki_doc(client, token, wiki_space_id, item)
                    count += 1
                except Exception as e:
                    logger.error(f"写入飞书知识库 {item.id} 失败: {e}")

        return count

    async def notify(self, event: HubEvent) -> bool:
        """发送飞书通知（消息卡片或文本）"""
        chat_id = self.config.get("chat_id", "")
        if not chat_id:
            return False

        token = await self._get_token()

        if event.type == "daily_summary":
            return await self._send_daily_card(token, chat_id, event)
        else:
            return await self._send_text(token, chat_id, event.summary)

    async def _get_token(self) -> str:
        """获取tenant_access_token"""
        app_id = self.config.get("app_id", "")
        app_secret = self.config.get("app_secret", "")

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.post(
                f"{self.API_BASE}/auth/v3/tenant_access_token/internal",
                json={"app_id": app_id, "app_secret": app_secret},
            )
            data = resp.json()
            if data.get("code") == 0:
                return data["tenant_access_token"]
            raise Exception(f"获取飞书token失败: {data}")

    async def _send_text(self, token: str, chat_id: str, text: str) -> bool:
        """发送文本消息"""
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.post(
                f"{self.API_BASE}/im/v1/messages",
                params={"receive_id_type": "chat_id"},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "text",
                    "content": json.dumps({"text": text}),
                },
            )
            data = resp.json()
            return data.get("code") == 0

    async def _send_daily_card(self, token: str, chat_id: str, event: HubEvent) -> bool:
        """发送日报消息卡片"""
        card = self._build_daily_card(event.data)
        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            resp = await client.post(
                f"{self.API_BASE}/im/v1/messages",
                params={"receive_id_type": "chat_id"},
                headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
                json={
                    "receive_id": chat_id,
                    "msg_type": "interactive",
                    "content": json.dumps(card),
                },
            )
            data = resp.json()
            return data.get("code") == 0

    def _build_daily_card(self, data: dict) -> dict:
        """构建日报卡片"""
        stats = data.get("stats", {})
        highlights = data.get("highlights", [])

        columns = []
        for channel_name, count in stats.items():
            icons = {
                "bilibili": "📺", "wechat": "📰", "zsxq": "🌐",
                "getnote": "📝", "zhihu": "💡", "quick_note": "✍️",
            }
            icon = icons.get(channel_name, "📄")
            columns.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": f"**{icon} {channel_name}**\n+{count}"}
            })

        elements = []
        if columns:
            elements.append({
                "tag": "column_set",
                "flex_mode": "bisect",
                "background_style": "default",
                "columns": [
                    {"tag": "column", "width": "weighted", "weight": 1, "elements": columns[i:i+2]}
                    for i in range(0, len(columns), 2)
                ],
            })

        if highlights:
            elements.append({"tag": "hr"})
            elements.append({
                "tag": "div",
                "text": {"tag": "lark_md", "content": "**🔥 今日热点**\n" + "\n".join(f"• {h}" for h in highlights[:5])}
            })

        elements.append({"tag": "hr"})
        elements.append({"tag": "note", "elements": [{"tag": "plain_text", "content": "AI Content Hub 自动推送"}]})

        return {
            "config": {"wide_screen_mode": True, "enable_forward": True},
            "header": {
                "title": {"tag": "plain_text", "content": "📡 AI Content Hub 日报"},
                "template": "indigo",
            },
            "elements": elements,
        }

    async def _create_wiki_doc(self, client, token, space_id, item: ContentItem) -> None:
        """创建飞书知识库文档"""
        # 飞书知识库API较复杂，这里只做基础实现
        resp = await client.post(
            f"{self.API_BASE}/wiki/v2/spaces/{space_id}/nodes",
            headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
            json={
                "title": item.title,
                "content": item.to_markdown(),
            },
        )
        if resp.status_code != 200:
            logger.warning(f"创建飞书知识库文档失败: {resp.status_code}")
