# 知识星球通道

from __future__ import annotations

import logging
from typing import AsyncIterator

import httpx

from ..core.base import BaseChannel
from ..core.models import Channel, ContentItem, ContentType

logger = logging.getLogger(__name__)


class ZsxqChannel(BaseChannel):
    """知识星球监测通道

    功能：扫描星球新主题、评论
    配置项：
        access_token: str - 知识星球Access Token
        group_ids: list - 要扫描的星球ID（空=全部）
    """

    name = "zsxq"
    display_name = "知识星球"

    API_BASE = "https://api.zsxq.com/v2"

    def validate_config(self) -> bool:
        return bool(self.config.get("access_token"))

    async def scan(self, incremental: bool = True) -> AsyncIterator[ContentItem]:
        """扫描知识星球新主题"""
        token = self.config.get("access_token", "")
        if not token:
            logger.error("未配置知识星球Access Token")
            return

        headers = {"Cookie": f"zsxq_access_token={token}"}
        processed = set(self.config.get("_processed_ids", []))
        target_groups = self.config.get("group_ids", [])

        async with httpx.AsyncClient(follow_redirects=True, timeout=30) as client:
            # 获取星球列表
            groups = await self._get_groups(client, headers)
            if not groups:
                return

            for group in groups:
                group_id = str(group.get("group_id", ""))
                group_name = group.get("name", "")

                if target_groups and group_id not in target_groups:
                    continue

                # 扫描主题
                page = 1
                while True:
                    try:
                        resp = await client.get(
                            f"{self.API_BASE}/groups/{group_id}/topics",
                            params={"scope": "all", "count": 20, "page": page},
                            headers=headers,
                        )
                        if resp.status_code != 200:
                            break

                        data = resp.json()
                        topics = data.get("resp_data", {}).get("topics", [])
                        if not topics:
                            break

                        for topic in topics:
                            topic_id = str(topic.get("topic_id", ""))
                            item_id = f"zsxq_{topic_id}"

                            if incremental and item_id in processed:
                                continue

                            # 提取内容
                            talk = topic.get("talk", {})
                            text = talk.get("text", "")
                            title = text[:60].replace("\n", " ") if text else "无标题"

                            # 提取作者
                            owner = talk.get("owner", {})
                            author = owner.get("name", "") if isinstance(owner, dict) else ""

                            # 提取时间
                            created = topic.get("create_time", "")

                            yield ContentItem(
                                id=item_id,
                                title=title,
                                content=text,
                                channel=Channel.ZSXQ,
                                content_type=ContentType.TOPIC,
                                url=f"https://wx.zsxq.com/topic/{topic_id}",
                                author=author,
                                created_at=created,
                                metadata={
                                    "group_id": group_id,
                                    "group_name": group_name,
                                    "topic_id": topic_id,
                                    "likes_count": topic.get("likes_count", 0),
                                    "comments_count": topic.get("comments_count", 0),
                                },
                            )

                        # 知识星球没有明确的has_more，用返回数量判断
                        if len(topics) < 20:
                            break
                        page += 1

                    except Exception as e:
                        logger.error(f"扫描星球 {group_name} 失败: {e}")
                        break

    async def parse(self, url_or_id: str) -> ContentItem | None:
        """知识星球暂不支持直接URL解析（需要登录态）"""
        logger.warning("知识星球暂不支持URL直接解析")
        return None

    async def _get_groups(self, client: httpx.AsyncClient, headers: dict) -> list:
        """获取星球列表"""
        try:
            resp = await client.get(
                f"{self.API_BASE}/groups",
                headers=headers,
            )
            if resp.status_code == 200:
                return resp.json().get("resp_data", {}).get("groups", [])
        except Exception as e:
            logger.error(f"获取星球列表失败: {e}")
        return []

    def get_status(self) -> dict:
        return {
            "name": self.name,
            "display_name": self.display_name,
            "config_valid": self.validate_config(),
            "token_configured": bool(self.config.get("access_token")),
        }
